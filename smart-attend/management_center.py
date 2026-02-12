import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

class ManagementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance System - Management Center")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Set theme
        style = ttk.Style()
        style.theme_use('clam')

        # Colors
        self.primary_color = "#2E8B57"
        self.secondary_color = "#32CD32"
        self.accent_color = "#FF6347"

        self.create_widgets()

        # Configure styles
        style.configure("Primary.TButton", background=self.primary_color, foreground="white", font=("Arial", 10, "bold"))
        style.configure("Secondary.TButton", background=self.secondary_color, foreground="white")
        style.configure("Accent.TButton", background=self.accent_color, foreground="white")

    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Face Recognition Attendance System",
                               font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 10))

        subtitle_label = ttk.Label(main_frame, text="Management Center",
                                  font=("Arial", 12))
        subtitle_label.pack(pady=(0, 30))

        # System Status Frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 20))

        # Check system components
        self.check_system_status(status_frame)

        # Management Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Management Options", padding="15")
        options_frame.pack(fill=tk.BOTH, expand=True)

        # Create option buttons
        self.create_option_buttons(options_frame)

        # Footer
        footer_label = ttk.Label(main_frame, text="Select an option above to manage your attendance system",
                                font=("Arial", 9), foreground="gray")
        footer_label.pack(pady=(20, 0))

    def check_system_status(self, parent):
        """Check and display system status"""
        # Check configuration files
        config_checks = [
            ("Parent Configuration", "parent_config.json"),
            ("Location Configuration", "location_config.json"),
            ("Parent Contacts", "parent_contacts.csv"),
            ("Face Recognition Models", "models/"),
            ("Student Images", "Images_Attendance/")
        ]

        row = 0
        for name, path in config_checks:
            status = "✅" if os.path.exists(path) else "❌"
            color = "green" if os.path.exists(path) else "red"

            ttk.Label(parent, text=f"{name}:").grid(row=row, column=0, sticky=tk.W, pady=2)
            ttk.Label(parent, text=status, foreground=color).grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            row += 1

        # Environment check
        ttk.Label(parent, text="Python Environment:").grid(row=row, column=0, sticky=tk.W, pady=2)
        try:
            import cv2
            import face_recognition
            import pandas
            ttk.Label(parent, text="✅", foreground="green").grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        except ImportError as e:
            ttk.Label(parent, text="❌", foreground="red").grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            ttk.Label(parent, text=f"Missing: {str(e)}", foreground="red").grid(row=row+1, column=0, columnspan=2, sticky=tk.W, pady=2)
            row += 1

        row += 1

    def create_option_buttons(self, parent):
        """Create management option buttons"""
        # Row 1: Core Management
        row1_frame = ttk.Frame(parent)
        row1_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(row1_frame, text="📝 Manage Parent Details",
                  command=self.open_parent_details,
                  style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=10)

        ttk.Button(row1_frame, text="📍 Manage Location Settings",
                  command=self.open_location_details,
                  style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=10)

        # Row 2: Attendance System
        row2_frame = ttk.Frame(parent)
        row2_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(row2_frame, text="🎓 Start Attendance System",
                  command=self.start_attendance_system,
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=10)

        ttk.Button(row2_frame, text="📱 Send Absence Notifications",
                  command=self.send_absence_notifications,
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=10)

        ttk.Button(row2_frame, text="🧪 Test Location Verification",
                  command=self.test_location,
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=10)

        # Row 3: Tools and Utilities
        row3_frame = ttk.Frame(parent)
        row3_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(row3_frame, text="🔧 System Setup & Tools",
                  command=self.open_tools_menu,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=10)

        ttk.Button(row3_frame, text="📊 View Reports",
                  command=self.view_reports,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=10)

        # Row 4: Help and Exit
        row4_frame = ttk.Frame(parent)
        row4_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(row4_frame, text="❓ Help & Documentation",
                  command=self.show_help,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=10)

        ttk.Button(row4_frame, text="🚪 Exit",
                  command=self.root.quit,
                  style="Accent.TButton").pack(side=tk.LEFT, ipadx=20, ipady=10)

    def open_parent_details(self):
        """Open parent details management GUI"""
        try:
            subprocess.Popen([sys.executable, "parent_details_gui.py"])
            messagebox.showinfo("Success", "Parent Details Management GUI opened!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Parent Details GUI: {str(e)}")

    def open_location_details(self):
        """Open location details management GUI"""
        try:
            subprocess.Popen([sys.executable, "location_details_gui.py"])
            messagebox.showinfo("Success", "Location Details Management GUI opened!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Location Details GUI: {str(e)}")

    def start_attendance_system(self):
        """Start the main attendance system"""
        try:
            # Run the original main.py which includes auto-setup and GUI
            subprocess.Popen([sys.executable, "main.py"])
            messagebox.showinfo("Success", "Attendance System starting... Please wait for setup to complete!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Attendance System: {str(e)}")

    def test_location(self):
        """Test location verification"""
        try:
            # Run the location test script
            result = subprocess.run([sys.executable, "-c",
                """
from location_verification import LocationVerifier
v = LocationVerifier()
verified, message, data = v.verify_location()
print(f'Location Test Result: {\"PASSED\" if verified else \"FAILED\"}')
print(f'Details: {message}')
                """],
                capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                messagebox.showinfo("Location Test", result.stdout)
            else:
                messagebox.showerror("Location Test Failed", result.stderr)
        except subprocess.TimeoutExpired:
            messagebox.showerror("Error", "Location test timed out!")
        except Exception as e:
            messagebox.showerror("Error", f"Location test failed: {str(e)}")

    def send_absence_notifications(self):
        """Open absence notification GUI"""
        try:
            subprocess.Popen([sys.executable, "absent_notification_gui.py"])
            messagebox.showinfo("Success", "Absence Notification GUI opened!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Absence Notification GUI: {str(e)}")

    def open_tools_menu(self):
        """Open tools and utilities menu"""
        tools_window = tk.Toplevel(self.root)
        tools_window.title("Tools & Utilities")
        tools_window.geometry("500x400")

        # Tools list
        tools = [
            ("Auto Setup", "tools/auto_setup.py"),
            ("Benchmark Encoding", "tools/benchmark_encoding.py"),
            ("Benchmark Recognition", "tools/benchmark_recognition.py"),
            ("Predict with Classifier", "tools/predict_with_classifier.py"),
            ("Retrain Classifier", "tools/retrain_on_register.py"),
            ("Train Embeddings", "tools/train_embeddings_classifier.py"),
            ("Clean CSV by Images", "clean_csv_by_images.py"),
            ("Generate Gallery", "generate_gallery.py"),
            ("Generate Graphs", "generate_graphs.py"),
            ("Update CSV Headers", "update_csv_headers.py")
        ]

        ttk.Label(tools_window, text="Available Tools & Utilities", font=("Arial", 14, "bold")).pack(pady=10)

        # Create scrollable frame
        canvas = tk.Canvas(tools_window)
        scrollbar = ttk.Scrollbar(tools_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for tool_name, tool_path in tools:
            if os.path.exists(tool_path):
                btn = ttk.Button(scrollable_frame, text=f"▶ {tool_name}",
                               command=lambda p=tool_path: self.run_tool(p))
                btn.pack(fill=tk.X, padx=20, pady=2)
            else:
                lbl = ttk.Label(scrollable_frame, text=f"❌ {tool_name} (Not found)",
                              foreground="red")
                lbl.pack(fill=tk.X, padx=20, pady=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def run_tool(self, tool_path):
        """Run a selected tool"""
        try:
            subprocess.Popen([sys.executable, tool_path])
            messagebox.showinfo("Success", f"Running {os.path.basename(tool_path)}...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run tool: {str(e)}")

    def view_reports(self):
        """View attendance reports"""
        reports_window = tk.Toplevel(self.root)
        reports_window.title("Attendance Reports")
        reports_window.geometry("600x400")

        ttk.Label(reports_window, text="Attendance Reports", font=("Arial", 14, "bold")).pack(pady=10)

        # List attendance files
        attendance_dir = "Attendance_Records"
        if os.path.exists(attendance_dir):
            files = [f for f in os.listdir(attendance_dir) if f.endswith('.csv')]
            if files:
                for file in sorted(files, reverse=True):
                    ttk.Button(reports_window, text=f"📄 {file}",
                             command=lambda f=file: self.open_csv_report(f)).pack(fill=tk.X, padx=20, pady=2)
            else:
                ttk.Label(reports_window, text="No attendance records found.").pack(pady=20)
        else:
            ttk.Label(reports_window, text="Attendance_Records directory not found.").pack(pady=20)

    def open_csv_report(self, filename):
        """Open CSV report (basic view)"""
        try:
            import pandas as pd
            df = pd.read_csv(f"Attendance_Records/{filename}")
            report_window = tk.Toplevel(self.root)
            report_window.title(f"Report: {filename}")
            report_window.geometry("800x600")

            # Create text widget to display CSV content
            text_widget = tk.Text(report_window, wrap=tk.NONE)
            scrollbar_y = ttk.Scrollbar(report_window, orient=tk.VERTICAL, command=text_widget.yview)
            scrollbar_x = ttk.Scrollbar(report_window, orient=tk.HORIZONTAL, command=text_widget.xview)
            text_widget.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

            # Insert CSV content
            text_widget.insert(tk.END, df.to_string(index=False))

            # Pack widgets
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            text_widget.pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open report: {str(e)}")

    def show_help(self):
        """Show help and documentation"""
        help_text = """
Face Recognition Attendance System - Help

MANAGEMENT CENTER:
• Parent Details: Add/edit student parent contact information
• Location Settings: Configure college location and verification rules
• Attendance System: Start the main face recognition attendance GUI
• Location Test: Verify current location against configured settings

TOOLS & UTILITIES:
• Auto Setup: Initialize system and train classifiers
• Benchmark Tools: Test performance of encoding/recognition
• Training Tools: Retrain classifiers with new data
• Data Tools: Clean CSV files, generate galleries, update headers

REPORTS:
• View attendance records from Attendance_Records folder
• CSV files contain daily attendance data

CONFIGURATION:
• parent_config.json: Email/SMS notification settings
• location_config.json: GPS/WiFi verification settings
• parent_contacts.csv: Student parent contact database

For detailed documentation, see SYSTEM_FLOW.md and ADVANCED_FEATURES.md
        """

        help_window = tk.Toplevel(self.root)
        help_window.title("Help & Documentation")
        help_window.geometry("700x500")

        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(help_window, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = ManagementGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()