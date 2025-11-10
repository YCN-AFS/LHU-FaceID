"""Face detection and embedding utilities."""
import cv2
import numpy as np
from mtcnn import MTCNN
import insightface
from typing import Tuple, Optional
import config as cfg
import logger_setup as logger_module

logger = logger_module.logger


class FaceDetector:
    """Face detection using MTCNN."""
    
    def __init__(self):
        """Initialize MTCNN detector."""
        self.detector = MTCNN(
            min_face_size=cfg.config.face_detection['min_face_size'],
            scale_factor=cfg.config.face_detection['scale_factor'],
            steps_threshold=cfg.config.face_detection['threshold']
        )
        logger.info("MTCNN face detector initialized")
    
    def detect_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect face in image and return cropped face.
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Cropped face image or None if no face detected
        """
        try:
            # Convert BGR to RGB for MTCNN
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            faces = self.detector.detect_faces(rgb_image)
            
            if len(faces) == 0:
                logger.warning("No face detected in image")
                return None
            
            if len(faces) > 1:
                logger.warning("Multiple faces detected, using the first one")
            
            # Get the first face
            face = faces[0]
            
            # Extract face coordinates
            x, y, w, h = face['box']
            
            # Expand bounding box slightly
            padding = 0.2
            x = max(0, int(x - w * padding))
            y = max(0, int(y - h * padding))
            w = int(w * (1 + 2 * padding))
            h = int(h * (1 + 2 * padding))
            
            # Crop face
            face_crop = image[y:y+h, x:x+w]
            
            if face_crop.size == 0:
                logger.error("Failed to crop face")
                return None
            
            logger.info(f"Face detected successfully")
            return face_crop
            
        except Exception as e:
            logger.error(f"Error in face detection: {str(e)}")
            return None


class ArcFaceEmbedder:
    """ArcFace embedding extraction."""
    
    def __init__(self):
        """Initialize ArcFace model."""
        try:
            # Initialize InsightFace app with ArcFace model
            self.app = insightface.app.FaceAnalysis()
            self.app.prepare(ctx_id=-1, det_size=(640, 640))
            logger.info("ArcFace model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ArcFace: {str(e)}")
            raise
    
    def get_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract face embedding from image.
        
        Args:
            image: Face image (BGR format) - already cropped face
            
        Returns:
            512-dimensional embedding vector or None
        """
        try:
            # Check image size
            if image is None or image.size == 0:
                logger.error("Empty image provided")
                return None
                
            logger.info(f"Extracting embedding from image shape: {image.shape}")
            
            # Resize image to expected size (112x112 for ArcFace)
            target_size = (112, 112)
            resized = cv2.resize(image, target_size, interpolation=cv2.INTER_CUBIC)
            
            # InsightFace expects RGB
            rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # Get face analysis - this includes detection and recognition models
            faces = self.app.get(rgb_image)
            
            if len(faces) == 0:
                logger.warning("InsightFace could not detect face in pre-cropped image, trying full pipeline")
                # If InsightFace still can't detect, the face might be too small or unclear
                # Return None to trigger retry with different preprocessing
                return None
            
            # Get embedding from the first face
            embedding = faces[0].embedding
            
            # Ensure it's 512 dimensions
            if len(embedding) != 512:
                logger.warning(f"Unexpected embedding dimension: {len(embedding)}")
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            logger.info(f"Successfully extracted embedding of shape {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error in embedding extraction: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None


class FaceMatcher:
    """Face matching using cosine similarity."""
    
    def __init__(self):
        """Initialize face matcher with thresholds."""
        self.threshold_match = cfg.config.threshold['match']
        self.threshold_uncertain = cfg.config.threshold['uncertain']
        logger.info(f"FaceMatcher initialized with thresholds: match={self.threshold_match}, uncertain={self.threshold_uncertain}")
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Ensure embeddings are normalized
            embedding1 = embedding1 / np.linalg.norm(embedding1)
            embedding2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def match(self, query_embedding: np.ndarray, reference_embedding: np.ndarray) -> Tuple[str, float]:
        """
        Match query embedding with reference embedding.
        
        Args:
            query_embedding: Query face embedding
            reference_embedding: Reference face embedding
            
        Returns:
            Tuple of (match_status, similarity_score)
            match_status: 'MATCH', 'UNCERTAIN', or 'NO_MATCH'
        """
        similarity = self.cosine_similarity(query_embedding, reference_embedding)
        
        if similarity >= self.threshold_match:
            status = 'MATCH'
        elif similarity >= self.threshold_uncertain:
            status = 'UNCERTAIN'
        else:
            status = 'NO_MATCH'
        
        logger.info(f"Match result: {status} (similarity={similarity:.4f})")
        return status, similarity
    
    def find_best_match(self, query_embedding: np.ndarray, students: list) -> Optional[dict]:
        """
        Find the best matching student for a query embedding.
        
        Args:
            query_embedding: Query face embedding
            students: List of student dicts with embeddings
            
        Returns:
            Best match dict with student info and match details, or None
        """
        best_match = None
        best_score = -1
        best_status = 'NO_MATCH'
        
        for student in students:
            status, score = self.match(query_embedding, student['embedding'])
            
            if score > best_score:
                best_score = score
                best_status = status
                best_match = {
                    'student_id': student['student_id'],
                    'name': student['name'],
                    'class': student['class'],
                    'similarity': score,
                    'status': status
                }
        
        if best_match and best_status != 'NO_MATCH':
            logger.info(f"Best match found: {best_match['student_id']} ({best_match['name']})")
        else:
            logger.warning("No valid match found")
        
        return best_match
