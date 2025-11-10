"""Student management utilities."""
from typing import List, Optional, Dict
import numpy as np
import logger_setup as logger_module

logger = logger_module.logger


class StudentManager:
    """Manage student information and embeddings."""
    
    def __init__(self, db_session):
        """Initialize student manager."""
        self.session = db_session
        logger.info("StudentManager initialized")
    
    def update_student_info(self, student_id: str, name: Optional[str] = None, 
                           class_name: Optional[str] = None) -> bool:
        """
        Update student information.
        
        Args:
            student_id: Student ID
            name: New name (optional)
            class_name: New class (optional)
            
        Returns:
            True if updated successfully
        """
        try:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if class_name is not None:
                updates.append('"class" = ?')
                params.append(class_name)
            
            if not updates:
                return True
            
            params.append(student_id)
            
            cql = f"""
            UPDATE students
            SET {', '.join(updates)}
            WHERE student_id = ?
            """
            
            prepared = self.session.prepare(cql)
            self.session.execute(prepared, params)
            
            logger.info(f"Updated student {student_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update student: {str(e)}")
            return False
    
    def update_student_embedding(self, student_id: str, embedding: np.ndarray) -> bool:
        """
        Update student face embedding.
        
        Args:
            student_id: Student ID
            embedding: New face embedding
            
        Returns:
            True if updated successfully
        """
        try:
            embedding_bytes = embedding.tobytes()
            
            cql = """
            UPDATE students
            SET embedding = ?
            WHERE student_id = ?
            """
            
            prepared = self.session.prepare(cql)
            self.session.execute(prepared, [embedding_bytes, student_id])
            
            logger.info(f"Updated embedding for student {student_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update embedding: {str(e)}")
            return False
    
    def delete_student(self, student_id: str) -> bool:
        """
        Delete student from database.
        
        Args:
            student_id: Student ID
            
        Returns:
            True if deleted successfully
        """
        try:
            cql = """
            DELETE FROM students
            WHERE student_id = ?
            """
            
            prepared = self.session.prepare(cql)
            self.session.execute(prepared, [student_id])
            
            logger.info(f"Deleted student {student_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete student: {str(e)}")
            return False
    
    def get_all_students_info(self) -> List[Dict]:
        """
        Get all students information (without embeddings).
        
        Returns:
            List of student info dicts
        """
        try:
            cql = """
            SELECT student_id, name, "class", last_checkin_time, created_at
            FROM students
            """
            
            results = self.session.execute(cql).all()
            
            students = []
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
                    'last_checkin_time': row.last_checkin_time.isoformat() if row.last_checkin_time else None,
                    'created_at': row.created_at.isoformat() if row.created_at else None
                })
            
            logger.info(f"Retrieved {len(students)} students")
            return students
            
        except Exception as e:
            logger.error(f"Failed to get all students: {str(e)}")
            return []


