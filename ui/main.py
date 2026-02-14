#!/usr/bin/env python3
"""
File Explorer Terminal Interface
Main entry point for the terminal-based file explorer
"""

import os
import sys
from pathlib import Path

# Import our modules
from core.file_manager import FileManager
from core.clipboard_manager import ClipboardManager
from core.search import SearchManager
from utils.file_info import get_file_info, format_size


class FileExplorerTerminal:
    def __init__(self):
        self.fm = FileManager()
        self.cb = ClipboardManager()
        self.searcher = SearchManager()
        self.running = True
    
    def run(self):
        """Run the main terminal interface loop."""
        print("Welcome to Python File Explorer!")
        print("Type 'help' for available commands or 'exit' to quit.")
        
        while self.running:
            try:
                # Show current path and get user input
                current_path = self.fm.get_current_path()
                prompt = f"[{current_path}]$ "
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Parse command and arguments
                parts = user_input.split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                # Execute the command
                self.execute_command(command, args)
                
            except KeyboardInterrupt:
                print("\n\nReceived interrupt signal. Exiting...")
                self.running = False
            except EOFError:
                print("\n\nEOF received. Exiting...")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")
    
    def execute_command(self, command, args):
        """Execute the given command with its arguments."""
        commands = {
            'ls': self.cmd_ls,
            'dir': self.cmd_ls,  # Alias for ls
            'cd': self.cmd_cd,
            'pwd': self.cmd_pwd,
            'mkdir': self.cmd_mkdir,
            'touch': self.cmd_touch,  # Create file
            'rm': self.cmd_rm,
            'rmdir': self.cmd_rmdir,
            'mv': self.cmd_mv,
            'cp': self.cmd_cp,
            'rename': self.cmd_rename,
            'info': self.cmd_info,
            'search': self.cmd_search,
            'find': self.cmd_search,  # Alias for search
            'copy': self.cmd_copy,
            'cut': self.cmd_cut,
            'paste': self.cmd_paste,
            'clear': self.cmd_clear,
            'cls': self.cmd_clear,  # Alias for clear (Windows)
            'history': self.cmd_history,
            'help': self.cmd_help,
            'exit': self.cmd_exit,
            'quit': self.cmd_exit,  # Alias for exit
        }
        
        if command in commands:
            commands[command](args)
        else:
            print(f"Unknown command: {command}. Type 'help' for available commands.")
    
    def cmd_ls(self, args):
        """List directory contents."""
        try:
            path = args[0] if args else None
            items = self.fm.list_directory(path)
            
            if not items:
                print("(empty)")
                return
            
            # Print header
            print(f"{'Name':<30} {'Type':<8} {'Size':<12} {'Modified'}")
            print("-" * 70)
            
            for item in items:
                name = item['name']
                item_type = "DIR" if item['is_dir'] else "FILE"
                size = format_size(item['size']) if not item['is_dir'] else "-"
                modified = item['modified']
                
                print(f"{name:<30} {item_type:<8} {size:<12} {modified}")
        
        except Exception as e:
            print(f"Error listing directory: {e}")
    
    def cmd_cd(self, args):
        """Change directory."""
        if not args:
            print("Usage: cd <directory>")
            return
        
        try:
            new_path = self.fm.change_directory(args[0])
            print(f"Changed to: {new_path}")
        except Exception as e:
            print(f"Error changing directory: {e}")
    
    def cmd_pwd(self, args):
        """Print current working directory."""
        print(self.fm.get_current_path())
    
    def cmd_mkdir(self, args):
        """Create a new directory."""
        if not args:
            print("Usage: mkdir <directory_name>")
            return
        
        try:
            path = self.fm.create_directory(args[0])
            print(f"Created directory: {path}")
        except Exception as e:
            print(f"Error creating directory: {e}")
    
    def cmd_touch(self, args):
        """Create a new empty file."""
        if not args:
            print("Usage: touch <file_name>")
            return
        
        try:
            path = self.fm.create_file(args[0])
            print(f"Created file: {path}")
        except Exception as e:
            print(f"Error creating file: {e}")
    
    def cmd_rm(self, args):
        """Delete a file or directory."""
        if not args:
            print("Usage: rm <file_or_directory_name>")
            return
        
        try:
            path = args[0]
            item_path = Path(self.fm.get_full_path(path))
            
            if item_path.is_dir():
                result = self.fm.delete_directory(path)
                print(f"Deleted directory: {result}")
            else:
                result = self.fm.delete_file(path)
                print(f"Deleted file: {result}")
        except Exception as e:
            print(f"Error deleting: {e}")
    
    def cmd_rmdir(self, args):
        """Remove an empty directory."""
        if not args:
            print("Usage: rmdir <directory_name>")
            return
        
        try:
            result = self.fm.delete_directory(args[0])
            print(f"Deleted directory: {result}")
        except Exception as e:
            print(f"Error removing directory: {e}")
    
    def cmd_mv(self, args):
        """Move/rename a file or directory."""
        if len(args) != 2:
            print("Usage: mv <source> <destination>")
            return
        
        try:
            result = self.fm.move_file(args[0], args[1])
            print(f"Moved: {result}")
        except Exception as e:
            print(f"Error moving: {e}")
    
    def cmd_cp(self, args):
        """Copy a file."""
        if len(args) != 2:
            print("Usage: cp <source> <destination>")
            return
        
        try:
            result = self.fm.copy_file(args[0], args[1])
            print(f"Copied: {result}")
        except Exception as e:
            print(f"Error copying: {e}")
    
    def cmd_rename(self, args):
        """Rename a file or directory."""
        if len(args) != 2:
            print("Usage: rename <old_name> <new_name>")
            return
        
        try:
            result = self.fm.rename_file(args[0], args[1])
            print(f"Renamed: {result}")
        except Exception as e:
            print(f"Error renaming: {e}")
    
    def cmd_info(self, args):
        """Show detailed information about a file or directory."""
        if not args:
            print("Usage: info <file_or_directory_name>")
            return
        
        try:
            path = self.fm.get_full_path(args[0])
            info = get_file_info(path)
            
            print(f"Name: {info['name']}")
            print(f"Path: {info['path']}")
            print(f"Type: {info['type']}")
            print(f"Size: {format_size(info['size'])}")
            print(f"Owner: {info['owner']}")
            print(f"Permissions: {info['permissions']}")
            print(f"Created: {info['created']}")
            print(f"Modified: {info['modified']}")
            print(f"Hidden: {'Yes' if info['hidden'] else 'No'}")
        except Exception as e:
            print(f"Error getting info: {e}")
    
    def cmd_search(self, args):
        """Search for files in the current directory."""
        if not args:
            print("Usage: search <term>")
            return
        
        try:
            term = args[0]
            results = self.searcher.search_in_directory(term, self.fm.get_current_path())
            
            if not results:
                print(f"No files found matching '{term}'")
                return
            
            print(f"Found {len(results)} result(s) for '{term}':")
            for result in results:
                item_type = "DIR" if result['is_dir'] else "FILE"
                size = format_size(result['size']) if not result['is_dir'] else "-"
                print(f"  {result['name']} ({item_type}, {size})")
        except Exception as e:
            print(f"Error searching: {e}")
    
    def cmd_copy(self, args):
        """Add items to clipboard for copying."""
        if not args:
            print("Usage: copy <file_or_directory_name> [...]")
            return
        
        try:
            result = self.cb.copy_items(args)
            print(result)
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
    
    def cmd_cut(self, args):
        """Add items to clipboard for cutting."""
        if not args:
            print("Usage: cut <file_or_directory_name> [...]")
            return
        
        try:
            result = self.cb.cut_items(args)
            print(result)
        except Exception as e:
            print(f"Error cutting to clipboard: {e}")
    
    def cmd_paste(self, args):
        """Paste items from clipboard to current directory."""
        try:
            destination = self.fm.get_current_path()
            results = self.cb.paste_items(destination)
            
            if isinstance(results, list):
                for result in results:
                    print(result)
            else:
                print(results)
        except Exception as e:
            print(f"Error pasting from clipboard: {e}")
    
    def cmd_clear(self, args):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def cmd_history(self, args):
        """Show command history (placeholder implementation)."""
        print("Command history is not implemented in this version.")
    
    def cmd_help(self, args):
        """Show help information."""
        help_text = """
Available Commands:
  ls/dir              - List directory contents
  cd <directory>      - Change directory
  pwd                 - Print current working directory
  mkdir <name>        - Create a new directory
  touch <name>        - Create a new empty file
  rm <name>           - Delete a file or directory
  rmdir <name>        - Remove an empty directory
  mv <src> <dest>     - Move/rename a file or directory
  cp <src> <dest>     - Copy a file
  rename <old> <new>  - Rename a file or directory
  info <name>         - Show detailed information about a file/directory
  search/find <term>  - Search for files in current directory
  copy <name> [...]   - Copy files/dirs to clipboard
  cut <name> [...]    - Cut files/dirs to clipboard
  paste               - Paste from clipboard to current directory
  clear/cls           - Clear the terminal screen
  history             - Show command history
  help                - Show this help message
  exit/quit           - Exit the program
        """
        print(help_text)
    
    def cmd_exit(self, args):
        """Exit the program."""
        self.running = False
        print("Goodbye!")


def main():
    """Main entry point."""
    explorer = FileExplorerTerminal()
    explorer.run()


if __name__ == "__main__":
    main()