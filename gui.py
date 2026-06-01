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

# ── Modern color palette ─────────────────────────────────────────
SURFACE      = "#FFFFFF"
BG           = "#F3F4F6"
PRIMARY      = "#2563EB"
PRIMARY_LT   = "#EFF6FF"
PRIMARY_DK   = "#1D4ED8"
TEXT         = "#1F2937"
TEXT_SEC     = "#6B7280"
TEXT_LIGHT   = "#9CA3AF"
BORDER       = "#E5E7EB"
DANGER       = "#EF4444"
DANGER_LT    = "#FEF2F2"
SUCCESS      = "#10B981"
WARNING      = "#F59E0B"
ROW_ALT      = "#F9FAFB"
HOVER        = "#F3F4F6"
SHADOW       = "#0000000A"

# ── Icon set (clean Unicode) ────────────────────────────────────
ICON_BACK      = "\u25C0"    # ◀
ICON_FWD       = "\u25B6"    # ▶
ICON_UP        = "\u25B2"    # ▲
ICON_FILE      = "\U0001F4C4"   # 📄
ICON_FOLDER    = "\U0001F4C1"   # 📁
ICON_RENAME    = "\u270E"    # ✎
ICON_DELETE    = "\u2716"    # ✖
ICON_DUP       = "\u2396"    # ⎖
ICON_COPY      = "\u29C9"    # ⧉
ICON_CUT       = "\u2702"    # ✂
ICON_PASTE     = "\u2355"    # ⍕
ICON_UNDO      = "\u21A9"    # ↩
ICON_REDO      = "\u21AA"    # ↪
ICON_SEARCH    = "\u26B2"    # ⚲
ICON_CLOSE     = "\u2715"    # ✕
ICON_GO        = "\u27A1"    # ➡
ICON_FOLDER_BIG = "\U0001F4C1"  # 📁
ICON_FILE_BIG  = "\U0001F4C4"   # 📄


class IconButton(tk.Canvas):
    """A flat, modern icon button drawn on a Canvas."""

    def __init__(self, master, text="", icon="", command=None, fg=PRIMARY,
                 bg=SURFACE, active_bg=HOVER, font=("Segoe UI", 11, "bold"),
                 padx=10, pady=6, tooltip="", **kwargs):
        super().__init__(master, bg=bg, highlightthickness=0, relief="flat",
                         cursor="hand2", **kwargs)
        self._command = command
        self._fg = fg
        self._bg = bg
        self._active_bg = active_bg
        self._disabled = False

        full = f"{icon} {text}" if icon else text
        self._label = self.create_text(0, 0, text=full, anchor="center",
                                       fill=fg, font=font, justify="center")
        self._text_bbox = self.bbox(self._label)
        w = (self._text_bbox[2] - self._text_bbox[0]) + padx * 2
        h = (self._text_bbox[3] - self._text_bbox[1]) + pady * 2
        self.configure(width=w, height=h)
        cx, cy = w / 2, h / 2
        self.coords(self._label, cx, cy)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        self._tooltip_id = None
        if tooltip:
            self.bind("<Enter>", lambda e: self._show_tooltip(tooltip), "+")
            self.bind("<Leave>", lambda e: self._hide_tooltip(), "+")

    def _on_enter(self, event):
        if not self._disabled:
            self.configure(bg=self._active_bg)

    def _on_leave(self, event):
        self.configure(bg=self._bg)
        self._hide_tooltip()

    def _on_click(self, event):
        if not self._disabled and self._command:
            self._command()

    def _show_tooltip(self, text):
        x = self.winfo_rootx() + self.winfo_width() // 2
        y = self.winfo_rooty() + self.winfo_height() + 4
        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self._tooltip, text=text, bg="#1F2937", fg=SURFACE,
                       font=("Segoe UI", 9), padx=8, pady=3)
        lbl.pack()

    def _hide_tooltip(self):
        if hasattr(self, "_tooltip"):
            try:
                self._tooltip.destroy()
            except tk.TclError:
                pass

    def set_disabled(self, disabled):
        self._disabled = disabled
        self.itemconfigure(self._label, fill=TEXT_LIGHT if disabled else self._fg)
        self.configure(cursor="arrow" if disabled else "hand2")


