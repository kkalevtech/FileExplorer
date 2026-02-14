# Python File Explorer - Command Reference

This document lists all available commands for the Python File Explorer terminal interface.

## Navigation Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `ls` / `dir` | `ls [path]` | List contents of the current directory or specified path |
| `cd` | `cd <directory>` | Change to the specified directory |
| `pwd` | `pwd` | Print the current working directory path |

## File and Directory Management

| Command | Syntax | Description |
|---------|--------|-------------|
| `mkdir` | `mkdir <directory_name>` | Create a new directory in the current location |
| `touch` | `touch <file_name>` | Create a new empty file in the current location |
| `rm` | `rm <file_or_directory_name>` | Delete a file or directory |
| `rmdir` | `rmdir <directory_name>` | Remove an empty directory |
| `rename` | `rename <old_name> <new_name>` | Rename a file or directory |

## File Operations

| Command | Syntax | Description |
|---------|--------|-------------|
| `mv` | `mv <source> <destination>` | Move or rename a file/directory |
| `cp` | `cp <source> <destination>` | Copy a file to a new location |
| `info` | `info <file_or_directory_name>` | Show detailed information about a file or directory |

## Search Functionality

| Command | Syntax | Description |
|---------|--------|-------------|
| `search` / `find` | `search <term>` | Search for files in the current directory by name |

## Clipboard Operations

| Command | Syntax | Description |
|---------|--------|-------------|
| `copy` | `copy <file_or_directory_name> [...]` | Copy files/directories to the clipboard |
| `cut` | `cut <file_or_directory_name> [...]` | Cut (mark for moving) files/directories to the clipboard |
| `paste` | `paste` | Paste files/directories from clipboard to current directory |

## Utility Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `clear` / `cls` | `clear` | Clear the terminal screen |
| `history` | `history` | Show command history (placeholder implementation) |
| `help` | `help` | Show help information with all available commands |
| `exit` / `quit` | `exit` | Exit the File Explorer application |

## Examples

```bash
# Navigate and list contents
ls
cd Documents
ls -l

# Create and manage files
mkdir new_folder
touch my_file.txt
rename old_name.txt new_name.txt

# File operations
cp file.txt backup/
mv file.txt new_location/
rm unwanted_file.txt

# Search and info
search python
info my_file.txt

# Clipboard operations
copy file1.txt file2.txt
paste
```

## Notes

- Most commands accept relative or absolute paths
- File and directory names with spaces should be enclosed in quotes
- The application maintains a current working directory context
- Clipboard operations persist until explicitly cleared or after a cut operation completes