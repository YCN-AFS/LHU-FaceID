"""Configuration management for LHU FaceID system."""
import yaml
import os
from typing import List


class Config:
    """Configuration class to load and access settings."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    @property
    def threshold(self) -> dict:
        """Get threshold configuration."""
        return self._config['threshold']
    
    @property
    def face_detection(self) -> dict:
        """Get face detection configuration."""
        return self._config['face_detection']
    
    @property
    def arcface(self) -> dict:
        """Get ArcFace model configuration."""
        return self._config['arcface']
    
    @property
    def cassandra(self) -> dict:
        """Get Cassandra database configuration."""
        return self._config['cassandra']
    
    @property
    def logging(self) -> dict:
        """Get logging configuration."""
        return self._config['logging']
    
    @property
    def api(self) -> dict:
        """Get API configuration."""
        return self._config['api']


# Global config instance
config = Config()

