# Core Architecture - File Explorer

## Introduction

This document outlines the minimal core functionality required to build a File Explorer application that can be extended by multiple developers working in parallel. The core implementation focuses purely on backend logic and data operations, providing a stable foundation upon which GUI, styling, and advanced features can be built in separate branches.

The core system is intentionally lean - it handles fundamental filesystem operations and data management without assuming any particular presentation layer or user interaction pattern.

---

## Core Functionality

### 1. Directory Navigation

**What it does:** Provides the ability to read directory contents, traverse folder hierarchies, and maintain awareness of the current working directory context.

**Why it is important:** Navigation is the most fundamental operation in any file explorer. Without it, users cannot move between folders or access their files. This is the primary mechanism by which the entire application gains access to the filesystem.

**How it supports expansion:** A robust navigation system enables developers to build breadcrumb components, history tracking, bookmarks, folder tree views, and quick-access panels in their respective branches without worrying about底层 filesystem access.

---

### 2. File and Folder CRUD Operations

**What it does:** Implements create, read, update, and delete operations for both files and directories. This includes creating new files and folders, reading existing content, renaming items, and removing items from the filesystem.

**Why it is important:** Users expect to be able to organize their files - creating folders to group related content, renaming items to reflect their purpose, and deleting items that are no longer needed. These operations form the backbone of any file management workflow.

**How it supports expansion:** With core CRUD operations in place, branches can focus on implementing features like batch operations, undo/redo functionality, trash/recycle bin integration, and conflict resolution dialogs without reimplementing the underlying operations.

---

### 3. Path Handling and Resolution

**What it does:** Provides utilities for parsing, normalizing, constructing, and resolving file paths. Handles platform-specific path formats, resolves relative paths to absolute paths, and manages path edge cases such as symbolic links and traversal sequences.

**Why it is important:** Paths are the primary interface between the application and the filesystem. Consistent and correct path handling prevents bugs related to path construction, ensures cross-platform compatibility, and protects against directory traversal vulnerabilities.

**How it supports expansion:** A solid path abstraction layer allows developers to add features like path shortcuts, aliases, virtual paths, and custom path mappings in extension branches without duplicating path handling logic.

---

### 4. File Metadata Retrieval

**What it does:** Extracts and exposes metadata for files and folders, including file size, creation date, modification date, file type/extension, and basic attributes (readonly, hidden, system, archive).

**Why it is important:** Users rely on metadata to understand and organize their files - checking file sizes before disk operations, sorting by date to find recent work, or identifying file types to understand what applications can open them.

**How it supports expansion:** Metadata availability enables future branches to implement sorting and filtering systems, detailed file property dialogs, size visualization, and file type detection for custom icons.

---

### 5. Search Functionality

**What it does:** Provides basic search capabilities to locate files and folders by name within a given directory tree. Supports pattern matching and recursive directory traversal.

**Why it is important:** Finding files is a core use case for any file explorer. Even basic search capability dramatically improves user experience compared to manual folder browsing, especially in directories with many files.

**How it supports expansion:** A core search foundation allows extension branches to build advanced features like full-text search, content-based search, filter systems, search history, and saved search queries without rebuilding the basic search infrastructure.

---

### 6. Copy and Move Operations

**What it does:** Implements file and directory copying and moving operations, handling both single items and batch operations. Manages source and destination paths, handles naming conflicts, and provides progress information.

**Why it is important:** Copy and move are essential file management operations. Users frequently need to organize files by moving them between folders or create duplicates by copying them. These operations must be reliable and handle errors gracefully.

**How it supports expansion:** Core copy/move operations enable branches to implement advanced features like clipboard integration, drag-and-drop support, conflict resolution dialogs, pause/resume functionality, and queue management.

---

### 7. Error Handling and Permission Management

**What it does:** Provides structured error handling for filesystem operations, including permission errors, path not found, disk full, file in use, and access denied scenarios. Exposes clear error codes and messages that callers can use to determine appropriate responses.

**Why it is important:** Filesystem operations frequently fail due to external conditions beyond the application's control. Robust error handling ensures the application can respond appropriately to failures rather than crashing or leaving the user confused about what went wrong.

**How it supports expansion:** With proper error handling in place, extension branches can implement user-friendly error dialogs, automatic retry logic, fallback strategies, logging systems, and permission request dialogs for restricted operations.

---

### 8. Filesystem Abstraction Layer

**What it does:** Provides a clean interface or adapter layer that abstracts the underlying filesystem operations. This layer defines a contract for interacting with files and directories, allowing the actual filesystem calls to be encapsulated behind well-defined methods.

**Why it is important:** An abstraction layer decouples business logic from platform-specific filesystem APIs. This improves code maintainability, enables easier testing through mocking, and allows for future support of alternative storage backends (virtual filesystems, network storage, archives).

**How it supports expansion:** The abstraction layer is critical for multi-developer collaboration - it ensures all branches work against a consistent interface while allowing individual developers to optimize or replace filesystem implementation details without affecting other parts of the system.

---

### 9. Command and Operation Abstraction

**What it does:** Defines a structured pattern for representing filesystem operations as objects or commands. Each operation encapsulates its parameters, execution logic, and rollback capability. Provides a foundation for operation queuing, history, and potential undo functionality.

**Why it is important:** Command abstraction promotes clean architecture, improves testability, and enables advanced features that require operation metadata (such as progress tracking, cancellation, undo/redo, and operation logging).

**How it supports expansion:** This foundation allows extension branches to implement operation history panels, undo/redo stacks, batch operation management, and scheduled/deferred file operations without redesigning the core operation model.

---

### 10. Configuration and Preferences Storage

**What it does:** Manages application configuration and user preferences at the core level. Stores settings such as default starting directory, display preferences, and operation defaults. Provides an interface for reading and writing configuration data.

**Why it is important:** Even a minimal file explorer benefits from configurable behavior. Default paths, user preferences, and application state need to persist between sessions to provide a personalized experience.

**How it supports expansion:** A configuration system enables future branches to expose rich settings dialogs, theme preferences, operation defaults, and user-defined shortcuts without creating competing configuration mechanisms.

---

## Summary

The core implementation should focus on these ten areas to provide a solid, extensible foundation. Each functionality is self-contained but connects to the others through clean interfaces, allowing developers to work on different features in parallel without creating conflicts. The core deliberately excludes GUI, visual components, and advanced optional features - these belong in extension branches built on top of this foundation.