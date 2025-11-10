"""Database models and connection for Cassandra."""
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.auth import PlainTextAuthProvider
from datetime import datetime
from typing import Optional, List
import numpy as np
import logger_setup as logger_module
import config as cfg

logger = logger_module.logger


class CassandraDB:
    """Cassandra database connection and operations."""
    
    def __init__(self):
        """Initialize Cassandra connection."""
        self.config = cfg.config.cassandra
        self.cluster = None
        self.session = None
        
    def connect(self):
        """Connect to Cassandra cluster."""
        try:
            self.cluster = Cluster(
                self.config['hosts'],
                port=self.config['port']
            )
            self.session = self.cluster.connect()
            logger.info("Connected to Cassandra cluster")
            
            # Create keyspace if not exists
            self._create_keyspace()
            self.session.set_keyspace(self.config['keyspace'])
            
            # Create tables
            self._create_tables()
            
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {str(e)}")
            raise
    
    def _create_keyspace(self):
        """Create keyspace if it doesn't exist."""
        keyspace = self.config['keyspace']
        replication = self.config['replication']
        replication_factor = replication['replication_factor']
        
        cql = f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace}
        WITH REPLICATION = {{
            'class' : '{replication['class']}',
            'replication_factor' : {replication_factor}
        }};
        """
        
        try:
            self.session.execute(cql)
            logger.info(f"Keyspace '{keyspace}' created or already exists")
        except Exception as e:
            logger.warning(f"Could not create keyspace: {str(e)}")
    
    def _create_tables(self):
        """Create necessary tables."""
        # Student table
        # Note: "class" is a reserved keyword in Cassandra, so we use quotes
        cql = """
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT,
            "class" TEXT,
            embedding BLOB,
            last_checkin_time TIMESTAMP,
            created_at TIMESTAMP
        );
        """
        
        self.session.execute(cql)
        logger.info("Table 'students' created or already exists")
    
    def register_student(self, student_id: str, name: str, class_name: str, embedding: np.ndarray):
        """Register a new student with face embedding."""
        try:
            # Check if database is connected
            if self.session is None:
                logger.error("Database not connected. Please start Cassandra.")
                raise Exception("Database not connected. Please start Cassandra database.")
            
            # Check if embedding is valid
            if embedding is None:
                logger.error("Empty embedding provided")
                raise Exception("Empty embedding provided")
                
            logger.info(f"Registering student: {student_id}, embedding shape: {embedding.shape}")
            
            # Convert numpy array to bytes
            embedding_bytes = embedding.tobytes()
            
            now = datetime.now()
            
            cql = """
            INSERT INTO students (student_id, name, "class", embedding, last_checkin_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            # Prepare statement
            prepared = self.session.prepare(cql)
            self.session.execute(
                prepared,
                [student_id, name, class_name, embedding_bytes, now, now]
            )
            
            logger.info(f"Student {student_id} registered successfully")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to register student: {error_msg}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Re-raise with detailed message
            raise Exception(f"Database error: {error_msg}")
    
    def get_student_info(self, student_id: str) -> Optional[dict]:
        """Get student information by student_id."""
        try:
            cql = """
            SELECT student_id, name, "class", last_checkin_time, created_at
            FROM students
            WHERE student_id = ?
            """
            
            prepared = self.session.prepare(cql)
            result = self.session.execute(prepared, [student_id]).one()
            
            if result:
                # Access "class" column - Cassandra driver renames it to field_2_ because "class" is a Python reserved keyword
                class_value = None
                try:
                    if hasattr(result, '_fields'):
                        # Check if class column exists (it will be renamed to field_2_ or similar)
                        if 'class' in result._fields:
                            idx = result._fields.index('class')
                            class_value = result[idx] if idx < len(result) else None
                        elif 'field_2_' in result._fields:
                            # Cassandra driver renames "class" to field_2_
                            class_value = getattr(result, 'field_2_', None)
                        else:
                            # Try to get by index (class is usually the 3rd column)
                            if len(result) >= 3:
                                class_value = result[2]
                    else:
                        # Try field_2_ attribute (Cassandra driver's renamed version)
                        class_value = getattr(result, 'field_2_', None)
                except Exception as e:
                    logger.warning(f"Could not access class column: {e}")
                
                return {
                    'student_id': result.student_id,
                    'name': result.name,
                    'class': class_value,
                    'last_checkin_time': result.last_checkin_time.isoformat() if result.last_checkin_time else None,
                    'created_at': result.created_at.isoformat() if result.created_at else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get student info: {str(e)}")
            return None
    
    def get_all_students(self) -> List[dict]:
        """Get all students with their embeddings."""
        try:
            cql = """
            SELECT student_id, name, "class", embedding, last_checkin_time
            FROM students
            """
            
            results = self.session.execute(cql).all()
            
            students = []
            for row in results:
                # Convert bytes back to numpy array
                embedding = np.frombuffer(row.embedding, dtype=np.float32)
                
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
                            # Try to get by index (class is usually the 3rd column: student_id, name, class)
                            if len(row) >= 3:
                                class_value = row[2]
                    else:
                        # Try field_2_ attribute (Cassandra driver's renamed version)
                        class_value = getattr(row, 'field_2_', None)
                except Exception as e:
                    logger.warning(f"Could not access class column: {e}")
                
                students.append({
                    'student_id': row.student_id,
                    'name': row.name,
                    'class': class_value,
                    'embedding': embedding,
                    'last_checkin_time': row.last_checkin_time
                })
            
            logger.info(f"Retrieved {len(students)} students from database")
            return students
            
        except Exception as e:
            logger.error(f"Failed to get all students: {str(e)}")
            return []
    
    def update_checkin(self, student_id: str):
        """Update last check-in time for a student."""
        try:
            cql = """
            UPDATE students
            SET last_checkin_time = ?
            WHERE student_id = ?
            """
            
            prepared = self.session.prepare(cql)
            self.session.execute(prepared, [datetime.now(), student_id])
            logger.info(f"Updated check-in time for student {student_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update check-in time: {str(e)}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Cassandra connection closed")


# Global database instance
db = CassandraDB()
