"""File system operations for langfun agents."""

from typing import Any, Dict, List, Optional, Union, Literal, ClassVar
import os
import shutil
import traceback
import langfun as lf
from langfun.core.agentic import action as action_lib
import pyglove as pg


class FileSystemAction(action_lib.Action):
    """Unified action for file system operations."""
    
    # Allow attribute assignment at runtime
    allow_symbolic_assignment = True
    
    operation: Literal["read", "write", "list", "delete", "copy", "move", "create_dir", "get_info"] = "write"
    source_path: Optional[str] = None
    path: Optional[str] = None  # Alias for source_path for compatibility
    target_path: Optional[str] = None
    content: Optional[str] = None
    
    # Class variable to define default paths
    default_storage_path: ClassVar[str] = "/tmp"
    
    def _on_bound(self):
        super()._on_bound()
        # If path is provided but source_path is not, use path
        if not self.source_path and self.path:
            self.source_path = self.path
            
        # If source_path is a directory, assume we want to write to a file in that directory
        if self.operation == "write" and self.source_path and os.path.isdir(self.source_path):
            # Generate a default filename if writing to a directory
            self.source_path = os.path.join(self.source_path, "output.txt")
            
        # Validate required parameters based on operation
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate parameters based on the operation."""
        # Handle case where neither source_path nor path is provided
        if not self.source_path:
            # Use a default path if none provided
            self.source_path = os.path.join(self.default_storage_path, "output.txt")
        
        # Operations that require an existing source path
        if self.operation in ["read", "list", "delete", "copy", "move"]:
            if not os.path.exists(self.source_path):
                raise ValueError(f"Source path does not exist: {self.source_path}")
        
        # Copy/move operations need target paths
        if self.operation in ["copy", "move"]:
            if not self.target_path:
                raise ValueError("Target path is required for copy/move operations")
    
    def call(self, session, *, lm=None, **kwargs):
        """Execute the file system operation.
        
        Args:
            session: The current session.
            lm: Language model (unused but required by langfun Action interface).
            **kwargs: Additional arguments.
            
        Returns:
            Operation-specific result:
                read: str (file contents)
                write: bool (success)
                list: list[str] (directory contents)
                delete: bool (success)
                copy: bool (success)
                move: bool (success)
                create_dir: bool (success)
                get_info: dict (file information)
        """
        try:
            # Log the start of operation with full details
            session.info(f"Starting {self.operation} operation on {self.source_path}")
            
            # Execute operation
            result = self._execute_operation()
            
            # Log success
            session.info(f"Successfully executed {self.operation} operation on {self.source_path}")
            return result
            
        except Exception as e:
            # Log full exception details
            error_msg = f"Failed to execute {self.operation} operation on {self.source_path}: {str(e)}"
            session.error(error_msg)
            session.error(traceback.format_exc())
            raise RuntimeError(error_msg) from e
    
    def _execute_operation(self) -> Any:
        """Execute the specific file system operation."""
        if self.operation == "read":
            with open(self.source_path, 'r') as f:
                return f.read()
        
        elif self.operation == "write":
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(os.path.abspath(self.source_path))
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
                
            with open(self.source_path, 'w') as f:
                f.write(self.content or "")
            return True
        
        elif self.operation == "list":
            return os.listdir(self.source_path)
        
        elif self.operation == "delete":
            if os.path.isfile(self.source_path):
                os.remove(self.source_path)
            else:
                shutil.rmtree(self.source_path)
            return True
        
        elif self.operation == "copy":
            if os.path.isfile(self.source_path):
                # Create parent directories for target if needed
                parent_dir = os.path.dirname(os.path.abspath(self.target_path))
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                shutil.copy2(self.source_path, self.target_path)
            else:
                shutil.copytree(self.source_path, self.target_path)
            return True
        
        elif self.operation == "move":
            # Create parent directories for target if needed
            parent_dir = os.path.dirname(os.path.abspath(self.target_path))
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            shutil.move(self.source_path, self.target_path)
            return True
        
        elif self.operation == "create_dir":
            os.makedirs(self.source_path, exist_ok=True)
            return True
        
        elif self.operation == "get_info":
            # Basic info that doesn't require the file to exist
            file_info = {
                "path": self.source_path,
                "exists": os.path.exists(self.source_path),
            }
            
            # Only add these properties if the file/directory exists
            if os.path.exists(self.source_path):
                try:
                    file_info.update({
                        "is_file": os.path.isfile(self.source_path),
                        "is_dir": os.path.isdir(self.source_path),
                        "size": os.path.getsize(self.source_path),
                        "last_modified": os.path.getmtime(self.source_path)
                    })
                except Exception as e:
                    # If we can't get some property, still return what we can
                    file_info["error"] = str(e)
            
            return file_info
        
        else:
            raise ValueError(f"Unsupported operation: {self.operation}")