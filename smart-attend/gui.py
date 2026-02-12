# gui.py
from tkinter import Toplevel, Label, Button, ttk, messagebox, filedialog
from tkcalendar import DateEntry
import pandas as pd
import os
import tkinter as tk
import subprocess
import sys
from register import register_student
from student_profile import show_student_profile
from notification_settings import create_settings_window

def start_attendance(period_var, cam_source_var, branch_var, root):
    period = period_var.get()
    if period not in ['1', '2', '3', '4', '5', '6']:
        messagebox.showerror("Invalid Input", "Please enter a period number (1-6).")
        return
    branch = branch_var.get() if branch_var.get() else None
    source = cam_source_var.get()

    # Start attendance as a separate process so the dashboard stays open
    attendance_script = os.path.join(os.getcwd(), 'attendance.py')
    cmd = [sys.executable, attendance_script, '--period', str(period), '--source', source]
    if branch:
        cmd += ['--branch', branch]
    try:
        subprocess.Popen(cmd)
        messagebox.showinfo("Attendance Started", f"Attendance started for Period {period} (branch: {branch or 'ALL'}) in a separate window.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start attendance process: {e}")

def download_branch_by_date(branch_var, date_entry):
    branch = branch_var.get()
    date_str = date_entry.get()
    csv_file = os.path.join('Attendance_Records', f'Attendance_{branch}.csv')
    if not os.path.exists(csv_file):
        messagebox.showerror("File Not Found", f"No CSV found for {branch}.")
        return
    df = pd.read_csv(csv_file)
    filtered = df[df['Date'] == date_str]
    if filtered.empty:
        messagebox.showinfo("No Data", f"No attendance found for {branch} on {date_str}")
        return
    # Ask user where to save (external location allowed)
    default_name = f"Attendance_{branch}_{date_str.replace('/', '-')}.csv"
    initial_dir = os.path.expanduser("~")
    save_path = filedialog.asksaveasfilename(
        title="Save Attendance CSV",
        defaultextension=".csv",
        initialdir=initial_dir,
        initialfile=default_name,
        filetypes=[("CSV files", "*.csv")]
    )
    if not save_path:
        return
    filtered.to_csv(save_path, index=False)
    messagebox.showinfo("Downloaded", f"Saved: {save_path}")

def show_attendance_by_date():
    win = Toplevel()
    win.title("View Attendance by Date")

    Label(win, text="Select Branch:").grid(row=0, column=0, padx=5, pady=5)
    branch_var = ttk.Combobox(win, values=['CSE', 'AIML', 'CSD', 'CAI', 'CSM'], state="readonly")
    branch_var.grid(row=0, column=1, padx=5, pady=5)
    branch_var.set('CSE')

    Label(win, text="Select Date:").grid(row=1, column=0, padx=5, pady=5)
    date_entry = DateEntry(win, date_pattern='dd/mm/yyyy')
    date_entry.grid(row=1, column=1, padx=5, pady=5)

    def view_attendance():
        branch = branch_var.get()
        date_str = date_entry.get()
        csv_file = os.path.join("Attendance_Records", f"Attendance_{branch}.csv")
        if not os.path.exists(csv_file):
            messagebox.showerror("Error", f"No CSV found for {branch}")
            return
        df = pd.read_csv(csv_file)
        filtered = df[df['Date'] == date_str]
        if filtered.empty:
            messagebox.showinfo("No Data", f"No attendance found for {branch} on {date_str}")
            return
        # Show in a simple window
        top = Toplevel(win)
        top.title(f"Attendance for {branch} on {date_str}")
        text = filtered.to_string(index=False)
        Label(top, text=text, font=("Courier", 10), justify="left").pack(padx=10, pady=10)

    def download_attendance():
        branch = branch_var.get()
        date_str = date_entry.get()
        csv_file = os.path.join("Attendance_Records", f"Attendance_{branch}.csv")
        if not os.path.exists(csv_file):
            messagebox.showerror("Error", f"No CSV found for {branch}")
            return
        df = pd.read_csv(csv_file)
        filtered = df[df['Date'] == date_str]
        if filtered.empty:
            messagebox.showinfo("No Data", f"No attendance found for {branch} on {date_str}")
            return
        # Ask user where to save (external location allowed)
        default_name = f"Attendance_{branch}_{date_str.replace('/', '-')}.csv"
        initial_dir = os.path.expanduser("~")
        save_path = filedialog.asksaveasfilename(
            title="Save Attendance CSV",
            defaultextension=".csv",
            initialdir=initial_dir,
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv")]
        )
        if not save_path:
            return
        filtered.to_csv(save_path, index=False)
        messagebox.showinfo("Downloaded", f"Attendance saved as {save_path}")

    Button(win, text="View Attendance", command=view_attendance, bg="blue", fg="white").grid(row=2, column=0, padx=5, pady=10)
    Button(win, text="Download CSV", command=download_attendance, bg="green", fg="white").grid(row=2, column=1, padx=5, pady=10)

