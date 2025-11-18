"""Support multiple images training per student."""
import numpy as np
from typing import List, Tuple
import logger_setup as logger_module

logger = logger_module.logger


class MultiImageTrainer:
    """Handle multiple images training for better accuracy."""
    
    def __init__(self):
        """Initialize multi-image trainer."""
        self.min_images = 5
        self.max_images = 10
        
    def compute_average_embedding(self, embeddings: List[np.ndarray]) -> np.ndarray:
        """
        Compute average embedding from multiple images.
        
        Args:
            embeddings: List of embeddings from different images
            
        Returns:
            Average embedding vector
        """
        try:
            if len(embeddings) == 0:
                return None
            
            # Stack embeddings
            embeddings_array = np.array(embeddings)
            
            # Compute mean
            avg_embedding = np.mean(embeddings_array, axis=0)
            
            # Normalize
            avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
            
            logger.info(f"Computed average embedding from {len(embeddings)} images")
            return avg_embedding
            
        except Exception as e:
            logger.error(f"Error computing average embedding: {str(e)}")
            return None
    
    def compute_robust_embedding(self, embeddings: List[np.ndarray], method: str = 'median') -> np.ndarray:
        """
        Compute robust embedding using median or trimmed mean.
        
        Args:
            embeddings: List of embeddings
            method: 'median' or 'trimmed_mean'
            
        Returns:
            Robust embedding vector
        """
        try:
            if len(embeddings) == 0:
                return None
            
            embeddings_array = np.array(embeddings)
            
            if method == 'median':
                # Use median which is more robust to outliers
                robust_embedding = np.median(embeddings_array, axis=0)
            elif method == 'trimmed_mean':
                # Use trimmed mean (remove top/bottom 10%)
                n_remove = max(1, int(len(embeddings) * 0.1))
                sorted_emb = np.sort(embeddings_array, axis=0)
                trimmed = sorted_emb[n_remove:-n_remove, :]
                robust_embedding = np.mean(trimmed, axis=0)
            else:
                robust_embedding = np.mean(embeddings_array, axis=0)
            
            # Normalize
            robust_embedding = robust_embedding / np.linalg.norm(robust_embedding)
            
            logger.info(f"Computed {method} embedding from {len(embeddings)} images")
            return robust_embedding
            
        except Exception as e:
            logger.error(f"Error computing robust embedding: {str(e)}")
            return None
    
    def filter_outliers(self, embeddings: List[np.ndarray], threshold: float = 0.3) -> List[np.ndarray]:
        """
        Filter out outlier embeddings.
        
        Args:
            embeddings: List of embeddings
            threshold: Cosine similarity threshold to filter outliers
            
        Returns:
            Filtered list of embeddings
        """
        try:
            if len(embeddings) <= 2:
                return embeddings
            
            # Compute centroid
            centroid = np.mean(np.array(embeddings), axis=0)
            centroid = centroid / np.linalg.norm(centroid)
            
            # Compute similarities
            similarities = []
            for emb in embeddings:
                norm_emb = emb / np.linalg.norm(emb)
                sim = np.dot(norm_emb, centroid)
                similarities.append(sim)
            
            # Filter out embeddings with similarity below threshold
            filtered = [emb for emb, sim in zip(embeddings, similarities) if sim >= threshold]
            
            if len(filtered) == 0:
                logger.warning("All embeddings filtered out, returning original")
                return embeddings
            
            logger.info(f"Filtered {len(embeddings) - len(filtered)} outlier embeddings")
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtering outliers: {str(e)}")
            return embeddings
    
    def get_best_embedding_set(self, embeddings: List[np.ndarray], n_best: int = 5) -> List[np.ndarray]:
        """
        Select best embeddings based on variance.
        
        Args:
            embeddings: List of embeddings
            n_best: Number of best embeddings to return
            
        Returns:
            List of best embeddings
        """
        try:
            if len(embeddings) <= n_best:
                return embeddings
            
            embeddings_array = np.array(embeddings)
            
            # Compute centroid
            centroid = np.mean(embeddings_array, axis=0)
            centroid = centroid / np.linalg.norm(centroid)
            
            # Compute distances from centroid
            distances = []
            for emb in embeddings:
                norm_emb = emb / np.linalg.norm(emb)
                dist = np.linalg.norm(norm_emb - centroid)
                distances.append(dist)
            
            # Sort by distance and get best ones
            sorted_indices = np.argsort(distances)[:n_best]
            best_embeddings = [embeddings[i] for i in sorted_indices]
            
            logger.info(f"Selected {len(best_embeddings)} best embeddings from {len(embeddings)}")
            return best_embeddings
            
        except Exception as e:
            logger.error(f"Error getting best embeddings: {str(e)}")
            return embeddings










