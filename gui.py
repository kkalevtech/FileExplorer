import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from file_explorer import (
    NativeFilesystem,
    DirectoryNavigator,
    create_file,
    create_directory,
    read_file_content,
    write_file_content,
    rename_item,
    delete_item,
    duplicate_item,
    copy_item,
    move_item,
    ConflictStrategy,
    search_by_name,
    SearchOptions,
    get_metadata,
    get_size_formatted,
    CreateFileCommand,
    CreateDirectoryCommand,
    DeleteFileCommand,
    DeleteDirectoryCommand,
    RenameCommand,
    CopyCommand,
    MoveCommand,
    OperationHistory,
    ConfigManager,
    FileExplorerError,
    PathNotFoundError,
    PermissionDeniedError,
    FileAlreadyExistsError,
)


BG = "#FFFFFF"
NAV_BG = "#B3D9FF"
TOOL_BG = "#F0F8FF"
STATUS_BG = "#B3D9FF"
SELECT_BG = "#ADD8E6"
FG = "#333333"
BTN_FG = "#1a1a1a"
SEP = "#CCCCCC"


class FileExplorerGUI:

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("File Explorer")
        self.root.geometry("960x620")
        self.root.minsize(640, 420)
        self.root.configure(bg=BG)

        self.fs = NativeFilesystem()
        self.nav = DirectoryNavigator(self.fs, Path.cwd())
        self.history = OperationHistory(limit=50)
        self.config = ConfigManager()
        self._clipboard: list[tuple[Path, str]] = []
        self._search_active = False
        self._last_search_pattern = ""

        self._setup_styles()
        self._setup_ui()
        self.root.after(100, self._load_directory)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Nav.TFrame", background=NAV_BG)
        style.configure("Tool.TFrame", background=TOOL_BG)
        style.configure("Content.TFrame", background=BG)
        style.configure("Status.TFrame", background=STATUS_BG)

        style.configure(
            "Treeview",
            background=BG,
            fieldbackground=BG,
            foreground=FG,
            rowheight=26,
            font=("Segoe UI", 10),
        )
        style.map("Treeview", background=[("selected", SELECT_BG)])
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background=NAV_BG,
            foreground=FG,
            relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", NAV_BG)])

        style.configure(
            "Nav.TButton",
            font=("Segoe UI", 10),
            foreground=BTN_FG,
            background=NAV_BG,
            borderwidth=0,
            focuscolor="none",
        )
        style.map(
            "Nav.TButton",
            background=[("active", "#9CC4E4"), ("pressed", "#8BB8D8")],
        )

        style.configure(
            "Tool.TButton",
            font=("Segoe UI", 9),
            foreground=BTN_FG,
            background=TOOL_BG,
            borderwidth=0,
            focuscolor="none",
            padding=(6, 3),
        )
        style.map(
            "Tool.TButton",
            background=[("active", "#D0E4F0"), ("pressed", "#C0D4E0")],
        )

        style.configure(
            "Search.TButton",
            font=("Segoe UI", 9),
            foreground=BTN_FG,
            background=NAV_BG,
            borderwidth=0,
            focuscolor="none",
            padding=(10, 3),
        )
        style.map(
            "Search.TButton",
            background=[("active", "#9CC4E4"), ("pressed", "#8BB8D8")],
        )

        style.configure("Separator", background=SEP)

        style.configure("Status.TLabel", font=("Segoe UI", 9), foreground=FG, background=STATUS_BG)
        style.configure("Path.TLabel", font=("Segoe UI", 10), foreground=FG, background=NAV_BG)

    # ------------------------------------------------------------------
     # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        # -- Navigation bar --
        nav_frame = ttk.Frame(self.root, style="Nav.TFrame")
        nav_frame.pack(side="top", fill="x")

        ttk.Button(nav_frame, text="< Back", style="Nav.TButton", command=self._go_back).pack(side="left", padx=(6, 0), pady=4)
        ttk.Button(nav_frame, text="Forward >", style="Nav.TButton", command=self._go_forward).pack(side="left", padx=2, pady=4)
        ttk.Button(nav_frame, text="^ Up", style="Nav.TButton", command=self._go_up).pack(side="left", padx=(2, 8), pady=4)

        self._path_var = tk.StringVar()
        self._path_entry = ttk.Entry(nav_frame, textvariable=self._path_var, font=("Segoe UI", 10))
        self._path_entry.pack(side="left", fill="x", expand=True, pady=4)
        self._path_entry.bind("<Return>", lambda e: self._go_to_path())

        ttk.Button(nav_frame, text="Go", style="Nav.TButton", command=self._go_to_path).pack(side="left", padx=(4, 6), pady=4)

        # -- Search bar --
        search_frame = ttk.Frame(self.root, style="Tool.TFrame")
        search_frame.pack(side="top", fill="x")

        ttk.Label(search_frame, text="Search:", font=("Segoe UI", 9), foreground=FG, background=TOOL_BG).pack(side="left", padx=(6, 2), pady=3)
        self._search_var = tk.StringVar()
        self._search_entry = ttk.Entry(search_frame, textvariable=self._search_var, font=("Segoe UI", 10), width=40)
        self._search_entry.pack(side="left", padx=2, pady=3)
        self._search_entry.bind("<Return>", lambda e: self._perform_search())
        ttk.Button(search_frame, text="Find", style="Search.TButton", command=self._perform_search).pack(side="left", padx=2, pady=3)
        ttk.Button(search_frame, text="Clear", style="Search.TButton", command=self._clear_search).pack(side="left", padx=2, pady=3)

        # -- Toolbar --
        tool_frame = ttk.Frame(self.root, style="Tool.TFrame")
        tool_frame.pack(side="top", fill="x")

        ttk.Button(tool_frame, text="+File", style="Tool.TButton", command=self._create_file).pack(side="left", padx=(6, 1), pady=2)
        ttk.Button(tool_frame, text="+Folder", style="Tool.TButton", command=self._create_folder).pack(side="left", padx=1, pady=2)
        ttk.Button(tool_frame, text="Rename", style="Tool.TButton", command=self._rename_selected).pack(side="left", padx=1, pady=2)
        ttk.Button(tool_frame, text="Delete", style="Tool.TButton", command=self._delete_selected).pack(side="left", padx=1, pady=2)
        ttk.Button(tool_frame, text="Duplicate", style="Tool.TButton", command=self._duplicate_selected).pack(side="left", padx=1, pady=2)

        ttk.Separator(tool_frame, orient="vertical").pack(side="left", fill="y", padx=6, pady=2)

        ttk.Button(tool_frame, text="Copy", style="Tool.TButton", command=self._copy_selected).pack(side="left", padx=1, pady=2)
        ttk.Button(tool_frame, text="Cut", style="Tool.TButton", command=self._cut_selected).pack(side="left", padx=1, pady=2)
        self._paste_btn = ttk.Button(tool_frame, text="Paste", style="Tool.TButton", command=self._paste_items)
        self._paste_btn.pack(side="left", padx=1, pady=2)

        ttk.Separator(tool_frame, orient="vertical").pack(side="left", fill="y", padx=6, pady=2)

        self._undo_btn = ttk.Button(tool_frame, text="Undo", style="Tool.TButton", command=self._undo)
        self._undo_btn.pack(side="left", padx=1, pady=2)
        self._redo_btn = ttk.Button(tool_frame, text="Redo", style="Tool.TButton", command=self._redo)
        self._redo_btn.pack(side="left", padx=1, pady=2)

        # -- Treeview --
        content_frame = ttk.Frame(self.root, style="Content.TFrame")
        content_frame.pack(side="top", fill="both", expand=True)

        columns = ("name", "size", "type", "modified", "attrs")
        self._tree = ttk.Treeview(content_frame, columns=columns, show="tree headings", selectmode="extended")
        self._tree.heading("#0", text="", anchor="w")
        self._tree.heading("name", text="Name", anchor="w")
        self._tree.heading("size", text="Size", anchor="e")
        self._tree.heading("type", text="Type", anchor="w")
        self._tree.heading("modified", text="Date Modified", anchor="w")
        self._tree.heading("attrs", text="Attributes", anchor="w")
        self._tree.column("#0", width=0, stretch=False, minwidth=0)
        self._tree.column("name", width=280, minwidth=120)
        self._tree.column("size", width=90, minwidth=60, anchor="e")
        self._tree.column("type", width=100, minwidth=60)
        self._tree.column("modified", width=160, minwidth=100)
        self._tree.column("attrs", width=80, minwidth=50)

        vsb = ttk.Scrollbar(content_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(content_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Button-3>", self._show_context_menu)
        self._tree.bind("<Delete>", lambda e: self._delete_selected())

        # -- Status bar --
        status_frame = ttk.Frame(self.root, style="Status.TFrame")
        status_frame.pack(side="bottom", fill="x")

        self._status_var = tk.StringVar(value="Ready")
        self._status_label = ttk.Label(status_frame, textvariable=self._status_var, style="Status.TLabel")
        self._status_label.pack(side="left", padx=8, pady=3)

    # ------------------------------------------------------------------
    # Directory loading
    # ------------------------------------------------------------------
    def _load_directory(self) -> None:
        self._path_var.set(str(self.nav.current))
        for item in self._tree.get_children():
            self._tree.delete(item)

        show_hidden = self.config.get("show_hidden_files")
        entries = self.nav.list_contents(show_hidden=show_hidden)

        parent_iid = self._tree.insert("", "end", text="", open=False)
        self._tree.set(parent_iid, "name", "..")
        self._tree.set(parent_iid, "type", "Folder")
        self._tree.item(parent_iid, tags=("parent",))

        dirs = sorted([e for e in entries if self.fs.is_dir(e)], key=lambda p: p.name.lower())
        files = sorted([e for e in entries if self.fs.is_file(e)], key=lambda p: p.name.lower())

        for entry in dirs + files:
            iid = self._tree.insert("", "end", text="", open=False)
            self._tree.set(iid, "name", entry.name)
            try:
                meta = get_metadata(self.fs, entry)
                self._tree.set(iid, "size", get_size_formatted(meta.size) if meta.is_file else "")
                self._tree.set(iid, "type", "Folder" if meta.is_dir else (meta.extension.upper() if meta.extension else "File"))
                self._tree.set(iid, "modified", self._format_time(meta.modified) if meta.modified else "")
                attrs_parts = []
                if meta.is_hidden:
                    attrs_parts.append("H")
                if meta.is_readonly:
                    attrs_parts.append("R")
                self._tree.set(iid, "attrs", " ".join(attrs_parts))
            except (PathNotFoundError, PermissionDeniedError):
                self._tree.set(iid, "type", "Folder" if self.fs.is_dir(entry) else "File")

            if self.fs.is_dir(entry):
                self._tree.item(iid, tags=("dir",))
            else:
                self._tree.item(iid, tags=("file",))

        self._tree.tag_configure("parent", font=("Segoe UI", 10, "bold"))
        self._tree.tag_configure("dir", font=("Segoe UI", 10))
        self._tree.tag_configure("file", font=("Segoe UI", 10))

        self._update_status(count=len(entries))
        self._update_buttons()

    def _format_time(self, timestamp: float) -> str:
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")

    def _update_status(self, count: int = 0, selected: str = "") -> None:
        parts = [f"{count} items"] if count else []
        if selected:
            parts.append(f"Selected: {selected}")
        self._status_var.set(" | ".join(parts) if parts else "Ready")

    def _update_buttons(self) -> None:
        self._undo_btn.configure(state="normal" if self.history.can_undo else "disabled")
        self._redo_btn.configure(state="normal" if self.history.can_redo else "disabled")
        self._paste_btn.configure(state="normal" if self._clipboard else "disabled")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _go_back(self) -> None:
        result = self.nav.go_back()
        if result:
            self._load_directory()

    def _go_forward(self) -> None:
        result = self.nav.go_forward()
        if result:
            self._load_directory()

    def _go_up(self) -> None:
        self.nav.go_up()
        self._load_directory()

    def _go_to_path(self) -> None:
        path_str = self._path_var.get().strip()
        if not path_str:
            return
        p = Path(path_str)
        if p.exists() and p.is_dir():
            self.nav.go_to(p)
            self._load_directory()
        else:
            messagebox.showerror("Error", f"Directory not found:\n{p}")

    def _on_double_click(self, event: tk.Event) -> None:
        iid = self._tree.identify_row(event.y)
        if not iid:
            return
        name = self._tree.set(iid, "name")
        if name == "..":
            self._go_up()
            return
        path = self.nav.current / name
        if self.fs.is_dir(path):
            self.nav.enter(name)
            self._load_directory()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def _create_file(self) -> None:
        name = simpledialog.askstring("New File", "Enter file name:", parent=self.root)
        if not name:
            return
        path = self.nav.current / name
        cmd = CreateFileCommand(self.fs, path)
        result = cmd.execute()
        if result.success:
            self.history.push(cmd)
            self._load_directory()
        else:
            messagebox.showerror("Error", result.error or f"Cannot create file: {name}")

    def _create_folder(self) -> None:
        name = simpledialog.askstring("New Folder", "Enter folder name:", parent=self.root)
        if not name:
            return
        path = self.nav.current / name
        cmd = CreateDirectoryCommand(self.fs, path)
        result = cmd.execute()
        if result.success:
            self.history.push(cmd)
            self._load_directory()
        else:
            messagebox.showerror("Error", result.error or f"Cannot create folder: {name}")

    def _rename_selected(self) -> None:
        path = self._get_selected_path()
        if not path:
            return
        new_name = simpledialog.askstring("Rename", "New name:", initialvalue=path.name, parent=self.root)
        if not new_name or new_name == path.name:
            return
        new_path = path.parent / new_name
        cmd = RenameCommand(self.fs, path, new_path)
        result = cmd.execute()
        if result.success:
            self.history.push(cmd)
            self._load_directory()
        else:
            messagebox.showerror("Error", result.error or "Cannot rename")

    def _delete_selected(self) -> None:
        paths = self._get_selected_paths()
        if not paths:
            return
        names = "\n".join(p.name for p in paths[:5])
        if len(paths) > 5:
            names += f"\n... and {len(paths) - 5} more"
        if not messagebox.askyesno("Confirm Delete", f"Delete these items?\n{names}", parent=self.root):
            return
        for path in paths:
            recursive = self.fs.is_dir(path)
            cmd = (DeleteDirectoryCommand(self.fs, path, recursive=True) if recursive
                   else DeleteFileCommand(self.fs, path))
            result = cmd.execute()
            if not result.success and result.error:
                messagebox.showerror("Error", result.error)
                break
            self.history.push(cmd)
        self._load_directory()

    def _duplicate_selected(self) -> None:
        path = self._get_selected_path()
        if not path:
            return
        try:
            new_path = duplicate_item(self.fs, path)
            self._load_directory()
            self._update_status(selected=f"Duplicated as {new_path.name}")
        except FileExplorerError as e:
            messagebox.showerror("Error", str(e))

    # ------------------------------------------------------------------
    # Copy / Move / Paste
    # ------------------------------------------------------------------
    def _copy_selected(self) -> None:
        paths = self._get_selected_paths()
        if not paths:
            return
        self._clipboard = [(p, "copy") for p in paths]
        self._update_buttons()
        self._update_status(selected=f"{len(paths)} item(s) copied")

    def _cut_selected(self) -> None:
        paths = self._get_selected_paths()
        if not paths:
            return
        self._clipboard = [(p, "cut") for p in paths]
        self._update_buttons()
        self._update_status(selected=f"{len(paths)} item(s) cut")

    def _paste_items(self) -> None:
        if not self._clipboard:
            return
        dest = self.nav.current
        for src, op in self._clipboard:
            dst = dest / src.name
            if op == "copy":
                cmd = CopyCommand(self.fs, src, dst)
            else:
                cmd = MoveCommand(self.fs, src, dst)
            result = cmd.execute()
            if result.success:
                self.history.push(cmd)
            else:
                if "already exists" in (result.error or "").lower():
                    if messagebox.askyesno("Conflict", f"{result.error}\nOverwrite?", parent=self.root):
                        cmd = CopyCommand(self.fs, src, dst, ConflictStrategy.OVERWRITE) if op == "copy" else MoveCommand(self.fs, src, dst, ConflictStrategy.OVERWRITE)
                        result = cmd.execute()
                        if result.success:
                            self.history.push(cmd)
                        else:
                            messagebox.showerror("Error", result.error or "Paste failed")
                else:
                    messagebox.showerror("Error", result.error or "Paste failed")
        if any(op == "cut" for _, op in self._clipboard):
            self._clipboard = []
            self._update_buttons()
        self._load_directory()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def _perform_search(self) -> None:
        pattern = self._search_var.get().strip()
        if not pattern:
            return
        self._last_search_pattern = pattern
        self._search_active = True

        options = SearchOptions(
            pattern=pattern,
            root_path=self.nav.current,
            recursive=True,
            case_sensitive=False,
            max_results=500,
        )

        for item in self._tree.get_children():
            self._tree.delete(item)

        def search_worker():
            try:
                results = search_by_name(self.fs, options)
                self.root.after(0, self._display_search_results, results)
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Search Error", str(e))

        self._status_var.set(f"Searching for '{pattern}'...")
        threading.Thread(target=search_worker, daemon=True).start()

    def _display_search_results(self, results) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)

        for r in results:
            iid = self._tree.insert("", "end", text="", open=False)
            self._tree.set(iid, "name", str(r.path.relative_to(self.nav.current)))
            try:
                meta = get_metadata(self.fs, r.path)
                self._tree.set(iid, "size", get_size_formatted(meta.size) if meta.is_file else "")
                self._tree.set(iid, "type", "Folder" if meta.is_dir else (meta.extension.upper() if meta.extension else "File"))
                self._tree.set(iid, "modified", self._format_time(meta.modified) if meta.modified else "")
            except (PathNotFoundError, PermissionDeniedError):
                self._tree.set(iid, "type", "Folder" if self.fs.is_dir(r.path) else "File")
            self._tree.item(iid, tags=("search_result",))

        self._tree.tag_configure("search_result", font=("Segoe UI", 10))
        self._status_var.set(f"Search: {len(results)} result(s) for '{self._last_search_pattern}'")

    def _clear_search(self) -> None:
        self._search_active = False
        self._search_var.set("")
        self._last_search_pattern = ""
        self._load_directory()

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------
    def _undo(self) -> None:
        result = self.history.undo()
        if result is None:
            return
        self._load_directory()
        if result.error:
            self._status_var.set(f"Undo note: {result.error}")

    def _redo(self) -> None:
        result = self.history.redo()
        if result is None:
            return
        self._load_directory()
        if result.error:
            self._status_var.set(f"Redo note: {result.error}")

    # ------------------------------------------------------------------
    # Selection events
    # ------------------------------------------------------------------
    def _on_select(self, event: tk.Event) -> None:
        paths = self._get_selected_paths()
        if not paths:
            self._update_status(count=len(self._tree.get_children()) - 1)
            return

        selected = ", ".join(p.name for p in paths[:3])
        if len(paths) > 3:
            selected += f" ... ({len(paths)} total)"

        if len(paths) == 1:
            try:
                meta = get_metadata(self.fs, paths[0])
                parts = [meta.name]
                if meta.is_file:
                    parts.append(get_size_formatted(meta.size))
                parts.append(f"Modified: {self._format_time(meta.modified)}")
                self._update_status(selected=" | ".join(parts))
            except (PathNotFoundError, PermissionDeniedError):
                self._update_status(selected=selected)
        else:
            self._update_status(selected=selected)

    def _show_context_menu(self, event: tk.Event) -> None:
        iid = self._tree.identify_row(event.y)
        if iid:
            self._tree.selection_set(iid)

        menu = tk.Menu(self.root, tearoff=False, bg=BG, fg=FG, font=("Segoe UI", 9))
        path = self._get_selected_path()

        if path:
            if self.fs.is_dir(path):
                menu.add_command(label="Open", command=lambda: self._open_dir(path))
            menu.add_command(label="Rename", command=self._rename_selected)
            menu.add_command(label="Delete", command=self._delete_selected)
            menu.add_command(label="Duplicate", command=self._duplicate_selected)
            menu.add_separator()
            menu.add_command(label="Copy", command=self._copy_selected)
            menu.add_command(label="Cut", command=self._cut_selected)

        if self._clipboard:
            if path is None:
                menu.add_separator()
            menu.add_command(label="Paste", command=self._paste_items)

        menu.add_separator()
        file_attr = get_metadata(self.fs, path) if path else None
        if file_attr:
            info = f"{file_attr.name}\nSize: {get_size_formatted(file_attr.size)}\nModified: {self._format_time(file_attr.modified)}"
            if file_attr.is_hidden:
                info += "\nHidden"
            if file_attr.is_readonly:
                info += "\nRead-only"
            menu.add_command(label="Properties", command=lambda: messagebox.showinfo("Properties", info, parent=self.root))

        menu.tk_popup(event.x_root, event.y_root)

    def _open_dir(self, path: Path) -> None:
        if self.fs.is_dir(path):
            self.nav.enter(path.name)
            self._load_directory()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_selected_path(self) -> Path | None:
        paths = self._get_selected_paths()
        return paths[0] if paths else None

    def _get_selected_paths(self) -> list[Path]:
        iids = self._tree.selection()
        result: list[Path] = []
        for iid in iids:
            name = self._tree.set(iid, "name")
            if not name or name == "..":
                continue
            result.append(self.nav.current / name)
        return result


def main() -> None:
    root = tk.Tk()
    app = FileExplorerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
