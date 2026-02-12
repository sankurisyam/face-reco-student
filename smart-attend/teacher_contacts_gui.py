import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

CONFIG_PATH = 'parent_config.json'
BRANCHES = ['CSE', 'AIML', 'CSD', 'CAI', 'CSM']


def _load():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def _save(cfg):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, indent=4)


class TeacherContactsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Manage Teacher Contacts')
        self.root.geometry('640x420')
        self._build()
        self._load()

    def _build(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        # Default teacher contact
        ttk.Label(frm, text='Default Teacher Contact', font=('Arial', 11, 'bold')).grid(row=0, column=0, columnspan=4, sticky='w')
        ttk.Label(frm, text='Name:').grid(row=1, column=0, sticky='e')
        self.default_name = tk.StringVar()
        ttk.Entry(frm, textvariable=self.default_name, width=30).grid(row=1, column=1, padx=6, sticky='w')

        ttk.Label(frm, text='Email:').grid(row=1, column=2, sticky='e')
        self.default_email = tk.StringVar()
        ttk.Entry(frm, textvariable=self.default_email, width=30).grid(row=1, column=3, padx=6, sticky='w')

        ttk.Label(frm, text='Mobile:').grid(row=2, column=0, sticky='e', pady=(6, 0))
        self.default_mobile = tk.StringVar()
        ttk.Entry(frm, textvariable=self.default_mobile, width=20).grid(row=2, column=1, padx=6, sticky='w', pady=(6, 0))

        # Separator
        ttk.Separator(frm, orient='horizontal').grid(row=3, column=0, columnspan=4, sticky='ew', pady=12)

        # Per-branch contacts
        ttk.Label(frm, text='Per-branch Teacher Contacts', font=('Arial', 11, 'bold')).grid(row=4, column=0, columnspan=4, sticky='w')

        # Left: form to add/update
        ttk.Label(frm, text='Branch:').grid(row=5, column=0, sticky='e', pady=6)
        self.branch_var = tk.StringVar()
        branch_combo = ttk.Combobox(frm, textvariable=self.branch_var, values=BRANCHES, state='readonly', width=12)
        branch_combo.grid(row=5, column=1, sticky='w', padx=6)

        ttk.Label(frm, text='Name:').grid(row=6, column=0, sticky='e')
        self.branch_name = tk.StringVar()
        ttk.Entry(frm, textvariable=self.branch_name, width=28).grid(row=6, column=1, sticky='w', padx=6)

        ttk.Label(frm, text='Email:').grid(row=7, column=0, sticky='e')
        self.branch_email = tk.StringVar()
        ttk.Entry(frm, textvariable=self.branch_email, width=28).grid(row=7, column=1, sticky='w', padx=6)

        ttk.Label(frm, text='Mobile:').grid(row=8, column=0, sticky='e')
        self.branch_mobile = tk.StringVar()
        ttk.Entry(frm, textvariable=self.branch_mobile, width=20).grid(row=8, column=1, sticky='w', padx=6)

        ttk.Button(frm, text='Add / Update', command=self.add_update_branch).grid(row=9, column=1, sticky='w', pady=8)

        # Right: treeview listing
        self.tree = ttk.Treeview(frm, columns=('branch', 'name', 'email', 'mobile'), show='headings', height=10)
        self.tree.heading('branch', text='Branch')
        self.tree.heading('name', text='Name')
        self.tree.heading('email', text='Email')
        self.tree.heading('mobile', text='Mobile')
        self.tree.column('branch', width=70, anchor='center')
        self.tree.column('name', width=140)
        self.tree.column('email', width=180)
        self.tree.column('mobile', width=110)
        self.tree.grid(row=5, column=2, rowspan=6, columnspan=2, padx=(10,0), sticky='nsew')

        # Controls below tree
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=11, column=2, columnspan=2, pady=(8,0), sticky='e')
        ttk.Button(btn_frame, text='Edit Selected', command=self.load_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text='Delete Selected', command=self.delete_selected).pack(side=tk.LEFT, padx=6)

        # Save / Close for default contact
        bottom_frame = ttk.Frame(frm)
        bottom_frame.grid(row=12, column=0, columnspan=4, pady=(12,0))
        ttk.Button(bottom_frame, text='Save All', command=self.save_all).pack(side=tk.LEFT, padx=6)
        ttk.Button(bottom_frame, text='Close', command=self.root.destroy).pack(side=tk.LEFT, padx=6)

    def _load(self):
        cfg = _load()
        tc = cfg.get('teacher_contact', {})
        default = tc.get('default', {})
        self.default_name.set(default.get('name', ''))
        self.default_email.set(default.get('email', ''))
        self.default_mobile.set(default.get('mobile', ''))

        # load by_branch
        for i in self.tree.get_children():
            self.tree.delete(i)
        byb = tc.get('by_branch', {})
        for branch, info in sorted(byb.items()):
            self.tree.insert('', 'end', values=(branch, info.get('name', ''), info.get('email', ''), info.get('mobile', '')))

    def add_update_branch(self):
        b = self.branch_var.get()
        if not b:
            messagebox.showerror('Validation', 'Select a branch')
            return
        name = self.branch_name.get().strip()
        email = self.branch_email.get().strip()
        mobile = self.branch_mobile.get().strip()
        # upsert in tree (replace if exists)
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, 'values')
            if vals[0] == b:
                self.tree.item(iid, values=(b, name, email, mobile))
                break
        else:
            self.tree.insert('', 'end', values=(b, name, email, mobile))
        # clear form
        self.branch_name.set('')
        self.branch_email.set('')
        self.branch_mobile.set('')

    def load_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], 'values')
        self.branch_var.set(vals[0])
        self.branch_name.set(vals[1])
        self.branch_email.set(vals[2])
        self.branch_mobile.set(vals[3])

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        self.tree.delete(sel[0])

    def save_all(self):
        # Build teacher_contact object
        default = {
            'name': self.default_name.get().strip(),
            'email': self.default_email.get().strip(),
            'mobile': self.default_mobile.get().strip()
        }
        by_branch = {}
        for iid in self.tree.get_children():
            branch, name, email, mobile = self.tree.item(iid, 'values')
            by_branch[branch] = {'name': name, 'email': email, 'mobile': mobile}

        cfg = _load()
        if 'teacher_contact' not in cfg:
            cfg['teacher_contact'] = {}
        cfg['teacher_contact']['default'] = default
        cfg['teacher_contact']['by_branch'] = by_branch
        _save(cfg)
        messagebox.showinfo('Saved', 'Teacher contacts updated in parent_config.json')


if __name__ == '__main__':
    root = tk.Tk()
    TeacherContactsGUI(root)
    root.mainloop()
