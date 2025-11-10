"""Main FastAPI application for LHU FaceID system."""
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List, Optional
from fastapi.responses import JSONResponse, HTMLResponse
import cv2
import numpy as np
from io import BytesIO
# Already imported List above
import config as cfg
import logger_setup as logger_module
from database import db
from face_utils import FaceDetector, ArcFaceEmbedder, FaceMatcher
from attendance_logger import AttendanceLogger
from student_manager import StudentManager
import os

logger = logger_module.logger

# Initialize FastAPI app
app = FastAPI(
    title="LHU FaceID API",
    description="Student face recognition and information retrieval system",
    version="1.0.0"
)

# Initialize components
face_detector = FaceDetector()
embedder = ArcFaceEmbedder()
matcher = FaceMatcher()


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    logger.info("Starting up LHU FaceID API")
    
    try:
        db.connect()
        logger.info("API ready to accept requests")
    except Exception as e:
        logger.warning(f"Could not connect to database: {str(e)}")
        logger.warning("Starting without database connection. Please start Cassandra.")
        logger.info("API ready to accept requests (limited functionality)")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    logger.info("Shutting down LHU FaceID API")
    db.close()


def read_image(file: UploadFile) -> np.ndarray:
    """Read image from uploaded file."""
    try:
        contents = file.file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        return image
    except Exception as e:
        logger.error(f"Error reading image: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to read image: {str(e)}")


