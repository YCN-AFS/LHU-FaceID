"""Attendance logging and analytics system."""
from datetime import datetime, date
from typing import List, Dict, Optional
from cassandra.cluster import Cluster
import logger_setup as logger_module
import config as cfg

logger = logger_module.logger


class AttendanceLogger:
    """Log and analyze attendance data."""
    
    def __init__(self, db_session):
        """Initialize attendance logger."""
        self.session = db_session
        self._create_attendance_table()
    
    def _create_attendance_table(self):
        """Create attendance logging table."""
        try:
            # First, try to add checkin_image_path column if it doesn't exist
            # If old BLOB column exists, we'll ignore it and use the new TEXT column
            try:
                cql_alter = """
                ALTER TABLE attendance_logs ADD checkin_image_path TEXT;
                """
                self.session.execute(cql_alter)
                logger.info("Added checkin_image_path column to attendance_logs table")
            except Exception as e:
                # Column might already exist, which is fine
                if "already exists" not in str(e).lower() and "Invalid" not in str(e):
                    logger.warning(f"Could not add checkin_image_path column: {str(e)}")
            
            # Create table if not exists
            cql = """
            CREATE TABLE IF NOT EXISTS attendance_logs (
                log_id UUID PRIMARY KEY,
                student_id TEXT,
                student_name TEXT,
                "class" TEXT,
                checkin_time TIMESTAMP,
                location TEXT,
                confidence_score FLOAT,
                status TEXT,
                face_detected BOOLEAN,
                checkin_image_path TEXT
            );
            """
            self.session.execute(cql)
            logger.info("Attendance logs table created or already exists")
        except Exception as e:
            logger.error(f"Failed to create attendance table: {str(e)}")
    
    def log_checkin(self, student_id: str, student_name: str, class_name: str, 
                   confidence: float, location: str = "main_gate", 
                   status: str = "success", checkin_image_path: str = None) -> bool:
        """
        Log a check-in event.
        
        Args:
            student_id: Student ID
            student_name: Student name
            class_name: Class name
            confidence: Recognition confidence score
            location: Check-in location
            status: success, uncertain, or failed
            checkin_image_path: Path to check-in image file (optional)
            
        Returns:
            True if logged successfully
        """
        try:
            if self.session is None:
                logger.error("Database session is None, cannot log check-in")
                return False
                
            from uuid import uuid4
            
            cql = """
            INSERT INTO attendance_logs (
                log_id, student_id, student_name, "class", 
                checkin_time, location, confidence_score, 
                status, face_detected, checkin_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Prepare statement before executing
            prepared = self.session.prepare(cql)
            self.session.execute(
                prepared,
                (uuid4(), student_id, student_name, class_name, 
                 datetime.now(), location, confidence, status, True, checkin_image_path)
            )
            
            logger.info(f"Check-in logged: {student_id} at {location}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log check-in: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def log_failed_recognition(self, confidence: float, location: str = "main_gate", checkin_image_path: str = None):
        """
        Log a failed recognition attempt.
        
        Args:
            confidence: Confidence score of best match (even if failed)
            location: Location of attempt
            checkin_image_path: Path to check-in image file (optional)
            
        Returns:
            True if logged successfully
        """
        try:
            if self.session is None:
                logger.error("Database session is None, cannot log failed recognition")
                return False
                
            from uuid import uuid4
            
            cql = """
            INSERT INTO attendance_logs (
                log_id, student_id, student_name, "class",
                checkin_time, location, confidence_score,
                status, face_detected, checkin_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Prepare statement before executing
            prepared = self.session.prepare(cql)
            self.session.execute(
                prepared,
                (uuid4(), None, None, None,
                 datetime.now(), location, confidence, 
                 "failed", True, checkin_image_path)
            )
            
            logger.warning(f"Failed recognition logged at {location}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log failed recognition: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def get_today_attendance(self) -> List[Dict]:
        """
        Get all attendance records for today.
        
        Returns:
            List of attendance records
        """
        try:
            if self.session is None:
                logger.error("Database session is None, cannot get attendance")
                return []
                
            cql = """
            SELECT log_id, student_id, student_name, "class",
                   checkin_time, location, confidence_score, status, checkin_image_path
            FROM attendance_logs
            WHERE checkin_time >= ? ALLOW FILTERING
            """
            
            today_start = datetime.combine(date.today(), datetime.min.time())
            
            # Prepare statement before executing
            prepared = self.session.prepare(cql)
            results = self.session.execute(prepared, (today_start,)).all()
            
            attendance_list = []
            for row in results:
                # Access "class" column - Cassandra driver renames it to field_2_ because "class" is a Python reserved keyword
                class_value = None
                try:
                    if hasattr(row, '_fields'):
                        if 'class' in row._fields:
                            idx = row._fields.index('class')
                            class_value = row[idx] if idx < len(row) else None
                        elif 'field_2_' in row._fields:
                            # Cassandra driver renames "class" to field_2_
                            class_value = getattr(row, 'field_2_', None)
                        else:
                            # Try to get by index (class is usually the 3rd column in attendance_logs)
                            if len(row) >= 4:  # log_id, student_id, student_name, class
                                class_value = row[3]
                    else:
                        # Try field_2_ attribute (Cassandra driver's renamed version)
                        class_value = getattr(row, 'field_2_', None)
                except Exception as e:
                    logger.warning(f"Could not access class column: {e}")
                
                # Check if checkin_image_path exists
                has_image = False
                image_path = None
                try:
                    if hasattr(row, 'checkin_image_path') and row.checkin_image_path is not None:
                        image_path = row.checkin_image_path
                        # Check if file actually exists
                        import os
                        if os.path.exists(image_path):
                            has_image = True
                except:
                    pass
                
                attendance_list.append({
                    'log_id': str(row.log_id),
                    'student_id': row.student_id,
                    'student_name': row.student_name,
                    'class': class_value,
                    'checkin_time': row.checkin_time.isoformat() if row.checkin_time else None,
                    'checkin_time_obj': row.checkin_time,  # Keep datetime object for sorting
                    'location': row.location,
                    'confidence': row.confidence_score,
                    'status': row.status,
                    'has_image': has_image,
                    'image_path': image_path
                })
            
            # Sort by checkin_time descending (newest first)
            attendance_list.sort(key=lambda x: x['checkin_time_obj'] if x['checkin_time_obj'] else datetime.min, reverse=True)
            
            # Remove the datetime object before returning (keep only ISO string)
            for record in attendance_list:
                record.pop('checkin_time_obj', None)
            
            logger.info(f"Retrieved {len(attendance_list)} attendance records for today")
            return attendance_list
            
        except Exception as e:
            logger.error(f"Failed to get today attendance: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def get_student_attendance_history(self, student_id: str, days: int = 30) -> List[Dict]:
        """
        Get attendance history for a student.
        
        Args:
            student_id: Student ID
            days: Number of days to look back
        
        Returns:
            List of attendance records
        """
        try:
            if self.session is None:
                logger.error("Database session is None, cannot get attendance history")
                return []
                
            from datetime import timedelta
            
            cql = """
            SELECT log_id, student_id, student_name, "class",
                   checkin_time, location, confidence_score, status
            FROM attendance_logs
            WHERE student_id = ? AND checkin_time >= ? ALLOW FILTERING
            """
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Prepare statement before executing
            prepared = self.session.prepare(cql)
            results = self.session.execute(prepared, (student_id, start_date)).all()
            
            history = []
            for row in results:
                # Access "class" column - Cassandra driver renames it to field_2_ because "class" is a Python reserved keyword
                class_value = None
                try:
                    if hasattr(row, '_fields'):
                        if 'class' in row._fields:
                            idx = row._fields.index('class')
                            class_value = row[idx] if idx < len(row) else None
                        elif 'field_2_' in row._fields:
                            # Cassandra driver renames "class" to field_2_
                            class_value = getattr(row, 'field_2_', None)
                        else:
                            # Try to get by index (class is usually the 3rd column in attendance_logs)
                            if len(row) >= 4:  # log_id, student_id, student_name, class
                                class_value = row[3]
                    else:
                        # Try field_2_ attribute (Cassandra driver's renamed version)
                        class_value = getattr(row, 'field_2_', None)
                except Exception as e:
                    logger.warning(f"Could not access class column: {e}")
                
                history.append({
                    'log_id': str(row.log_id),
                    'student_id': row.student_id,
                    'student_name': row.student_name,
                    'class': class_value,
                    'checkin_time': row.checkin_time.isoformat() if row.checkin_time else None,
                    'checkin_time_obj': row.checkin_time,  # Keep datetime object for sorting
                    'location': row.location,
                    'confidence': row.confidence_score,
                    'status': row.status
                })
            
            # Sort by checkin_time descending (newest first)
            history.sort(key=lambda x: x['checkin_time_obj'] if x['checkin_time_obj'] else datetime.min, reverse=True)
            
            # Remove the datetime object before returning (keep only ISO string)
            for record in history:
                record.pop('checkin_time_obj', None)
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get attendance history: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get attendance statistics for today.
        
        Returns:
            Dictionary with statistics
        """
        try:
            today_records = self.get_today_attendance()
            
            total = len(today_records)
            successful = len([r for r in today_records if r['status'] == 'success'])
            uncertain = len([r for r in today_records if r['status'] == 'uncertain'])
            failed = len([r for r in today_records if r['status'] == 'failed'])
            
            avg_confidence = 0.0
            if today_records:
                avg_confidence = sum(r['confidence'] for r in today_records) / len(today_records)
            
            return {
                'total_attempts': total,
                'successful': successful,
                'uncertain': uncertain,
                'failed': failed,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'average_confidence': round(avg_confidence, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {
                'total_attempts': 0,
                'successful': 0,
                'uncertain': 0,
                'failed': 0,
                'success_rate': 0,
                'average_confidence': 0.0
            }
