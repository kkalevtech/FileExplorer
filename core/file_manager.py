"""
File Manager Module
Handles navigation and basic file operations for the File Explorer
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


class FileManager:
    def __init__(self, start_path=None):
        """
        Initialize the file manager with a starting path.
        If no path is provided, uses the current working directory.
        """
        if start_path is None:
            self.current_path = Path.cwd()
        else:
            start_path = Path(start_path)
            if start_path.exists() and start_path.is_dir():
                self.current_path = start_path.resolve()
            else:
                raise ValueError(f"Invalid starting path: {start_path}")
    
    def get_current_path(self):
        """Return the current directory path."""
        return str(self.current_path)
    
    def list_directory(self, path=None):
        """
        List contents of the current directory or specified path.
        Returns a list of dictionaries with file/folder info.
        """
        if path is None:
            target_path = self.current_path
        else:
            target_path = Path(path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"Path does not exist: {target_path}")
        
        if not target_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {target_path}")
        
        items = []
        for item in sorted(target_path.iterdir()):
            is_dir = item.is_dir()
            size = 0 if is_dir else item.stat().st_size
            modified_time = datetime.fromtimestamp(item.stat().st_mtime)
            
            items.append({
                'name': item.name,
                'is_dir': is_dir,
                'size': size,
                'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                'path': str(item)
            })
        
        return items
    
    def change_directory(self, path):
        """
        Change the current directory to the specified path.
        Can be relative or absolute.
        """
        new_path = Path(path)
        
        # If it's a relative path, resolve it relative to current directory
        if not new_path.is_absolute():
            new_path = self.current_path / new_path
        
        resolved_path = new_path.resolve()
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"Path does not exist: {resolved_path}")
        
        if not resolved_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {resolved_path}")
        
        self.current_path = resolved_path
        return str(resolved_path)
    
    def go_back(self):
        """Go back to the parent directory."""
        parent = self.current_path.parent
        self.current_path = parent
        return str(parent)
    
    def create_file(self, filename):
        """Create a new empty file in the current directory."""
        file_path = self.current_path / filename
        if file_path.exists():
            raise FileExistsError(f"File already exists: {file_path}")
        
        with open(file_path, 'w'):
            pass  # Create empty file
        return str(file_path)
    
    def create_directory(self, dirname):
        """Create a new directory in the current directory."""
        dir_path = self.current_path / dirname
        if dir_path.exists():
            raise FileExistsError(f"Directory already exists: {dir_path}")
        
        dir_path.mkdir(parents=True, exist_ok=True)
        return str(dir_path)
    
    def delete_file(self, filename):
        """Delete a file from the current directory."""
        file_path = self.current_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")
        
        if file_path.is_dir():
            raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
        
        file_path.unlink()
        return str(file_path)
    
    def delete_directory(self, dirname):
        """Delete a directory and all its contents from the current directory."""
        dir_path = self.current_path / dirname
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {dir_path}")
        
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {dir_path}")
        
        shutil.rmtree(dir_path)
        return str(dir_path)
    
    def rename_file(self, old_name, new_name):
        """Rename a file in the current directory."""
        old_path = self.current_path / old_name
        new_path = self.current_path / new_name
        
        if not old_path.exists():
            raise FileNotFoundError(f"File does not exist: {old_path}")
        
        if new_path.exists():
            raise FileExistsError(f"New name already exists: {new_path}")
        
        old_path.rename(new_path)
        return str(new_path)
    
    def copy_file(self, src, dest):
        """Copy a file from source to destination."""
        src_path = self.current_path / src
        dest_path = self.current_path / dest
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {src_path}")
        
        if dest_path.exists():
            raise FileExistsError(f"Destination already exists: {dest_path}")
        
        shutil.copy2(src_path, dest_path)
        return str(dest_path)
    
    def move_file(self, src, dest):
        """Move a file from source to destination."""
        src_path = self.current_path / src
        dest_path = self.current_path / dest
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {src_path}")
        
        if dest_path.exists():
            raise FileExistsError(f"Destination already exists: {dest_path}")
        
        shutil.move(str(src_path), str(dest_path))
        return str(dest_path)
    
    def get_full_path(self, name):
        """Get the full path for a file/directory in the current directory."""
        return str(self.current_path / name)


if __name__ == "__main__":
    # Example usage
    fm = FileManager()
    print("Current path:", fm.get_current_path())
    print("Directory contents:")
    for item in fm.list_directory():
        print(f"  {item['name']} ({'DIR' if item['is_dir'] else 'FILE'}) - {item['size']} bytes")