@app.post("/register_face")
async def register_face(
    files: List[UploadFile] = File(...),
    student_id: str = Form(...),
    name: str = Form(...),
    class_name: str = Form(...)
):
    """
    Register a new student with face embedding(s).
    
    Args:
        files: Multiple face image files
        student_id: Student ID
        name: Student name
        class_name: Student class
        
    Returns:
        Registration result
    """
    try:
        logger.info(f"Registering student: {student_id}, name: {name}, class: {class_name}")
        logger.info(f"Received {len(files)} image files")
        
        embeddings = []
        
        # Process each image
        for idx, file in enumerate(files):
            logger.info(f"Processing image {idx + 1}/{len(files)}: {file.filename}")
            
            try:
                # Read image
                image = read_image(file)
                
                # Detect face
                face = face_detector.detect_face(image)
                if face is None:
                    logger.warning(f"No face detected in image {idx + 1}")
                    continue
                
                # Extract embedding
                logger.info(f"Face detected in image {idx + 1}, extracting embedding...")
                embedding = embedder.get_embedding(face)
                if embedding is None:
                    logger.warning(f"Failed with cropped face for image {idx + 1}, trying original")
                    embedding = embedder.get_embedding(image)
                    
                if embedding is not None:
                    embeddings.append(embedding)
                    logger.info(f"Successfully extracted embedding from image {idx + 1}")
            except Exception as e:
                logger.error(f"Error processing image {idx + 1}: {str(e)}")
                continue
        
        if len(embeddings) == 0:
            logger.error("No valid embeddings extracted from any images")
            raise HTTPException(status_code=400, detail="Failed to extract face embeddings from any images. Please ensure at least one image contains a clear face.")
        
        logger.info(f"Successfully extracted {len(embeddings)} embeddings")
        
        # Import multi-image trainer
        from multi_image_trainer import MultiImageTrainer
        trainer = MultiImageTrainer()
        
        # Filter outliers if more than 2 images
        if len(embeddings) > 2:
            embeddings = trainer.filter_outliers(embeddings)
        
        # Compute average embedding
        if len(embeddings) > 1:
            embedding = trainer.compute_average_embedding(embeddings)
        else:
            embedding = embeddings[0]
        
        # Save to database
        try:
            success = db.register_student(student_id, name, class_name, embedding)
            
            if success:
                logger.info(f"Successfully registered student {student_id} with {len(embeddings)} embeddings")
                return JSONResponse(
                    content={
                        "status": "success",
                        "message": f"Student {student_id} registered successfully",
                        "student_id": student_id,
                        "name": name,
                        "class": class_name,
                        "images_count": len(embeddings)
                    },
                    status_code=200
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to save to database")
        except Exception as db_error:
            error_msg = str(db_error)
            logger.error(f"Database error during registration: {error_msg}")
            
            # Provide helpful error message
            if "not connected" in error_msg.lower() or "cassandra" in error_msg.lower():
                detail_msg = "Database không kết nối được. Vui lòng khởi động Cassandra:\n\n" + \
                           "docker run -d --name cassandra -p 9042:9042 cassandra:latest"
            else:
                detail_msg = f"Lỗi database: {error_msg}"
            
            raise HTTPException(status_code=500, detail=detail_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register_face: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/verify_face")
async def verify_face(file: UploadFile = File(...)):
    """
    Verify a face and find matching student.
    
    Args:
        file: Face image file
        
    Returns:
        Verification result with student info if matched
    """
    try:
        logger.info("Verifying face")
        
        # Read image
        image = read_image(file)
        
        # Save image bytes for logging
        import cv2
        import io
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_bytes = buffer.tobytes()
        
        # Detect face
        face = face_detector.detect_face(image)
        if face is None:
            return JSONResponse(
                content={
                    "status": "no_face",
                    "message": "No face detected in image",
                    "student_info": None,
                    "similarity": None
                },
                status_code=200
            )
        
        # Extract embedding - try cropped face first, then original
        embedding = embedder.get_embedding(face)
        if embedding is None:
            logger.warning("Failed with cropped face, trying with original image")
            embedding = embedder.get_embedding(image)
            
        if embedding is None:
            raise HTTPException(status_code=400, detail="Failed to extract face embedding")
        
        # Get all students from database
        students = db.get_all_students()
        
        if len(students) == 0:
            return JSONResponse(
                content={
                    "status": "no_students",
                    "message": "No students registered in database",
                    "student_info": None,
                    "similarity": None
                },
                status_code=200
            )
        
        # Find best match
        match = matcher.find_best_match(embedding, students)
        
        # Log attendance
        attendance_logger = AttendanceLogger(db.session)
        
        if match is None or match['status'] == 'NO_MATCH':
            # Log failed recognition with image
            if match:
                attendance_logger.log_failed_recognition(match['similarity'], checkin_image=image_bytes)
            
            return JSONResponse(
                content={
                    "status": match['status'] if match else 'NO_MATCH',
                    "message": "No match found",
                    "student_info": None,
                    "similarity": match['similarity'] if match else None
                },
                status_code=200
            )
        
        # Log successful/uncertain recognition with image
        attendance_logger.log_checkin(
            match['student_id'],
            match['name'],
            match['class'],
            match['similarity'],
            location="main_gate",
            status='success' if match['status'] == 'MATCH' else 'uncertain',
            checkin_image=image_bytes
        )
        
        # Update check-in time if matched
        if match['status'] == 'MATCH':
            db.update_checkin(match['student_id'])
        
        logger.info(f"Face verification successful for student {match['student_id']}")
        return JSONResponse(
            content={
                "status": match['status'],
                "message": f"Face matched with similarity {match['similarity']:.4f}",
                "student_info": {
                    "student_id": match['student_id'],
                    "name": match['name'],
                    "class": match['class']
                },
                "similarity": match['similarity']
            },
            status_code=200
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify_face: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/get_student_info/{student_id}")
async def get_student_info(student_id: str):
    """
    Get student information by student ID.
    
    Args:
        student_id: Student ID
        
    Returns:
        Student information
    """
    try:
        logger.info(f"Getting info for student: {student_id}")
        
        info = db.get_student_info(student_id)
        
        if info is None:
            raise HTTPException(
                status_code=404,
                detail=f"Student {student_id} not found"
            )
        
        return JSONResponse(
            content={
                "status": "success",
                "student_info": info
            },
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_student_info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve web interface."""
    if os.path.exists("templates/index.html"):
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {
        "message": "LHU FaceID API",
        "version": "1.0.0",
        "endpoints": {
            "register_face": "POST /register_face",
            "verify_face": "POST /verify_face",
            "get_student_info": "GET /get_student_info/{student_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected" if db.session else "disconnected",
        "cassandra": "Please run: docker run -d --name cassandra -p 9042:9042 cassandra:latest"
    }


@app.get("/get_today_attendance")
async def get_today_attendance():
    """Get today's attendance records."""
    try:
        logger.info("Getting today's attendance")
        
        # Initialize attendance logger
        attendance_logger = AttendanceLogger(db.session)
        
        # Get attendance records
        attendance = attendance_logger.get_today_attendance()
        
        # Get statistics
        stats = attendance_logger.get_statistics()
        
        return JSONResponse(
            content={
                "status": "success",
                "attendance": attendance,
                "stats": stats
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error in get_today_attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/get_checkin_image/{log_id}")
async def get_checkin_image(log_id: str):
    """
    Get check-in image by log_id.
    
    Args:
        log_id: Attendance log ID
        
    Returns:
        Image file
    """
    try:
        from uuid import UUID
        from fastapi.responses import Response
        
        # Query database for image
        cql = """
        SELECT checkin_image
        FROM attendance_logs
        WHERE log_id = ?
        """
        
        prepared = db.session.prepare(cql)
        result = db.session.execute(prepared, [UUID(log_id)]).one()
        
        if result is None or not hasattr(result, 'checkin_image') or result.checkin_image is None:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Return image
        return Response(
            content=result.checkin_image,
            media_type="image/jpeg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting checkin image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/attendance")
async def attendance_dashboard():
    """Serve attendance dashboard."""
    if os.path.exists("templates/attendance.html"):
        with open("templates/attendance.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Attendance dashboard not found</h1>")


@app.get("/management")
async def management_dashboard():
    """Serve student management dashboard."""
    if os.path.exists("templates/management.html"):
        with open("templates/management.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Management dashboard not found</h1>")


@app.get("/get_all_students")
async def get_all_students():
    """Get all registered students."""
    try:
        logger.info("Getting all students")
        
        manager = StudentManager(db.session)
        students = manager.get_all_students_info()
        
        return JSONResponse(
            content={
                "status": "success",
                "students": students,
                "total": len(students)
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error getting all students: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.put("/update_student/{student_id}")
async def update_student(
    student_id: str,
    name: Optional[str] = Form(None),
    class_name: Optional[str] = Form(None)
):
    """Update student information."""
    try:
        logger.info(f"Updating student {student_id}")
        
        manager = StudentManager(db.session)
        success = manager.update_student_info(student_id, name, class_name)
        
        if success:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": f"Student {student_id} updated successfully"
                },
                status_code=200
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to update student")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating student: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/update_student_photo/{student_id}")
async def update_student_photo(
    student_id: str,
    files: List[UploadFile] = File(...)
):
    """Update student face embedding with new photo(s)."""
    try:
        logger.info(f"Updating photo for student {student_id}")
        
        embeddings = []
        
        # Process files
        for idx, file in enumerate(files):
            try:
                image = read_image(file)
                face = face_detector.detect_face(image)
                
                if face is None:
                    continue
                
                embedding = embedder.get_embedding(face)
                if embedding is None:
                    embedding = embedder.get_embedding(image)
                    
                if embedding is not None:
                    embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error processing image {idx + 1}: {str(e)}")
                continue
        
        if len(embeddings) == 0:
            raise HTTPException(status_code=400, detail="Failed to extract embeddings from any images")
        
        # Compute average embedding if multiple
        if len(embeddings) > 1:
            from multi_image_trainer import MultiImageTrainer
            trainer = MultiImageTrainer()
            embeddings = trainer.filter_outliers(embeddings)
            embedding = trainer.compute_average_embedding(embeddings)
        else:
            embedding = embeddings[0]
        
        # Update embedding
        manager = StudentManager(db.session)
        success = manager.update_student_embedding(student_id, embedding)
        
        if success:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": f"Updated photo for student {student_id}",
                    "images_count": len(embeddings)
                },
                status_code=200
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to update embedding")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating photo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/delete_student/{student_id}")
async def delete_student(student_id: str):
    """Delete student from system."""
    try:
        logger.info(f"Deleting student {student_id}")
        
        manager = StudentManager(db.session)
        success = manager.delete_student(student_id)
        
        if success:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": f"Student {student_id} deleted successfully"
                },
                status_code=200
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete student")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=cfg.config.api['host'],
        port=cfg.config.api['port'],
        reload=cfg.config.api['reload']
    )
