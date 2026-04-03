import os
import tkinter as tk
from tkinter import ttk

class FileTreePanel(ttk.Frame):
    def __init__(self, parent, on_select_callback):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        
        tools = ttk.Frame(self)
        tools.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(tools, text="☑ Check All", command=lambda: self._bulk_toggle(True), width=12).pack(side=tk.LEFT)
        ttk.Button(tools, text="☐ Uncheck All", command=lambda: self._bulk_toggle(False), width=12).pack(side=tk.LEFT, padx=5)
        
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(container, columns=("check", "size", "id"), selectmode="browse")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.heading("#0", text="File / Folder Name", anchor=tk.W)
        
        self.tree.column("check", width=40, minwidth=40, stretch=False, anchor=tk.CENTER)
        self.tree.heading("check", text="Inc.")
        
        self.tree.column("size", width=80, anchor=tk.E)
        self.tree.heading("size", text="Size")
        
        self.tree.column("id", width=150)
        self.tree.heading("id", text="Stable ID")
        
        # UI Tags for locked modules
        self.tree.tag_configure("locked", foreground="#999999")
        self.tree.tag_configure("module_root", font=("Segoe UI", 9, "bold"), foreground="#0055AA")
        
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item_id = self.tree.identify_row(event.y)
            
            if column == "#1" and item_id:
                tags = self.tree.item(item_id, "tags")
                if "locked" in tags:
                    # Ignore clicks on locked children
                    return "break"
                
                self._toggle_item(item_id)
                return "break"
        return

    def _set_node_state(self, item_id, check_state, add_tags=None, remove_tags=None):
        vals = list(self.tree.item(item_id, "values"))
        vals[0] = check_state
        self.tree.item(item_id, values=vals)

        tags = list(self.tree.item(item_id, "tags"))
        changed = False
        if add_tags:
            for t in add_tags:
                if t not in tags:
                    tags.append(t)
                    changed = True
        if remove_tags:
            for t in remove_tags:
                if t in tags:
                    tags.remove(t)
                    changed = True
        if changed:
            self.tree.item(item_id, tags=tags)

    def _lock_children(self, parent_id, lock: bool):
        for child in self.tree.get_children(parent_id):
            tags = list(self.tree.item(child, "tags"))
            state = "☑" if lock else "☐"

            # Always strip module_root if a parent asserts a lock over this node
            if "module_root" in tags:
                tags.remove("module_root")

            if lock:
                if "locked" not in tags:
                    tags.append("locked")
            else:
                if "locked" in tags:
                    tags.remove("locked")

            self.tree.item(child, tags=tags)
            vals = list(self.tree.item(child, "values"))
            vals[0] = state
            self.tree.item(child, values=vals)

            self._lock_children(child, lock)

    def _toggle_item(self, item_id):
        current_vals = list(self.tree.item(item_id, "values"))
        current_check = current_vals[0]
        new_state = "☐" if current_check == "☑" else "☑"
        
        tags = list(self.tree.item(item_id, "tags"))
        if "folder" in tags:
            if new_state == "☑":
                self._set_node_state(item_id, "☑", add_tags=["module_root"])
                self._lock_children(item_id, True)
            else:
                self._set_node_state(item_id, "☐", remove_tags=["module_root"])
                self._lock_children(item_id, False)
        else:
            self._set_node_state(item_id, new_state)

    def _bulk_toggle(self, checked: bool):
        """Standard check/uncheck that clears all locks."""
        state = "☑" if checked else "☐"
        def recurse(item_id):
            self._set_node_state(item_id, state, remove_tags=["locked", "module_root"])
            for child in self.tree.get_children(item_id):
                recurse(child)
                
        for child in self.tree.get_children(""):
            recurse(child)

    def check_specific_files(self, target_stable_ids: set) -> int:
        self._bulk_toggle(False)
        matched = [0]
        
        def traverse_and_check(item_id) -> bool:
            vals = list(self.tree.item(item_id, "values"))
            tags = self.tree.item(item_id, "tags")
            is_file = tags and tags[0] != "folder"
            
            has_checked_child = False
            
            if is_file:
                stable_id = vals[2]
                if stable_id in target_stable_ids:
                    vals[0] = "☑"
                    self.tree.item(item_id, values=vals)
                    matched[0] += 1
                    return True
            else:
                for child in self.tree.get_children(item_id):
                    if traverse_and_check(child):
                        has_checked_child = True
                        
                if has_checked_child:
                    self.tree.item(item_id, open=True)
                    
            return has_checked_child

        for child in self.tree.get_children():
            traverse_and_check(child)
            
        return matched[0]

    def _on_selection_change(self, event):
        selected = self.tree.selection()
        if selected:
            tags = self.tree.item(selected[0], "tags")
            if tags and tags[0] != "folder":
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

                item_id = self.tree.insert(parent_id, "end", text=f"{icon}{name}", values=values, open=False)
                
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

    def get_modules(self) -> dict:
        """
        Returns a dictionary of { "module_name": [list_of_abs_paths] }
        for all nodes explicitly tagged as module_root.
        """
        modules = {}
        def traverse(item_id):
            tags = self.tree.item(item_id, "tags")
            if "module_root" in tags:
                raw_text = self.tree.item(item_id, "text")
                name = raw_text.replace("📁 ", "").strip()
                paths = self.get_checked_files(item_id)
                modules[name] = paths
            else:
                for child in self.tree.get_children(item_id):
                    traverse(child)

        for child in self.tree.get_children(""):
            traverse(child)

        return modules