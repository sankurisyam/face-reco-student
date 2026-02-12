import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
from datetime import datetime
from parent_notifications import ParentNotificationManager

class AbsenceNotificationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Send Absence Notifications")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # Initialize notification manager
        self.notification_manager = ParentNotificationManager()

        # Available branches
        self.branches = ['AIML', 'CAI', 'CSD', 'CSE', 'CSM']

        self.create_widgets()

    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Send Absence Notifications",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))

        subtitle_label = ttk.Label(main_frame, text="Select branch to send absence SMS to parents",
                                  font=("Arial", 10))
        subtitle_label.pack(pady=(0, 30))

        # Branch selection frame
        branch_frame = ttk.LabelFrame(main_frame, text="Branch Selection", padding="15")
        branch_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(branch_frame, text="Select Branch:").pack(anchor=tk.W, pady=(0, 5))

        self.branch_var = tk.StringVar()
        branch_combo = ttk.Combobox(branch_frame, textvariable=self.branch_var,
                                   values=self.branches, state="readonly")
        branch_combo.pack(fill=tk.X, pady=(0, 10))
        branch_combo.set("Select a branch...")

        # Preview button
        ttk.Button(branch_frame, text="Preview Absences",
                  command=self.preview_absences).pack(fill=tk.X, pady=(10, 5))

        # Preview text area
        self.preview_text = tk.Text(branch_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Action buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Send Notifications",
                  command=self.send_notifications,
                  style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=10)

        ttk.Button(button_frame, text="Cancel",
                  command=self.root.quit).pack(side=tk.LEFT, ipadx=20, ipady=10)

        # Status label
        self.status_label = ttk.Label(main_frame, text="", foreground="blue")
        self.status_label.pack(pady=(10, 0))

        # Configure button style
        style = ttk.Style()
        style.configure("Primary.TButton", background="#2E8B57", foreground="white", font=("Arial", 10, "bold"))

    def preview_absences(self):
        """Preview absences for selected branch"""
        branch = self.branch_var.get()
        if not branch or branch == "Select a branch...":
            messagebox.showwarning("Warning", "Please select a branch first.")
            return

        try:
            # Get today's date in DD/MM/YYYY format
            today = datetime.now().strftime("%d/%m/%Y")

            # Read attendance file
            attendance_file = f"Attendance_Records/Attendance_{branch}.csv"
            if not os.path.exists(attendance_file):
                self.preview_text.config(state=tk.NORMAL)
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(tk.END, f"No attendance records found for {branch}")
                self.preview_text.config(state=tk.DISABLED)
                return

            df = pd.read_csv(attendance_file)

            # Filter for today's records
            today_records = df[df['Date'] == today]

            if today_records.empty:
                self.preview_text.config(state=tk.NORMAL)
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(tk.END, f"No attendance records found for {branch} on {today}")
                self.preview_text.config(state=tk.DISABLED)
                return

            # Find absent students
            absent_students = []
            for _, row in today_records.iterrows():
                # Check if student is absent in any period
                periods = ['Period1', 'Period2', 'Period3', 'Period4', 'Period5', 'Period6']
                absent_periods = []

                for period in periods:
                    if period in row and str(row[period]).strip().lower() == 'absent':
                        absent_periods.append(period.replace('Period', ''))

                if absent_periods:
                    absent_students.append({
                        'roll_no': str(row['RollNo']).strip(),
                        'name': str(row['Name']).strip(),
                        'absent_periods': absent_periods
                    })

            # Display preview
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)

            if absent_students:
                self.preview_text.insert(tk.END, f"Absent students for {branch} on {today}:\n\n")
                for student in absent_students:
                    periods_str = ", ".join(student['absent_periods'])
                    self.preview_text.insert(tk.END, f"• {student['name']} ({student['roll_no']}) - Periods: {periods_str}\n")

                self.preview_text.insert(tk.END, f"\nTotal absent students: {len(absent_students)}")
            else:
                self.preview_text.insert(tk.END, f"No absences found for {branch} on {today}")

            self.preview_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview absences: {str(e)}")

    def send_notifications(self):
        """Send absence notifications to parents"""
        branch = self.branch_var.get()
        if not branch or branch == "Select a branch...":
            messagebox.showwarning("Warning", "Please select a branch first.")
            return

        # Confirm action
        if not messagebox.askyesno("Confirm", f"Are you sure you want to send absence notifications for {branch}?"):
            return

        try:
            self.status_label.config(text="Sending notifications...", foreground="blue")
            self.root.update()

            # Get today's date in DD/MM/YYYY format
            today = datetime.now().strftime("%d/%m/%Y")

            # Read attendance file
            attendance_file = f"Attendance_Records/Attendance_{branch}.csv"
            if not os.path.exists(attendance_file):
                messagebox.showerror("Error", f"No attendance records found for {branch}")
                self.status_label.config(text="")
                return

            df = pd.read_csv(attendance_file)

            # Filter for today's records
            today_records = df[df['Date'] == today]

            if today_records.empty:
                messagebox.showinfo("Info", f"No attendance records found for {branch} on {today}")
                self.status_label.config(text="")
                return

            # Find absent students and send notifications
            sent_count = 0
            failed_count = 0

            for _, row in today_records.iterrows():
                # Check if student is absent in any period
                periods = ['Period1', 'Period2', 'Period3', 'Period4', 'Period5', 'Period6']
                absent_periods = []

                for period in periods:
                    if period in row and str(row[period]).strip().lower() == 'absent':
                        absent_periods.append(period.replace('Period', ''))

                if absent_periods:
                    roll_no = str(row['RollNo']).strip()
                    student_name = str(row['Name']).strip()
                    periods_str = ", ".join(absent_periods)

                    # Send notification
                    try:
                        success = self.notification_manager.notify_absence(
                            student_name, roll_no, today
                        )
                        if success:
                            sent_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        print(f"Failed to send notification for {student_name} ({roll_no}): {e}")
                        failed_count += 1

            # Show results
            if sent_count > 0:
                message = f"Successfully sent {sent_count} absence notifications for {branch}."
                if failed_count > 0:
                    message += f" {failed_count} notifications failed."
                messagebox.showinfo("Success", message)
            else:
                messagebox.showwarning("Warning", "No notifications were sent. Check SMS configuration.")

            self.status_label.config(text="", foreground="blue")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to send notifications: {str(e)}")
            self.status_label.config(text="", foreground="blue")


def main():
    root = tk.Tk()
    app = AbsenceNotificationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()