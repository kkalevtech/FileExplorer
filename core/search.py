"""
Search Module
Handles file and directory search functionality for the File Explorer
"""

import os
from pathlib import Path
import fnmatch


class SearchManager:
    def __init__(self):
        pass
    
    def search_in_directory(self, search_term, directory_path, search_subdirs=False):
        """
        Search for files/directories in a given directory based on a search term.
        If search_subdirs is True, searches recursively in subdirectories.
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory does not exist or is not a directory: {directory}")
        
        results = []
        
        if search_subdirs:
            # Recursive search
            for root, dirs, files in os.walk(directory):
                for name in dirs + files:
                    if fnmatch.fnmatch(name.lower(), f'*{search_term.lower()}*'):
                        full_path = Path(root) / name
                        is_dir = full_path.is_dir()
                        size = 0 if is_dir else full_path.stat().st_size
                        modified = os.path.getmtime(full_path)
                        
                        results.append({
                            'name': name,
                            'path': str(full_path),
                            'is_dir': is_dir,
                            'size': size
                        })
        else:
            # Search only in the current directory
            for item in directory.iterdir():
                if search_term.lower() in item.name.lower():
                    is_dir = item.is_dir()
                    size = 0 if is_dir else item.stat().st_size
                    
                    results.append({
                        'name': item.name,
                        'path': str(item),
                        'is_dir': is_dir,
                        'size': size
                    })
        
        return results
    
    def search_by_extension(self, extension, directory_path, search_subdirs=False):
        """
        Search for files with a specific extension in a given directory.
        Extension should be provided with the dot (e.g., '.txt').
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory does not exist or is not a directory: {directory}")
        
        results = []
        
        if search_subdirs:
            # Recursive search
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(extension.lower()):
                        full_path = Path(root) / file
                        size = full_path.stat().st_size
                        modified = os.path.getmtime(full_path)
                        
                        results.append({
                            'name': file,
                            'path': str(full_path),
                            'size': size
                        })
        else:
            # Search only in the current directory
            for item in directory.iterdir():
                if item.is_file() and item.name.lower().endswith(extension.lower()):
                    results.append({
                        'name': item.name,
                        'path': str(item),
                        'size': item.stat().st_size
                    })
        
        return results
    
    def search_by_size(self, min_size, max_size, directory_path, search_subdirs=False):
        """
        Search for files within a specific size range (in bytes).
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory does not exist or is not a directory: {directory}")
        
        results = []
        
        if search_subdirs:
            # Recursive search
            for root, dirs, files in os.walk(directory):
                for file in files:
                    full_path = Path(root) / file
                    size = full_path.stat().st_size
                    if min_size <= size <= max_size:
                        results.append({
                            'name': file,
                            'path': str(full_path),
                            'size': size
                        })
        else:
            # Search only in the current directory
            for item in directory.iterdir():
                if item.is_file():
                    size = item.stat().st_size
                    if min_size <= size <= max_size:
                        results.append({
                            'name': item.name,
                            'path': str(item),
                            'size': size
                        })
        
        return results


if __name__ == "__main__":
    # Example usage
    searcher = SearchManager()
    import os
    current_dir = os.getcwd()
    print(f"Searching for 'py' in {current_dir}")
    results = searcher.search_in_directory('py', current_dir)
    for result in results:
        print(f"  {result['name']} - {result['path']}")