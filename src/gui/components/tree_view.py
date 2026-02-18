import os
import tkinter as tk
from tkinter import ttk

class FileTreePanel(ttk.Frame):
    def __init__(self, parent, on_select_callback):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        
        # Tools
        tools = ttk.Frame(self)
        tools.pack(fill=tk.X, pady=(0, 5))
        
        # Styled Buttons
        ttk.Button(tools, text="☑ Check All", command=lambda: self._bulk_toggle(True), width=12).pack(side=tk.LEFT)
        ttk.Button(tools, text="☐ Uncheck All", command=lambda: self._bulk_toggle(False), width=12).pack(side=tk.LEFT, padx=5)
        
        # Tree Container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Define Columns
        # Note: #0 is the tree structure (Name). We add 'check' as a distinct column.
        self.tree = ttk.Treeview(container, columns=("check", "size", "id"), selectmode="browse")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # --- Column Configuration (MO2 Style) ---
        
        # 1. The Tree Column (Name/Structure)
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.heading("#0", text="File / Folder Name", anchor=tk.W)
        
        # 2. The Checkbox Column (Strict width, first data column)
        self.tree.column("check", width=40, minwidth=40, stretch=False, anchor=tk.CENTER)
        self.tree.heading("check", text="Inc.")
        
        # 3. Metadata Columns
        self.tree.column("size", width=80, anchor=tk.E)
        self.tree.heading("size", text="Size")
        
        self.tree.column("id", width=150)
        self.tree.heading("id", text="Stable ID")
        
        # --- Event Bindings ---
        # We bind Button-1 (Left Click) to handle the checkbox strictly
        self.tree.bind("<Button-1>", self._on_click)
        # Selection event handles the preview logic
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _on_click(self, event):
        """
        Strict click handler to separate Toggle vs Select actions.
        """
        region = self.tree.identify_region(event.x, event.y)
        
        # Only interact if we clicked a cell (not a header, not the background)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item_id = self.tree.identify_row(event.y)
            
            # The 'check' column is typically #1 in the columns list.
            # identify_column returns string IDs like '#1', '#2'.
            if column == "#1" and item_id:
                # User specifically clicked the Checkbox column. Toggle it.
                self._toggle_item(item_id)
                # Return 'break' to prevent the tree from selecting this row
                # (Optional: remove if you want selection + toggle)
                return "break"

        # If user clicked the tree arrow or the name (Column #0), 
        # default Treeview behavior takes over (Expand or Select).
        return

    def _toggle_item(self, item_id):
        """Toggles the state of a single item and its children."""
        current_vals = list(self.tree.item(item_id, "values"))
        current_check = current_vals[0]
        
        # Toggle Logic
        # ☑ = True, ☐ = False
        new_state = "☐" if current_check == "☑" else "☑"
        
        self._set_check_recursive(item_id, new_state)

    def _set_check_recursive(self, item_id, state):
        vals = list(self.tree.item(item_id, "values"))
        vals[0] = state
        self.tree.item(item_id, values=vals)
        
        for child in self.tree.get_children(item_id):
            self._set_check_recursive(child, state)

    def _bulk_toggle(self, checked: bool):
        state = "☑" if checked else "☐"
        for child in self.tree.get_children():
            self._set_check_recursive(child, state)

    def _on_selection_change(self, event):
        """Handles updating the Preview Pane."""
        selected = self.tree.selection()
        if selected:
            tags = self.tree.item(selected[0], "tags")
            # Ensure it's a file, not a folder
            if tags and tags[0] != "folder":
                # tags[0] is abs_path, values[2] is stable_id
                stable_id = self.tree.item(selected[0], "values")[2]
                self.on_select_callback(tags[0], stable_id)

    def populate(self, tree_structure):
        self.clear()
        
        def insert_node(parent_id, structure):
            keys = sorted(structure.keys())
            folders = [k for k in keys if k != '__metadata__' and '__metadata__' not in structure[k]]
            files = [k for k in keys if k != '__metadata__' and '__metadata__' in structure[k]]
            
            for name in folders + files:
                node_data = structure[name]
                is_file = '__metadata__' in node_data
                
                # Default to Checked (☑)
                # Columns: [Check, Size, ID]
                values = ["☑", "", ""]
                
                if is_file:
                    meta = node_data['__metadata__']
                    try:
                        size = os.path.getsize(meta['abs_path'])
                        values = ["☑", f"{size:,} B", meta['stable_id']]
                    except OSError:
                        values = ["☑", "Err", meta['stable_id']]
                    icon = "📄 "
                else:
                    icon = "📁 "

                item_id = self.tree.insert(parent_id, "end", text=f"{icon}{name}", values=values, open=True)
                
                if is_file:
                    self.tree.item(item_id, tags=(node_data['__metadata__']['abs_path'], "file"))
                else:
                    self.tree.item(item_id, tags=("folder",))
                    insert_node(item_id, node_data)

        insert_node("", tree_structure)

    def get_checked_files(self, parent_id="") -> list:
        paths = []
        for item_id in self.tree.get_children(parent_id):
            vals = self.tree.item(item_id, "values")
            if vals[0] == "☑":
                tags = self.tree.item(item_id, "tags")
                if tags and tags[0] != "folder":
                    paths.append(tags[0])
                paths.extend(self.get_checked_files(item_id))
        return paths