class ModernButton(tk.Canvas):
    """Rounded modern button with icon + text, colored background."""

    def __init__(self, master, text="", icon="", command=None,
                 color=PRIMARY, text_color=SURFACE, font=("Segoe UI", 9, "bold"),
                 padx=14, pady=6, tooltip="", **kwargs):
        super().__init__(master, bg=master["bg"], highlightthickness=0,
                         relief="flat", cursor="hand2", **kwargs)
        self._command = command
        self._color = color
        self._text_color = text_color
        self._disabled = False
        self._bg = master["bg"]

        full = f"{icon} {text}" if icon else text
        self._label = self.create_text(0, 0, text=full, anchor="center",
                                       fill=text_color, font=font, justify="center")

        self.update_idletasks()
        bbox = self.bbox(self._label)
        tw = (bbox[2] - bbox[0]) + padx * 2
        th = (bbox[3] - bbox[1]) + pady * 2

        self._rect = self.create_rectangle(2, 2, tw - 2, th - 2,
                                           fill=color, outline="", width=0,  # no outline
                                           )
        # Round effect via dash hack – not real rounding, but looks polished
        self.tag_lower(self._rect)
        self.configure(width=tw, height=th)
        cx, cy = tw / 2, th / 2
        self.coords(self._label, cx, cy)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        if tooltip:
            self.bind("<Enter>", lambda e: self._show_tooltip(tooltip), "+")
            self.bind("<Leave>", lambda e: self._hide_tooltip(), "+")

    def _on_enter(self, event):
        if not self._disabled:
            self.itemconfigure(self._rect, fill=self._darken(self._color, 0.15))

    def _on_leave(self, event):
        if not self._disabled:
            self.itemconfigure(self._rect, fill=self._color)
        self._hide_tooltip()

    def _on_click(self, event):
        if not self._disabled and self._command:
            self._command()

    def _darken(self, color, amount):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        r = max(0, int(r * (1 - amount)))
        g = max(0, int(g * (1 - amount)))
        b = max(0, int(b * (1 - amount)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _show_tooltip(self, text):
        x = self.winfo_rootx() + self.winfo_width() // 2
        y = self.winfo_rooty() + self.winfo_height() + 4
        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self._tooltip, text=text, bg="#1F2937", fg=SURFACE,
                       font=("Segoe UI", 9), padx=8, pady=3)
        lbl.pack()

    def _hide_tooltip(self):
        if hasattr(self, "_tooltip"):
            try:
                self._tooltip.destroy()
            except tk.TclError:
                pass

    def set_disabled(self, disabled):
        self._disabled = disabled
        self.itemconfigure(self._label, fill=TEXT_LIGHT if disabled else self._text_color)
        self.itemconfigure(self._rect, fill="#D1D5DB" if disabled else self._color)
        self.configure(cursor="arrow" if disabled else "hand2")


class FileExplorerGUI:

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("File Explorer")
        self.root.geometry("1060x680")
        self.root.minsize(760, 480)
        self.root.configure(bg=BG)

        self.fs = NativeFilesystem()
        self.nav = DirectoryNavigator(self.fs, Path.cwd())
        self.history = OperationHistory(limit=50)
        self.config = ConfigManager()
        self._clipboard: list[tuple[Path, str]] = []
        self._search_active = False
        self._last_search_pattern = ""
        self._sort_col = "name"
        self._sort_rev = False
        self._drag_start_iid: str | None = None

        self._setup_window()
        self._build_header()
        self._build_toolbar()
        self._build_search_bar()
        self._build_file_list()
        self._build_status_bar()

        self.root.after(100, self._load_directory)

    # ── Window setup ────────────────────────────────────────────
    def _setup_window(self) -> None:
        try:
            if sys.platform == "win32":
                self.root.iconbitmap(default="")
        except Exception:
            pass

    # ── Header / Nav bar ────────────────────────────────────────
    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=SURFACE, highlightthickness=0)
        header.pack(side="top", fill="x")

        # subtle bottom shadow line
        shadow = tk.Frame(header, bg=BORDER, height=1)
        shadow.pack(side="bottom", fill="x")

        inner = tk.Frame(header, bg=SURFACE)
        inner.pack(side="top", fill="x", padx=12, pady=(8, 6))

        # Nav buttons
        self._back_btn = IconButton(inner, icon=ICON_BACK, fg=TEXT_SEC,
                                     tooltip="Go back (Alt+Left)",
                                     command=self._go_back)
        self._back_btn.pack(side="left", padx=(0, 2))

        self._fwd_btn = IconButton(inner, icon=ICON_FWD, fg=TEXT_SEC,
                                    tooltip="Go forward (Alt+Right)",
                                    command=self._go_forward)
        self._fwd_btn.pack(side="left", padx=2)

        self._up_btn = IconButton(inner, icon=ICON_UP, fg=TEXT_SEC,
                                   tooltip="Go up one level (Alt+Up)",
                                   command=self._go_up)
        self._up_btn.pack(side="left", padx=(2, 10))

        # Path bar
        path_frame = tk.Frame(inner, bg=BORDER, highlightthickness=0)
        path_frame.pack(side="left", fill="x", expand=True)

        self._path_var = tk.StringVar()
        self._path_entry = tk.Entry(
            path_frame, textvariable=self._path_var,
            font=("Segoe UI", 10), fg=TEXT, bg="#F9FAFB",
            relief="flat", insertbackground=PRIMARY,
            highlightthickness=1, highlightcolor=PRIMARY,
            highlightbackground=BORDER, bd=0
        )
        self._path_entry.pack(fill="x", expand=True)
        self._path_entry.bind("<Return>", lambda e: self._go_to_path())

        go_btn = IconButton(inner, icon=ICON_GO, fg=PRIMARY,
                             tooltip="Navigate to path",
                             command=self._go_to_path)
        go_btn.pack(side="left", padx=(4, 0))

        # keyboard shortcuts
        self.root.bind("<Alt-Left>", lambda e: self._go_back())
        self.root.bind("<Alt-Right>", lambda e: self._go_forward())
        self.root.bind("<Alt-Up>", lambda e: self._go_up())

    # ── Toolbar ─────────────────────────────────────────────────
    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self.root, bg=SURFACE, highlightthickness=0)
        toolbar.pack(side="top", fill="x")

        inner = tk.Frame(toolbar, bg=SURFACE)
        inner.pack(side="top", fill="x", padx=10, pady=(2, 6))

        # Row 1: CRUD
        row1 = tk.Frame(inner, bg=SURFACE)
        row1.pack(fill="x", pady=(0, 3))

        self._crud_buttons = []
        btn_specs = [
            (f"{ICON_FOLDER}  New Folder", SUCCESS, SURFACE, self._create_folder, "Create a new folder"),
            (f"{ICON_FILE}  New File", PRIMARY, SURFACE, self._create_file, "Create a new file"),
            (f"{ICON_RENAME}  Rename", WARNING, SURFACE, self._rename_selected, "Rename the selected item"),
            (f"{ICON_DELETE}  Delete", DANGER, SURFACE, self._delete_selected, "Delete the selected item(s)"),
            (f"{ICON_DUP}  Duplicate", TEXT_SEC, SURFACE, self._duplicate_selected, "Duplicate the selected item"),
        ]
        for text, color, text_color, cmd, tip in btn_specs:
            btn = ModernButton(row1, text=text, color=color, text_color=text_color,
                               command=cmd, tooltip=tip)
            btn.pack(side="left", padx=2)
            self._crud_buttons.append(btn)

        # Row 2: Copy/Move | Undo/Redo
        row2 = tk.Frame(inner, bg=SURFACE)
        row2.pack(fill="x")

        copy_specs = [
            (f"{ICON_COPY}  Copy", PRIMARY, SURFACE, self._copy_selected, "Copy selected item(s)"),
            (f"{ICON_CUT}  Cut", TEXT_SEC, SURFACE, self._cut_selected, "Cut selected item(s)"),
            (f"{ICON_PASTE}  Paste", SUCCESS, SURFACE, self._paste_items, "Paste from clipboard"),
        ]
        for text, color, text_color, cmd, tip in copy_specs:
            btn = ModernButton(row2, text=text, color=color, text_color=text_color,
                               command=cmd, tooltip=tip)
            btn.pack(side="left", padx=2)

        # Separator
        sep = tk.Frame(row2, bg=BORDER, width=1, height=24)
        sep.pack(side="left", padx=6, fill="y")

        self._undo_btn = ModernButton(row2, text=f"{ICON_UNDO}  Undo", color=TEXT_SEC,
                                       text_color=SURFACE, command=self._undo,
                                       tooltip="Undo last action (Ctrl+Z)")
        self._undo_btn.pack(side="left", padx=2)

        self._redo_btn = ModernButton(row2, text=f"{ICON_REDO}  Redo", color=TEXT_SEC,
                                       text_color=SURFACE, command=self._redo,
                                       tooltip="Redo last undone action (Ctrl+Y)")
        self._redo_btn.pack(side="left", padx=2)

        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-y>", lambda e: self._redo())

    # ── Search bar ──────────────────────────────────────────────
    def _build_search_bar(self) -> None:
        search_frame = tk.Frame(self.root, bg=BG, highlightthickness=0)
        search_frame.pack(side="top", fill="x", padx=12, pady=(0, 6))

        container = tk.Frame(search_frame, bg=SURFACE, highlightthickness=0)
        container.pack(fill="x")

        inner = tk.Frame(container, bg=SURFACE)
        inner.pack(padx=2, pady=2, fill="x")

        search_icon = tk.Label(inner, text=ICON_SEARCH, font=("Segoe UI", 12),
                                fg=TEXT_LIGHT, bg=SURFACE)
        search_icon.pack(side="left", padx=(6, 2))

        self._search_var = tk.StringVar()
        self._search_entry = tk.Entry(
            inner, textvariable=self._search_var,
            font=("Segoe UI", 10), fg=TEXT, bg=SURFACE,
            relief="flat", insertbackground=PRIMARY,
            highlightthickness=0, bd=0
        )
        self._search_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self._search_entry.bind("<Return>", lambda e: self._perform_search())

        self._find_btn = ModernButton(inner, text=f"{ICON_SEARCH} Find",
                                       color=PRIMARY, text_color=SURFACE,
                                       command=self._perform_search,
                                       tooltip="Search files by name",
                                       font=("Segoe UI", 9, "bold"), padx=10, pady=4)
        self._find_btn.pack(side="left", padx=(4, 2))

        self._clear_btn = ModernButton(inner, text=f"{ICON_CLOSE} Clear",
                                        color=TEXT_SEC, text_color=SURFACE,
                                        command=self._clear_search,
                                        tooltip="Clear search and return to browse",
                                        font=("Segoe UI", 9, "bold"), padx=10, pady=4)
        self._clear_btn.pack(side="left", padx=2)

    # ── File list ───────────────────────────────────────────────
    def _build_file_list(self) -> None:
        container = tk.Frame(self.root, bg=SURFACE, highlightthickness=0)
        container.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 6))

        # inner rounded-corner effect via padding
        list_frame = tk.Frame(container, bg=SURFACE, highlightthickness=1,
                              highlightcolor=BORDER, highlightbackground=BORDER)
        list_frame.pack(fill="both", expand=True)

        columns = ("name", "size", "type", "modified", "attrs")
        self._tree = ttk.Treeview(list_frame, columns=columns,
                                   show="tree headings", selectmode="extended",
                                   style="Modern.Treeview")

        # Configure treeview style
        style = ttk.Style()
        style.layout("Modern.Treeview", [("Modern.Treeview.treearea", {"sticky": "nswe"})])
        style.configure("Modern.Treeview",
                         background=SURFACE, fieldbackground=SURFACE,
                         foreground=TEXT, rowheight=32,
                         font=("Segoe UI", 10), borderwidth=0)
        style.map("Modern.Treeview",
                   background=[("selected", PRIMARY_LT)],
                   foreground=[("selected", PRIMARY_DK)])
        style.configure("Modern.Treeview.Heading",
                         font=("Segoe UI", 9, "bold"), foreground=TEXT_SEC,
                         background=SURFACE, borderwidth=0,
                         relief="flat", padding=(6, 6))
        style.map("Modern.Treeview.Heading",
                   background=[("active", "#F3F4F6")])

        # Columns
        self._tree.heading("#0", text="", anchor="w")
        self._tree.heading("name", text="Name", anchor="w")
        self._tree.heading("size", text="Size", anchor="e")
        self._tree.heading("type", text="Type", anchor="w")
        self._tree.heading("modified", text="Date Modified", anchor="w")
        self._tree.heading("attrs", text="Attributes", anchor="w")

        self._tree.column("#0", width=0, stretch=False, minwidth=0)
        self._tree.column("name", width=320, minwidth=140)
        self._tree.column("size", width=100, minwidth=70, anchor="e")
        self._tree.column("type", width=110, minwidth=70)
        self._tree.column("modified", width=170, minwidth=110)
        self._tree.column("attrs", width=80, minwidth=50)

        # Scrollbar
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # Heading click bindings for sorting
        for col in columns:
            self._tree.heading(col, command=lambda c=col: self._on_sort(c))

        # Bindings — drag selection
        self._tree.bind("<Button-1>", self._on_drag_start, "+")
        self._tree.bind("<B1-Motion>", self._on_drag_motion, "+")
        self._tree.bind("<ButtonRelease-1>", self._on_drag_end, "+")
        # Other bindings
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Button-3>", self._show_context_menu)
        self._tree.bind("<Delete>", lambda e: self._delete_selected())

        self.root.bind("<F5>", lambda e: self._load_directory())
        self.root.bind("<Control-a>", self._select_all)
        self.root.bind("<Control-A>", self._select_all)

        # Tag configurations
        self._tree.tag_configure("parent", font=("Segoe UI", 10, "bold"),
                                  foreground=PRIMARY)
        self._tree.tag_configure("dir", font=("Segoe UI", 10), foreground=PRIMARY_DK)
        self._tree.tag_configure("file", font=("Segoe UI", 10), foreground=TEXT)
        self._tree.tag_configure("search_result", font=("Segoe UI", 10),
                                  foreground=TEXT)
        self._tree.tag_configure("hidden", foreground=TEXT_LIGHT)
        self._tree.tag_configure("readonly", foreground=TEXT)

    # ── Status bar ──────────────────────────────────────────────
    def _build_status_bar(self) -> None:
        bar = tk.Frame(self.root, bg=SURFACE, highlightthickness=0)
        bar.pack(side="bottom", fill="x")

        # top border line
        top_line = tk.Frame(bar, bg=BORDER, height=1)
        top_line.pack(side="top", fill="x")

        inner = tk.Frame(bar, bg=SURFACE)
        inner.pack(side="top", fill="x", padx=14, pady=(5, 7))

        self._status_var = tk.StringVar(value="Ready")
        self._status_icon = tk.Label(inner, text="", font=("Segoe UI", 10),
                                      fg=TEXT_SEC, bg=SURFACE)
        self._status_icon.pack(side="left", padx=(0, 4))

        self._status_label = tk.Label(inner, textvariable=self._status_var,
                                       font=("Segoe UI", 9), fg=TEXT_SEC,
                                       bg=SURFACE, anchor="w")
        self._status_label.pack(side="left", fill="x", expand=True)

        self._dir_count_label = tk.Label(inner, text="", font=("Segoe UI", 9),
                                          fg=TEXT_LIGHT, bg=SURFACE)
        self._dir_count_label.pack(side="right", padx=4)

        self._file_count_label = tk.Label(inner, text="", font=("Segoe UI", 9),
                                           fg=TEXT_LIGHT, bg=SURFACE)
        self._file_count_label.pack(side="right", padx=4)

    # ── Directory loading ───────────────────────────────────────
    def _load_directory(self) -> None:
        curr = self.nav.current
        self._path_var.set(str(curr))

        for item in self._tree.get_children():
            self._tree.delete(item)

        show_hidden = self.config.get("show_hidden_files")
        entries = self.nav.list_contents(show_hidden=show_hidden)

        # ".." parent entry
        parent_iid = self._tree.insert("", "end", text="", open=False)
        self._tree.set(parent_iid, "name", f"{ICON_UP}  ..")
        self._tree.set(parent_iid, "type", "Folder")
        self._tree.set(parent_iid, "attrs", "")
        self._tree.item(parent_iid, tags=("parent",))

        # Collect entries with metadata
        item_data = []
        for entry in entries:
            is_dir = self.fs.is_dir(entry)
            try:
                meta = get_metadata(self.fs, entry)
            except (PathNotFoundError, PermissionDeniedError):
                meta = None
            item_data.append((entry, meta, is_dir))

        # Sort
        item_data.sort(key=lambda t: self._sort_key(t[0], t[1], t[2]))

        dir_count = 0
        file_count = 0

        for entry, meta, is_dir in item_data:
            if is_dir:
                dir_count += 1
            else:
                file_count += 1

            iid = self._tree.insert("", "end", text="", open=False)
            name_prefix = f"{ICON_FOLDER}  " if is_dir else f"{ICON_FILE}  "

            if meta is not None:
                display_name = name_prefix + entry.name
                self._tree.set(iid, "name", display_name)
                self._tree.set(iid, "size",
                                get_size_formatted(meta.size) if meta.is_file else "")
                self._tree.set(iid, "type",
                                "Folder" if meta.is_dir
                                else (meta.extension.upper() if meta.extension else "File"))
                self._tree.set(iid, "modified",
                                self._format_time(meta.modified) if meta.modified else "")
                attrs_parts = []
                if meta.is_hidden:
                    attrs_parts.append("H")
                if meta.is_readonly:
                    attrs_parts.append("R")
                self._tree.set(iid, "attrs", " ".join(attrs_parts))
            else:
                self._tree.set(iid, "name", name_prefix + entry.name)
                self._tree.set(iid, "type",
                                "Folder" if is_dir else "File")

            tags = ["dir" if is_dir else "file"]
            if entry.name.startswith("."):
                tags.append("hidden")
            self._tree.item(iid, tags=tuple(tags))

        total = len(entries)
        self._update_status(count=total, dir_count=dir_count, file_count=file_count)
        self._update_buttons()

    def _sort_key(self, entry: Path, meta, is_dir: bool) -> tuple:
        dir_order = 0 if is_dir else 1
        col = self._sort_col
        rev = self._sort_rev

        if col == "name":
            val = entry.name.lower()
        elif col == "size":
            val = meta.size if meta is not None and meta.is_file else (-1 if is_dir else 0)
        elif col == "type":
            if is_dir:
                val = ""
            elif meta is not None:
                val = meta.extension.lower()
            else:
                val = ""
        elif col == "modified":
            val = meta.modified if meta is not None else 0.0
        elif col == "attrs":
            parts = []
            if meta is not None:
                if meta.is_hidden:
                    parts.append("H")
                if meta.is_readonly:
                    parts.append("R")
            val = "".join(parts)
        else:
            val = entry.name.lower()

        return (dir_order, val if not rev else self._flip(val))

    def _flip(self, val):
        if isinstance(val, (int, float)):
            return -val
        if isinstance(val, str):
            return "".join(chr(0xFFFF - ord(c)) for c in val)
        return val

    def _on_sort(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False
        self._update_sort_indicators()
        self._load_directory()

    def _update_sort_indicators(self) -> None:
        indicator = " \u25B2" if not self._sort_rev else " \u25BC"
        for col in ("name", "size", "type", "modified", "attrs"):
            text = col.capitalize() if col != "name" else "Name"
            if col == self._sort_col:
                text += indicator
            self._tree.heading(col, text=text)

    def _format_time(self, timestamp: float) -> str:
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        if dt.date() == now.date():
            return dt.strftime("%I:%M %p")
        elif dt.year == now.year:
            return dt.strftime("%b %d, %I:%M %p")
        return dt.strftime("%b %d %Y, %I:%M %p")

    def _update_status(self, count=0, dir_count=0, file_count=0, selected="") -> None:
        if selected:
            self._status_var.set(selected)
        elif count:
            self._status_var.set(f"{count} items")
        else:
            self._status_var.set("Ready")

        if dir_count or file_count:
            parts = []
            if dir_count:
                parts.append(f"{ICON_FOLDER} {dir_count}")
            if file_count:
                parts.append(f"{ICON_FILE} {file_count}")
            status = "  |  ".join(parts)
            mid = len(parts) // 2
            if parts:
                self._dir_count_label.configure(
                    text=f"{ICON_FOLDER}  {dir_count}" if dir_count else "")
                self._file_count_label.configure(
                    text=f"{ICON_FILE}  {file_count}" if file_count else "")
        else:
            self._dir_count_label.configure(text="")
            self._file_count_label.configure(text="")

    def _update_buttons(self) -> None:
        self._undo_btn.set_disabled(not self.history.can_undo)
        self._redo_btn.set_disabled(not self.history.can_redo)
        # paste button disabled state is handled by _paste_btn being a ModernButton

    # ── Navigation ──────────────────────────────────────────────
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
            messagebox.showerror("Error", f"Directory not found:\n{p}",
                                 parent=self.root)

    # ── Drag selection ──────────────────────────────────────────
    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_start_iid = self._tree.identify_row(event.y)

    def _on_drag_motion(self, event: tk.Event) -> None:
        if not self._drag_start_iid:
            return
        current_iid = self._tree.identify_row(event.y)
        if not current_iid or current_iid == self._drag_start_iid:
            return
        children = self._tree.get_children()
        if self._drag_start_iid not in children or current_iid not in children:
            return
        s = children.index(self._drag_start_iid)
        e = children.index(current_iid)
        if s > e:
            s, e = e, s
        self._tree.selection_set(children[s:e + 1])

    def _on_drag_end(self, event: tk.Event) -> None:
        self._drag_start_iid = None

    # ── Navigation ──────────────────────────────────────────────
    def _on_double_click(self, event: tk.Event) -> None:
        iid = self._tree.identify_row(event.y)
        if not iid:
            return
        name_raw = self._tree.set(iid, "name")
        name = name_raw.split("  ", 1)[-1] if "  " in name_raw else name_raw
        if name == "..":
            self._go_up()
            return
        path = self.nav.current / name
        if self.fs.is_dir(path):
            self.nav.enter(name)
            self._load_directory()
        else:
            self._open_file_viewer(path)

    def _open_file_viewer(self, path: Path) -> None:
        win = tk.Toplevel(self.root)
        win.title(f"View: {path.name}")
        win.geometry("720x540")
        win.minsize(400, 300)
        win.configure(bg=SURFACE)

        # Metadata header
        header = tk.Frame(win, bg=SURFACE)
        header.pack(fill="x", padx=14, pady=(10, 4))
        try:
            meta = get_metadata(self.fs, path)
            info = f"{ICON_FILE}  {path.name}  |  {get_size_formatted(meta.size)}  |  Modified {self._format_time(meta.modified)}  |  {meta.extension.upper() if meta.extension else 'File'}"
        except (PathNotFoundError, PermissionDeniedError):
            info = f"{ICON_FILE}  {path.name}"

        tk.Label(header, text=info, font=("Segoe UI", 9), fg=TEXT_SEC,
                 bg=SURFACE, anchor="w").pack(fill="x")

        # Separator
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(0, 4))

        # Text area
        text_frame = tk.Frame(win, bg=SURFACE)
        text_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        inner = tk.Frame(text_frame, bg=SURFACE, highlightthickness=1,
                         highlightcolor=BORDER, highlightbackground=BORDER)
        inner.pack(fill="both", expand=True)

        text_widget = tk.Text(inner, wrap="word", font=("Cascadia Code", 10) if sys.platform == "win32" else ("Consolas", 10),
                              fg=TEXT, bg=SURFACE, relief="flat", bd=0,
                              padx=10, pady=10, state="disabled")
        text_widget.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(inner, orient="vertical", command=text_widget.yview)
        vsb.pack(side="right", fill="y")
        text_widget.configure(yscrollcommand=vsb.set)

        # Load content
        try:
            content = read_file_content(self.fs, path, mode="text")
            text_widget.configure(state="normal")
            text_widget.insert("1.0", content)
            text_widget.configure(state="disabled")
        except (FileExplorerError, UnicodeDecodeError):
            text_widget.configure(state="normal")
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", "[Binary file — cannot preview as text]\n\n")
            try:
                raw = read_file_content(self.fs, path, mode="binary")
                text_widget.insert("end", f"Size: {get_size_formatted(len(raw))}")
            except FileExplorerError:
                pass
            text_widget.configure(state="disabled")

        # Close button
        btn_frame = tk.Frame(win, bg=SURFACE)
        btn_frame.pack(fill="x", padx=14, pady=(0, 10))
        tk.Button(btn_frame, text="  Close  ", bg=PRIMARY, fg=SURFACE,
                  font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                  padx=16, pady=4, cursor="hand2",
                  command=win.destroy).pack(side="right")

        win.transient(self.root)
        win.grab_set()
        win.focus_set()

    # ── CRUD ────────────────────────────────────────────────────
    def _create_file(self) -> None:
        name = simpledialog.askstring("New File", "Enter file name:",
                                       parent=self.root)
        if not name:
            return
        path = self.nav.current / name
        cmd = CreateFileCommand(self.fs, path)
        result = cmd.execute()
        if result.success:
            self.history.push(cmd)
            self._load_directory()
        else:
            messagebox.showerror("Error", result.error or f"Cannot create file: {name}",
                                 parent=self.root)

    def _create_folder(self) -> None:
        name = simpledialog.askstring("New Folder", "Enter folder name:",
                                       parent=self.root)
        if not name:
            return
        path = self.nav.current / name
        cmd = CreateDirectoryCommand(self.fs, path)
        result = cmd.execute()
        if result.success:
            self.history.push(cmd)
            self._load_directory()
        else:
            messagebox.showerror("Error", result.error or f"Cannot create folder: {name}",
                                 parent=self.root)

    def _rename_selected(self) -> None:
        path = self._get_selected_path()
        if not path:
            messagebox.showinfo("Rename", "No item selected.", parent=self.root)
            return
        new_name = simpledialog.askstring("Rename", "New name:",
                                           initialvalue=path.name, parent=self.root)
        if not new_name or new_name == path.name:
            return
        new_path = path.parent / new_name
        cmd = RenameCommand(self.fs, path, new_path)
        result = cmd.execute()
        if result.success:
            self.history.push(cmd)
            self._load_directory()
        else:
            messagebox.showerror("Error", result.error or "Cannot rename",
                                 parent=self.root)

    def _delete_selected(self) -> None:
        paths = self._get_selected_paths()
        if not paths:
            return
        names = "\n".join(f"  {ICON_DELETE} {p.name}" for p in paths[:5])
        if len(paths) > 5:
            names += f"\n  ... and {len(paths) - 5} more"
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirm Delete")
        dialog.configure(bg=SURFACE)
        dialog.resizable(False, False)
        tk.Label(dialog, text="Delete these items?", font=("Segoe UI", 11, "bold"),
                 fg=TEXT, bg=SURFACE).pack(padx=20, pady=(14, 4))
        tk.Label(dialog, text=names, font=("Segoe UI", 10), fg=TEXT_SEC,
                 bg=SURFACE, justify="left").pack(padx=20, pady=(0, 10))
        btn_frame = tk.Frame(dialog, bg=SURFACE)
        btn_frame.pack(pady=(0, 12))
        def do_delete():
            dialog.destroy()
            for path in paths:
                recursive = self.fs.is_dir(path)
                cmd = (DeleteDirectoryCommand(self.fs, path, recursive=True)
                       if recursive else DeleteFileCommand(self.fs, path))
                result = cmd.execute()
                if not result.success and result.error:
                    messagebox.showerror("Error", result.error, parent=self.root)
                    break
                self.history.push(cmd)
            self._load_directory()
        tk.Button(btn_frame, text="  Delete  ", bg=DANGER, fg=SURFACE,
                  font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                  padx=16, pady=4, cursor="hand2",
                  command=do_delete).pack(side="left", padx=4)
        tk.Button(btn_frame, text="  Cancel  ", bg=BG, fg=TEXT,
                  font=("Segoe UI", 9), relief="flat", bd=0,
                  padx=16, pady=4, cursor="hand2",
                  command=dialog.destroy).pack(side="left", padx=4)
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def _duplicate_selected(self) -> None:
        paths = self._get_selected_paths()
        if not paths:
            return
        count = len(paths)
        successes = 0
        errors: list[str] = []
        for path in paths:
            try:
                duplicate_item(self.fs, path)
                successes += 1
            except FileExplorerError as e:
                errors.append(str(e))
        self._load_directory()
        if successes:
            plural = "s" if successes != 1 else ""
            self._update_status(selected=f"Duplicated {successes} item{plural}")
        if errors:
            messagebox.showerror("Error", "\n".join(errors[:3]), parent=self.root)

    # ── Copy / Move / Paste ─────────────────────────────────────
    def _copy_selected(self) -> None:
        paths = self._get_selected_paths()
        if not paths:
            return
        self._clipboard = [(p, "copy") for p in paths]
        self._update_status(
            selected=f"{ICON_COPY}  {len(paths)} item(s) copied to clipboard"
        )

    def _cut_selected(self) -> None:
        paths = self._get_selected_paths()
        if not paths:
            return
        self._clipboard = [(p, "cut") for p in paths]
        self._update_status(
            selected=f"{ICON_CUT}  {len(paths)} item(s) cut to clipboard"
        )

    def _paste_items(self) -> None:
        if not self._clipboard:
            return
        dest = self.nav.current
        results: list[str] = []
        for src, op in self._clipboard:
            dst = dest / src.name
            if op == "copy":
                cmd = CopyCommand(self.fs, src, dst)
            else:
                cmd = MoveCommand(self.fs, src, dst)
            result = cmd.execute()
            if result.success:
                self.history.push(cmd)
                results.append(f"  {ICON_PASTE} {src.name}")
            else:
                err = (result.error or "").lower()
                if "already exists" in err:
                    if messagebox.askyesno("Conflict",
                                           f"{result.error}\nOverwrite?",
                                           parent=self.root):
                        strat = ConflictStrategy.OVERWRITE
                        cmd = (CopyCommand(self.fs, src, dst, strat)
                               if op == "copy"
                               else MoveCommand(self.fs, src, dst, strat))
                        result = cmd.execute()
                        if result.success:
                            self.history.push(cmd)
                            results.append(f"  {ICON_PASTE} {src.name}")
                        else:
                            messagebox.showerror("Error",
                                                 result.error or "Paste failed",
                                                 parent=self.root)
                else:
                    messagebox.showerror("Error", result.error or "Paste failed",
                                         parent=self.root)
        if any(op == "cut" for _, op in self._clipboard):
            self._clipboard = []
        if results:
            self._update_status(selected=f"Pasted {len(results)} item(s)")
        self._load_directory()

    # ── Search ──────────────────────────────────────────────────
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

        self._status_var.set(f"{ICON_SEARCH}  Searching for '{pattern}'...")

        def search_worker():
            try:
                results = search_by_name(self.fs, options)
                self.root.after(0, self._display_search_results, results)
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Search Error",
                                str(e))

        threading.Thread(target=search_worker, daemon=True).start()

    def _display_search_results(self, results) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)

        for r in results:
            iid = self._tree.insert("", "end", text="", open=False)
            is_dir = self.fs.is_dir(r.path)
            prefix = f"{ICON_FOLDER}  " if is_dir else f"{ICON_FILE}  "
            try:
                rel = r.path.relative_to(self.nav.current)
                self._tree.set(iid, "name", prefix + str(rel))
            except ValueError:
                self._tree.set(iid, "name", prefix + r.path.name)

            try:
                meta = get_metadata(self.fs, r.path)
                self._tree.set(iid, "size",
                                get_size_formatted(meta.size) if meta.is_file else "")
                self._tree.set(iid, "type",
                                "Folder" if meta.is_dir
                                else (meta.extension.upper() if meta.extension else "File"))
                self._tree.set(iid, "modified",
                                self._format_time(meta.modified) if meta.modified else "")
            except (PathNotFoundError, PermissionDeniedError):
                self._tree.set(iid, "type", "Folder" if is_dir else "File")

            tags = ["search_result"]
            if is_dir:
                tags.append("dir")
            else:
                tags.append("file")
            self._tree.item(iid, tags=tuple(tags))

        n = len(results)
        msg = f"{ICON_SEARCH}  {n} result{'s' if n != 1 else ''} for '{self._last_search_pattern}'"
        self._status_var.set(msg)

    def _clear_search(self) -> None:
        self._search_active = False
        self._search_var.set("")
        self._last_search_pattern = ""
        self._load_directory()

    # ── Undo / Redo ─────────────────────────────────────────────
    def _undo(self) -> None:
        result = self.history.undo()
        if result is None:
            return
        self._load_directory()
        if result.error:
            self._update_status(selected=f"  Undo note: {result.error}")

    def _redo(self) -> None:
        result = self.history.redo()
        if result is None:
            return
        self._load_directory()
        if result.error:
            self._update_status(selected=f"  Redo note: {result.error}")

    # ── Selection ───────────────────────────────────────────────
    def _on_select(self, event: tk.Event) -> None:
        paths = self._get_selected_paths()
        if not paths:
            self._update_status(count=len(self._tree.get_children()) - 1)
            return

        if len(paths) == 1:
            p = paths[0]
            try:
                meta = get_metadata(self.fs, p)
                parts = [f"{ICON_FILE_BIG if meta.is_file else ICON_FOLDER_BIG}  {meta.name}"]
                if meta.is_file:
                    parts.append(get_size_formatted(meta.size))
                parts.append(self._format_time(meta.modified))
                if meta.is_hidden:
                    parts.append("Hidden")
                if meta.is_readonly:
                    parts.append("Read-only")
                self._update_status(selected="  |  ".join(parts))
            except (PathNotFoundError, PermissionDeniedError):
                self._update_status(selected=f"  {p.name}")
        else:
            names = ", ".join(p.name for p in paths[:3])
            if len(paths) > 3:
                names += f" ... (+{len(paths) - 3})"
            self._update_status(selected=f"  {len(paths)} selected: {names}")

    # ── Context menu ────────────────────────────────────────────
    def _show_context_menu(self, event: tk.Event) -> None:
        iid = self._tree.identify_row(event.y)
        if iid:
            sel = self._tree.selection()
            if iid not in sel:
                self._tree.selection_set(iid)
            if not self._tree.selection():
                self._tree.selection_set(iid)

        paths = self._get_selected_paths()
        n = len(paths)
        single = n == 1

        menu = tk.Menu(self.root, tearoff=False, bg=SURFACE, fg=TEXT,
                       font=("Segoe UI", 9), bd=0,
                       activebackground=PRIMARY_LT, activeforeground=PRIMARY_DK)

        if single:
            p = paths[0]
            if self.fs.is_dir(p):
                menu.add_command(
                    label=f"{ICON_UP}  Open",
                    command=lambda: self._open_dir(p)
                )
                menu.add_separator()
            menu.add_command(
                label=f"{ICON_RENAME}  Rename",
                command=self._rename_selected
            )
        menu.add_command(
            label=f"{ICON_DELETE}  Delete{' (' + str(n) + ')' if n > 1 else ''}",
            command=self._delete_selected
        )
        menu.add_command(
            label=f"{ICON_DUP}  Duplicate{' (' + str(n) + ')' if n > 1 else ''}",
            command=self._duplicate_selected
        )
        menu.add_separator()
        menu.add_command(
            label=f"{ICON_COPY}  Copy{' (' + str(n) + ')' if n > 1 else ''}",
            command=self._copy_selected
        )
        menu.add_command(
            label=f"{ICON_CUT}  Cut{' (' + str(n) + ')' if n > 1 else ''}",
            command=self._cut_selected
        )

        if self._clipboard:
            menu.add_separator()
            menu.add_command(
                label=f"{ICON_PASTE}  Paste",
                command=self._paste_items
            )

        if single:
            menu.add_separator()
            try:
                meta = get_metadata(self.fs, paths[0])
                info_parts = [f"Name: {meta.name}"]
                if meta.is_file:
                    info_parts.append(f"Size: {get_size_formatted(meta.size)}")
                info_parts.append(f"Modified: {self._format_time(meta.modified)}")
                if meta.is_hidden:
                    info_parts.append("Hidden")
                if meta.is_readonly:
                    info_parts.append("Read-only")
                info = "\n".join(info_parts)
                menu.add_command(
                    label=f"  Properties",
                    command=lambda: messagebox.showinfo(
                        "Properties", info, parent=self.root
                    ),
                )
            except (PathNotFoundError, PermissionDeniedError):
                pass
        elif n > 1:
            menu.add_separator()
            menu.add_command(
                label=f"  Properties ({n} selected)",
                command=lambda: self._show_multi_properties(paths)
            )

        menu.add_separator()
        menu.add_command(
            label="  Select All",
            command=self._select_all
        )

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _show_multi_properties(self, paths: list[Path]) -> None:
        dirs = sum(1 for p in paths if self.fs.is_dir(p))
        files = len(paths) - dirs
        total_size = 0
        for p in paths:
            try:
                meta = get_metadata(self.fs, p)
                total_size += meta.size
            except (PathNotFoundError, PermissionDeniedError):
                pass
        info = (
            f"Selected: {len(paths)} item(s)\n"
            f"{ICON_FOLDER} Folders: {dirs}\n"
            f"{ICON_FILE} Files: {files}\n"
            f"Total size: {get_size_formatted(total_size)}"
        )
        messagebox.showinfo("Properties", info, parent=self.root)

    def _open_dir(self, path: Path) -> None:
        if self.fs.is_dir(path):
            self.nav.enter(path.name)
            self._load_directory()

    # ── Selection helper ────────────────────────────────────────
    def _select_all(self, event: tk.Event | None = None) -> None:
        for iid in self._tree.get_children():
            name = self._tree.set(iid, "name")
            raw = name.split("  ", 1)[-1] if "  " in name else name
            if raw == "..":
                continue
            self._tree.selection_add(iid)

    def _get_selected_path(self) -> Path | None:
        paths = self._get_selected_paths()
        return paths[0] if paths else None

    def _get_selected_paths(self) -> list[Path]:
        iids = self._tree.selection()
        result: list[Path] = []
        for iid in iids:
            raw = self._tree.set(iid, "name")
            name = raw.split("  ", 1)[-1] if "  " in raw else raw
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
