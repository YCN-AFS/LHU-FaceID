"""Mask detection for face recognition with masks."""
import cv2
import numpy as np
from typing import Optional, Tuple
import logger_setup as logger_module
from mtcnn import MTCNN

logger = logger_module.logger


class MaskDetector:
    """Detect and handle faces with masks."""
    
    def __init__(self):
        """Initialize mask detector."""
        self.detector = MTCNN()
        self.mask_detection_model = None
        logger.info("Mask detector initialized")
    
    def detect_face_and_mask(self, image: np.ndarray) -> Optional[dict]:
        """
        Detect face and check if mask is present.
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Dict with 'face', 'bbox', 'has_mask', 'confidence'
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            faces = self.detector.detect_faces(rgb_image)
            
            if len(faces) == 0:
                return None
            
            # Get first face
            face_data = faces[0]
            
            # Extract bounding box
            x, y, w, h = face_data['box']
            
            # Check for mask using simple heuristic (nose/mouth region)
            has_mask = self._check_mask_simple(image, face_data)
            
            # Crop face
            face_crop = image[y:y+h, x:x+w]
            
            return {
                'face': face_crop,
                'bbox': (x, y, w, h),
                'has_mask': has_mask,
                'confidence': face_data['confidence'],
                'keypoints': face_data.get('keypoints', {})
            }
            
        except Exception as e:
            logger.error(f"Error in mask detection: {str(e)}")
            return None
    
    def _check_mask_simple(self, image: np.ndarray, face_data: dict) -> bool:
        """
        Simple mask detection using face landmarks.
        
        Args:
            image: Input image
            face_data: Face detection result from MTCNN
            
        Returns:
            True if mask detected
        """
        try:
            # Check if keypoints exist
            keypoints = face_data.get('keypoints', {})
            
            if 'nose' not in keypoints or 'mouth_left' not in keypoints or 'mouth_right' not in keypoints:
                # No landmarks, assume no mask
                return False
            
            # Check nose and mouth region for mask color
            nose_point = keypoints['nose']
            
            # Extract small region around nose
            x, y, w, h = face_data['box']
            
            # Nose region
            nose_x, nose_y = int(nose_point[0]), int(nose_point[1])
            region_size = 30
            
            x1 = max(0, nose_x - region_size)
            x2 = min(image.shape[1], nose_x + region_size)
            y1 = max(0, nose_y - region_size)
            y2 = min(image.shape[0], nose_y + region_size)
            
            nose_region = image[y1:y2, x1:x2]
            
            if nose_region.size == 0:
                return False
            
            # Convert to grayscale
            gray_region = cv2.cvtColor(nose_region, cv2.COLOR_BGR2GRAY)
            
            # Compute mean and std
            mean_intensity = np.mean(gray_region)
            std_intensity = np.std(gray_region)
            
            # Mask typically has lower std (less variation in nose region)
            # and specific intensity range
            has_mask = std_intensity < 25 and 50 < mean_intensity < 150
            
            logger.debug(f"Mask detection: mean={mean_intensity:.1f}, std={std_intensity:.1f}, has_mask={has_mask}")
            
            return has_mask
            
        except Exception as e:
            logger.error(f"Error in simple mask detection: {str(e)}")
            return False
    
    def enhance_face_with_mask(self, image: np.ndarray, adjust_contrast: bool = True) -> np.ndarray:
        """
        Enhance face region when mask is present.
        
        Args:
            image: Face image
            adjust_contrast: Whether to adjust contrast
            
        Returns:
            Enhanced image
        """
        try:
            # Apply CLAHE for better contrast
            if adjust_contrast:
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                
                # Convert to LAB and apply CLAHE on L channel
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                l_enhanced = clahe.apply(l)
                lab_enhanced = cv2.merge([l_enhanced, a, b])
                image = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
            
            # Apply bilateral filter for noise reduction
            image = cv2.bilateralFilter(image, 9, 75, 75)
            
            return image
            
        except Exception as e:
            logger.error(f"Error enhancing face with mask: {str(e)}")
            return image
    
    def extract_upper_face_features(self, face_image: np.ndarray) -> np.ndarray:
        """
        Extract features from upper face only (forehead, eyes).
        Useful when mask is present.
        
        Args:
            face_image: Face image
            
        Returns:
            Upper face region
        """
        try:
            h, w = face_image.shape[:2]
            
            # Extract top 60% (forehead and eyes)
            upper_face = face_image[0:int(h*0.6), :]
            
            # Resize back to original dimensions to maintain consistency
            upper_face = cv2.resize(upper_face, (w, h), interpolation=cv2.INTER_CUBIC)
            
            return upper_face
            
        except Exception as e:
            logger.error(f"Error extracting upper face: {str(e)}")
            return face_image
    
    def extract_eye_region_features(self, image: np.ndarray, face_data: dict) -> Optional[np.ndarray]:
        """
        Extract features from eye region only.
        
        Args:
            image: Full image
            face_data: Face detection result
            
        Returns:
            Eye region image
        """
        try:
            keypoints = face_data.get('keypoints', {})
            
            if 'left_eye' not in keypoints or 'right_eye' not in keypoints:
                return None
            
            left_eye = keypoints['left_eye']
            right_eye = keypoints['right_eye']
            
            # Calculate bounding box for eye region
            x_coords = [left_eye[0], right_eye[0]]
            y_coords = [left_eye[1], right_eye[1]]
            
            x_min = max(0, int(min(x_coords) - 50))
            x_max = min(image.shape[1], int(max(x_coords) + 50))
            y_min = max(0, int(min(y_coords) - 40))
            y_max = min(image.shape[0], int(max(y_coords) + 40))
            
            eye_region = image[y_min:y_max, x_min:x_max]
            
            if eye_region.size == 0:
                return None
            
            return eye_region
            
        except Exception as e:
            logger.error(f"Error extracting eye region: {str(e)}")
            return None










