"""
Clipboard Manager Module
Handles copy/cut/paste operations for the File Explorer
"""

import shutil
from pathlib import Path


class ClipboardManager:
    def __init__(self):
        self.clipboard = []
        self.operation_type = None  # 'copy' or 'cut'
    
    def copy_items(self, items):
        """
        Add items to clipboard for copying.
        Items can be paths or names relative to current directory.
        """
        self.clipboard = [str(Path(item)) for item in items]
        self.operation_type = 'copy'
        return f"Copied {len(items)} item(s) to clipboard"
    
    def cut_items(self, items):
        """
        Add items to clipboard for cutting/moving.
        Items can be paths or names relative to current directory.
        """
        self.clipboard = [str(Path(item)) for item in items]
        self.operation_type = 'cut'
        return f"Cut {len(items)} item(s) to clipboard"
    
    def paste_items(self, destination_path):
        """
        Paste items from clipboard to destination path.
        """
        if not self.clipboard:
            return "Clipboard is empty"
        
        destination = Path(destination_path)
        if not destination.exists() or not destination.is_dir():
            raise ValueError(f"Destination path does not exist or is not a directory: {destination}")
        
        results = []
        for item_path_str in self.clipboard:
            item_path = Path(item_path_str)
            
            if not item_path.exists():
                results.append(f"Warning: {item_path} does not exist")
                continue
            
            dest_item_path = destination / item_path.name
            
            # Handle naming conflicts
            counter = 1
            original_dest_path = dest_item_path
            while dest_item_path.exists():
                stem = original_dest_path.stem
                suffix = original_dest_path.suffix
                dest_item_path = destination / f"{stem}_{counter}{suffix}"
                counter += 1
            
            try:
                if self.operation_type == 'copy':
                    if item_path.is_dir():
                        shutil.copytree(item_path, dest_item_path)
                    else:
                        shutil.copy2(item_path, dest_item_path)
                    results.append(f"Copied {item_path.name} to {dest_item_path}")
                
                elif self.operation_type == 'cut':
                    shutil.move(str(item_path), str(dest_item_path))
                    results.append(f"Moved {item_path.name} to {dest_item_path}")
                    # Remove from clipboard since it's moved
                    self.clear_clipboard()
            
            except Exception as e:
                results.append(f"Error processing {item_path}: {str(e)}")
        
        return results
    
    def get_clipboard_contents(self):
        """Return the current clipboard contents."""
        return {
            'items': self.clipboard,
            'operation': self.operation_type
        }
    
    def clear_clipboard(self):
        """Clear the clipboard."""
        self.clipboard = []
        self.operation_type = None
        return "Clipboard cleared"


if __name__ == "__main__":
    cb = ClipboardManager()
    print("Clipboard initialized:", cb.get_clipboard_contents())