def build_gui():
    root = tk.Tk()
    root.title("Attendance System")

    tk.Label(root, text="Enter Period (1-6):", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10)
    period_var = tk.StringVar()
    tk.Entry(root, textvariable=period_var, font=("Arial", 12)).grid(row=0, column=1, padx=10, pady=10)

    # Branch selector (required when starting attendance)
    tk.Label(root, text="Branch:", font=("Arial", 12)).grid(row=0, column=2, padx=10, pady=10)
    branch_var = tk.StringVar(value="CSE")
    branch_combo_top = ttk.Combobox(root, textvariable=branch_var, values=['CSE','AIML','CSD','CAI','CSM'], state="readonly", width=8)
    branch_combo_top.grid(row=0, column=3, padx=10, pady=10)

    cam_source_var = tk.StringVar(value="mobile")
    tk.Label(root, text="Camera Source:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10)
    tk.Radiobutton(root, text="Mobile (IP Webcam)", variable=cam_source_var, value="mobile").grid(row=1, column=1, sticky="w")
    tk.Radiobutton(root, text="Laptop Webcam", variable=cam_source_var, value="laptop").grid(row=1, column=2, sticky="w")
    
    tk.Button(root, text="Start Attendance",
              command=lambda: start_attendance(period_var, cam_source_var, branch_var, root),
              bg="green", fg="white").grid(row=0, column=4, padx=10, pady=10)
    branch_combo = ttk.Combobox(root, textvariable=branch_var,
                 values=['CSE', 'AIML', 'CSD', 'CAI', 'CSM'],
                 state="readonly")
    branch_combo.grid(row=2, column=1, padx=10, pady=10)

    tk.Label(root, text="Date:", font=("Arial", 12)).grid(row=2, column=2, padx=10, pady=10)
    top_date_entry = DateEntry(root, date_pattern='dd/mm/yyyy')
    top_date_entry.grid(row=2, column=3, padx=10, pady=10)

    tk.Button(root, text="Download CSV",
              command=lambda: download_branch_by_date(branch_var, top_date_entry),
              bg="blue", fg="white").grid(row=2, column=4, padx=10, pady=10)

    tk.Button(root, text="Register Student",
              command=lambda: register_student(root),
              bg="orange", fg="black").grid(row=3, column=1, padx=10, pady=10)

    tk.Button(root, text="View Attendance by Date",
              command=show_attendance_by_date,
              bg="purple", fg="white").grid(row=4, column=1, padx=10, pady=10)

    tk.Button(root, text="Student Attendance Profile",
              command=lambda: show_student_profile(root, 'Attendance_Records', ['CSE', 'AIML', 'CSD', 'CAI', 'CSM'], 'Images_Attendance'),
              bg="teal", fg="white").grid(row=4, column=2, padx=10, pady=10)

    tk.Button(root, text="Notification Settings",
              command=lambda: create_settings_window(),
              bg="red", fg="white").grid(row=4, column=3, padx=10, pady=10)

    root.mainloop()
