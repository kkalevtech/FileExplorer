"""
File Information Module
Handles retrieving detailed information about files and directories
"""

import os
import stat
from pathlib import Path
from datetime import datetime


def get_file_info(filepath):
    """
    Get detailed information about a file or directory.
    Returns a dictionary with file information.
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File or directory does not exist: {filepath}")
    
    stat_info = path.stat()
    
    # Determine if it's a file or directory
    is_dir = path.is_dir()
    
    # Get file size
    size = stat_info.st_size if not is_dir else _get_directory_size(path)
    
    # Convert timestamps to readable format
    created_time = datetime.fromtimestamp(stat_info.st_ctime)
    modified_time = datetime.fromtimestamp(stat_info.st_mtime)
    
    # Get file type
    file_type = _get_file_type(path, is_dir)
    
    # Get permissions
    permissions = _get_permissions(stat_info.st_mode)
    
    # Get owner information (where available)
    try:
        import pwd
        owner = pwd.getpwuid(stat_info.st_uid).pw_name
    except ImportError:
        # On systems without pwd module (e.g., Windows)
        owner = "N/A"
    
    return {
        'name': path.name,
        'path': str(path),
        'is_directory': is_dir,
        'size': size,
        'type': file_type,
        'permissions': permissions,
        'owner': owner,
        'created': created_time.strftime('%Y-%m-%d %H:%M:%S'),
        'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
        'hidden': _is_hidden(path)
    }


def _get_directory_size(directory_path):
    """
    Calculate the total size of a directory by summing all file sizes within it.
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory_path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            try:
                total_size += filepath.stat().st_size
            except OSError:
                # Skip files that can't be accessed
                continue
    return total_size


def _get_file_type(path, is_dir):
    """
    Determine the file type based on extension or characteristics.
    """
    if is_dir:
        return "Directory"
    
    suffix = path.suffix.lower()
    
    # Common file types
    image_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.tiff']
    document_types = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx']
    audio_types = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
    video_types = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']
    archive_types = ['.zip', '.rar', '.tar', '.gz', '.7z', '.bz2']
    code_types = ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs']
    
    if suffix in image_types:
        return "Image"
    elif suffix in document_types:
        return "Document"
    elif suffix in audio_types:
        return "Audio"
    elif suffix in video_types:
        return "Video"
    elif suffix in archive_types:
        return "Archive"
    elif suffix in code_types:
        return f"Code ({suffix[1:].upper()})"
    else:
        return f"File ({suffix[1:].upper()})" if suffix else "File"


def _get_permissions(mode):
    """
    Convert file mode to a human-readable permission string.
    """
    perm_str = ""
    
    # Owner permissions
    perm_str += "r" if mode & stat.S_IRUSR else "-"
    perm_str += "w" if mode & stat.S_IWUSR else "-"
    perm_str += "x" if mode & stat.S_IXUSR else "-"
    
    # Group permissions
    perm_str += "r" if mode & stat.S_IRGRP else "-"
    perm_str += "w" if mode & stat.S_IWGRP else "-"
    perm_str += "x" if mode & stat.S_IXGRP else "-"
    
    # Other permissions
    perm_str += "r" if mode & stat.S_IROTH else "-"
    perm_str += "w" if mode & stat.S_IWOTH else "-"
    perm_str += "x" if mode & stat.S_IXOTH else "-"
    
    return perm_str


def _is_hidden(path):
    """
    Check if a file or directory is hidden.
    """
    # On Unix-like systems, files starting with . are hidden
    if path.name.startswith('.'):
        return True
    
    # On Windows, check the file attribute
    try:
        return bool(os.stat(path).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
    except AttributeError:
        # Not on Windows
        return False
    except:
        # If we can't check, assume it's not hidden
        return False


def format_size(size_bytes):
    """
    Format file size in a human-readable format.
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


if __name__ == "__main__":
    # Example usage
    import os
    current_file = __file__
    info = get_file_info(current_file)
    print(f"File Info for {current_file}:")
    for key, value in info.items():
        print(f"  {key}: {value}")