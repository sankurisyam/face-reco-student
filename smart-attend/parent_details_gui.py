import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import json
import os
import re

class ParentDetailsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Parent Details Management - Face Recognition Attendance System")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Set theme
        style = ttk.Style()
        style.theme_use('clam')

        # Colors
        self.primary_color = "#2E8B57"
        self.secondary_color = "#32CD32"
        self.accent_color = "#FF6347"

        self.csv_file = "parent_contacts.csv"
        self.load_data()

        self.create_widgets()
        self.load_existing_data()

    def load_data(self):
        """Load parent contacts data from CSV (ensure mobile columns are strings)."""
        try:
            if os.path.exists(self.csv_file):
                # Read with explicit dtype for mobile columns to avoid pandas dtype coercion warnings
                try:
                    self.df = pd.read_csv(self.csv_file, dtype={ 'Parent_Mobile1': str, 'Parent_Mobile2': str })
                except Exception:
                    # fallback to generic read then coerce
                    self.df = pd.read_csv(self.csv_file)
                    self.df['Parent_Mobile1'] = self.df.get('Parent_Mobile1', '').fillna('').astype(str)
                    self.df['Parent_Mobile2'] = self.df.get('Parent_Mobile2', '').fillna('').astype(str)

                # Ensure required columns exist and normalize mobile columns
                required_cols = ['Roll_No', 'Student_Name', 'Parent_Email', 'Parent_Mobile1', 'Parent_Mobile2']
                for col in required_cols:
                    if col not in self.df.columns:
                        self.df[col] = ""

                # Ensure no NaN and mobile columns are strings
                self.df['Parent_Mobile1'] = self.df['Parent_Mobile1'].fillna('').astype(str)
                self.df['Parent_Mobile2'] = self.df['Parent_Mobile2'].fillna('').astype(str)
            else:
                # Create new dataframe with required columns
                self.df = pd.DataFrame(columns=['Roll_No', 'Student_Name', 'Parent_Email', 'Parent_Mobile1', 'Parent_Mobile2'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV file: {str(e)}")
            self.df = pd.DataFrame(columns=['Roll_No', 'Student_Name', 'Parent_Email', 'Parent_Mobile1', 'Parent_Mobile2'])

    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Parent Details Management",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Add/Edit Parent Details", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 20))

        # Create input fields
        self.create_input_fields(input_frame)

        # Buttons frame
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=(15, 0), sticky=tk.EW)

        # Buttons
        ttk.Button(btn_frame, text="Add Student", command=self.add_student,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Update Selected", command=self.update_student).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_form).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_student,
                  style="Danger.TButton").pack(side=tk.LEFT)

        # Data display frame
        display_frame = ttk.LabelFrame(main_frame, text="Student Records", padding="15")
        display_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for displaying data
        self.create_treeview(display_frame)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))

        # Configure styles
        style = ttk.Style()
        style.configure("Accent.TButton", background=self.primary_color, foreground="white")
        style.configure("Danger.TButton", background=self.accent_color, foreground="white")

    def create_input_fields(self, parent):
        """Create input fields for parent details"""
        # Roll Number
        ttk.Label(parent, text="Roll Number *:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.roll_var = tk.StringVar()
        roll_entry = ttk.Entry(parent, textvariable=self.roll_var, width=30)
        roll_entry.grid(row=0, column=1, padx=(10, 20), pady=5)
        roll_entry.focus()

        # Student Name
        ttk.Label(parent, text="Student Name *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.name_var, width=30).grid(row=1, column=1, padx=(10, 20), pady=5)

        # Parent Email
        ttk.Label(parent, text="Parent Email *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.email_var, width=30).grid(row=2, column=1, padx=(10, 20), pady=5)

        # Parent Mobile 1
        ttk.Label(parent, text="Parent Mobile 1 *:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.mobile1_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.mobile1_var, width=30).grid(row=3, column=1, padx=(10, 20), pady=5)

        # Parent Mobile 2
        ttk.Label(parent, text="Parent Mobile 2:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.mobile2_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.mobile2_var, width=30).grid(row=4, column=1, padx=(10, 20), pady=5)

        # Required fields note
        note_label = ttk.Label(parent, text="* Required fields", foreground=self.accent_color)
        note_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

    def create_treeview(self, parent):
        """Create treeview for displaying student records"""
        # Create treeview
        columns = ('Roll_No', 'Student_Name', 'Parent_Email', 'Parent_Mobile1', 'Parent_Mobile2')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=15)

        # Define headings
        self.tree.heading('Roll_No', text='Roll Number')
        self.tree.heading('Student_Name', text='Student Name')
        self.tree.heading('Parent_Email', text='Parent Email')
        self.tree.heading('Parent_Mobile1', text='Mobile 1')
        self.tree.heading('Parent_Mobile2', text='Mobile 2')

        # Define column widths
        self.tree.column('Roll_No', width=120)
        self.tree.column('Student_Name', width=150)
        self.tree.column('Parent_Email', width=200)
        self.tree.column('Parent_Mobile1', width=120)
        self.tree.column('Parent_Mobile2', width=120)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def load_existing_data(self):
        """Load existing data into treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Load data from dataframe
        for _, row in self.df.iterrows():
            self.tree.insert('', tk.END, values=(
                row.get('Roll_No', ''),
                row.get('Student_Name', ''),
                row.get('Parent_Email', ''),
                row.get('Parent_Mobile1', ''),
                row.get('Parent_Mobile2', '')
            ))

        self.status_var.set(f"Loaded {len(self.df)} student records")

    def validate_input(self):
        """Validate input fields"""
        roll_no = self.roll_var.get().strip()
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        mobile1 = self.mobile1_var.get().strip()

        # Check required fields
        if not roll_no:
            messagebox.showerror("Validation Error", "Roll Number is required!")
            return False

        if not name:
            messagebox.showerror("Validation Error", "Student Name is required!")
            return False

        if not email:
            messagebox.showerror("Validation Error", "Parent Email is required!")
            return False

        if not mobile1:
            messagebox.showerror("Validation Error", "Parent Mobile 1 is required!")
            return False

        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messagebox.showerror("Validation Error", "Invalid email format!")
            return False

        # Validate mobile numbers
        if not re.match(r'^\+91[6-9]\d{9}$', mobile1):
            messagebox.showerror("Validation Error", "Mobile 1 must be in format +91XXXXXXXXXX!")
            return False

        mobile2 = self.mobile2_var.get().strip()
        if mobile2 and not re.match(r'^\+91[6-9]\d{9}$', mobile2):
            messagebox.showerror("Validation Error", "Mobile 2 must be in format +91XXXXXXXXXX!")
            return False

        # Check for duplicate roll number
        if roll_no in self.df['Roll_No'].astype(str).values:
            if not hasattr(self, 'selected_item') or not self.selected_item:
                messagebox.showerror("Validation Error", "Roll Number already exists!")
                return False

        return True

    def add_student(self):
        """Add new student record"""
        if not self.validate_input():
            return

        # Create new record
        new_record = {
            'Roll_No': self.roll_var.get().strip(),
            'Student_Name': self.name_var.get().strip(),
            'Parent_Email': self.email_var.get().strip(),
            'Parent_Mobile1': self.mobile1_var.get().strip(),
            'Parent_Mobile2': self.mobile2_var.get().strip()
        }

        # Add to dataframe
        self.df = pd.concat([self.df, pd.DataFrame([new_record])], ignore_index=True)

        # Save to CSV
        self.save_data()

        # Refresh display
        self.load_existing_data()

        # Clear form
        self.clear_form()

        self.status_var.set("Student added successfully")

    def update_student(self):
        """Update selected student record"""
        if not hasattr(self, 'selected_item') or not self.selected_item:
            messagebox.showerror("Error", "Please select a student to update!")
            return

        if not self.validate_input():
            return

        # Get selected item index
        selected_values = self.tree.item(self.selected_item)['values']
        roll_no = selected_values[0]

        # Find index in dataframe
        idx = self.df[self.df['Roll_No'].astype(str) == str(roll_no)].index[0]

        # Update record
        self.df.at[idx, 'Roll_No'] = self.roll_var.get().strip()
        self.df.at[idx, 'Student_Name'] = self.name_var.get().strip()
        self.df.at[idx, 'Parent_Email'] = self.email_var.get().strip()
        self.df.at[idx, 'Parent_Mobile1'] = self.mobile1_var.get().strip()
        self.df.at[idx, 'Parent_Mobile2'] = self.mobile2_var.get().strip()

        # Save to CSV
        self.save_data()

        # Refresh display
        self.load_existing_data()

        # Clear form
        self.clear_form()

        self.status_var.set("Student updated successfully")

    def delete_student(self):
        """Delete selected student record"""
        if not hasattr(self, 'selected_item') or not self.selected_item:
            messagebox.showerror("Error", "Please select a student to delete!")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this student record?"):
            # Get selected item values
            selected_values = self.tree.item(self.selected_item)['values']
            roll_no = selected_values[0]

            # Remove from dataframe
            self.df = self.df[self.df['Roll_No'].astype(str) != str(roll_no)]

            # Save to CSV
            self.save_data()

            # Refresh display
            self.load_existing_data()

            # Clear form
            self.clear_form()

            self.status_var.set("Student deleted successfully")

    def on_tree_select(self, event):
        """Handle treeview selection"""
        selected_items = self.tree.selection()
        if selected_items:
            self.selected_item = selected_items[0]
            values = self.tree.item(self.selected_item)['values']

            # Populate form fields
            self.roll_var.set(values[0] if values[0] else "")
            self.name_var.set(values[1] if values[1] else "")
            self.email_var.set(values[2] if values[2] else "")
            self.mobile1_var.set(values[3] if values[3] else "")
            self.mobile2_var.set(values[4] if values[4] else "")
        else:
            self.selected_item = None

    def clear_form(self):
        """Clear all form fields"""
        self.roll_var.set("")
        self.name_var.set("")
        self.email_var.set("")
        self.mobile1_var.set("")
        self.mobile2_var.set("")
        if hasattr(self, 'selected_item'):
            self.selected_item = None

        # Clear treeview selection
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def save_data(self):
        """Save data to CSV file"""
        try:
            self.df.to_csv(self.csv_file, index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")

def main():
    root = tk.Tk()
    app = ParentDetailsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()