# File Explorer

## Overview
A desktop file explorer application built with **Python** and **PyQt**.  
The goal is to create a modern, professional file manager with navigation, file operations, search functionality, clipboard system, and a customizable theme system.

---

## Technologies
- Python
- PyQt (Qt Framework)
- Standard libraries: os, shutil, pathlib, datetime, json
- Additional libraries: psutil (for disk usage), PIL/Pillow (for thumbnails), watchdog (for file monitoring)

---

## Core Features

### Navigation
- Display current directory (address bar)
- List files and folders
- Enter folder (double-click)
- Go back to parent directory
- Navigate using breadcrumb trail
- Quick access panel (Home, Desktop, Documents, Downloads)
- Recent locations history
- Refresh directory

### File Operations
- Create file
- Create folder
- Delete file/folder (with confirmation dialog)
- Rename file/folder
- Duplicate/copy file/folder
- Move files with drag-and-drop support
- Bulk operations (select multiple files for operations)
- File compression/decompression (zip/tar)

### File Information
- Name
- Type (File / Folder)
- Size
- Last Modified Date
- Creation Date
- Owner permissions
- File attributes (hidden, read-only, etc.)
- File preview (images, text files, PDFs)
- Thumbnail generation for images and videos

---

## Advanced Features

### Search
- Search files in the current directory
- Global search across all drives
- Advanced filters (by date, size, type, extension)
- Search result preview with highlighting
- Saved search queries

### Clipboard System
- Copy
- Cut
- Paste
- Move files
- Clipboard history
- Drag-and-drop operations

### File Interaction
- Double-click file to open with system default application
- Quick preview without opening external applications
- File properties dialog
- File associations management
- Batch file operations

### Theme System
- Preset themes (Dark, Light, Solarized, etc.)
- Custom theme creator
- Save themes as JSON
- Persist selected theme between sessions
- Syntax highlighting for code files
- Adaptive interface based on system theme

---

## Professional & Portfolio-Quality Features

### Performance & Monitoring
- Real-time disk usage visualization
- Background file system monitoring (auto-refresh when files change)
- Asynchronous loading for large directories
- Memory-efficient thumbnail generation
- File operation progress indicators
- Bandwidth throttling for large file operations

### Security Features
- File encryption/decryption
- Secure deletion (overwrite before delete)
- Password protection for sensitive folders
- File integrity verification (checksums)
- Permission management interface

### Productivity Features
- Tabbed interface for multiple directories
- Split view (dual pane) mode
- Bookmarks for frequently accessed locations
- Tagging system for files
- File synchronization between directories
- File versioning and backup
- Keyboard shortcuts customization
- Command palette for quick actions

### Modern UX/UI Improvements
- Responsive design that adapts to screen size
- Animated transitions between views
- Dark/light mode toggle with system preference detection
- Modern icon set with high-resolution SVG icons
- Smooth scrolling with kinetic effects
- Context-aware toolbar that changes based on selection
- Floating action buttons for common operations
- Hover previews for files and folders
- Bread crumb navigation with folder icons
- Visual file type indicators with color coding
- Progress bars for long-running operations
- Undo/redo functionality for file operations
- Status bar with contextual information and quick stats
- Customizable toolbar layout
- Collapsible side panels