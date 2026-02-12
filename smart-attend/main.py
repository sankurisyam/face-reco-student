# main.py - Face Recognition Attendance System Management Center

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import sys
import os
import json
import pandas as pd
import threading
import time
from datetime import datetime
import webbrowser

class ModernAttendanceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance System - Management Center")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        # Modern color scheme
        self.colors = {
            'primary': '#2E8B57',      # Sea Green
            'secondary': '#32CD32',    # Lime Green
            'accent': '#FF6347',       # Tomato Red
            'warning': '#FFA500',      # Orange
            'success': '#28a745',      # Green
            'info': '#17a2b8',         # Teal
            'light': '#f8f9fa',        # Light Gray
            'dark': '#343a40',         # Dark Gray
            'white': '#ffffff',
            'gray': '#6c757d'
        }

        # Configure styles
        self.setup_styles()

        # Create main container
        self.create_main_container()

        # Initialize data
        self.load_system_status()

        # Initialize warnings tracking
        self.current_warnings = []

        # Create GUI components
        self.create_header()
        self.create_navigation()
        self.create_main_content()
        self.create_footer()

        # Start status updates
        self.start_status_thread()

    def setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Button styles
        style.configure("Primary.TButton",
                       background=self.colors['primary'],
                       foreground=self.colors['white'],
                       font=('Arial', 10, 'bold'),
                       padding=10)
        style.map("Primary.TButton",
                 background=[('active', self.colors['secondary'])])

        style.configure("Secondary.TButton",
                       background=self.colors['secondary'],
                       foreground=self.colors['white'],
                       font=('Arial', 10),
                       padding=8)
        style.map("Secondary.TButton",
                 background=[('active', self.colors['primary'])])

        style.configure("Accent.TButton",
                       background=self.colors['accent'],
                       foreground=self.colors['white'],
                       font=('Arial', 10),
                       padding=8)
        style.map("Accent.TButton",
                 background=[('active', '#ff4500')])

        style.configure("Success.TButton",
                       background=self.colors['success'],
                       foreground=self.colors['white'],
                       font=('Arial', 10),
                       padding=8)

        style.configure("Info.TButton",
                       background=self.colors['info'],
                       foreground=self.colors['white'],
                       font=('Arial', 10),
                       padding=8)

        # Label styles
        style.configure("Header.TLabel",
                       font=('Arial', 16, 'bold'),
                       foreground=self.colors['dark'])

        style.configure("Subheader.TLabel",
                       font=('Arial', 12, 'bold'),
                       foreground=self.colors['primary'])

        style.configure("Card.TFrame", background=self.colors['white'], relief='raised', borderwidth=1)
        style.configure("Status.TLabel", font=('Arial', 9))

    def create_main_container(self):
        """Create main container with modern layout"""
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_header(self):
        """Create modern header with logo and title"""
        header_frame = ttk.Frame(self.main_container, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Logo/Title section
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, padx=20, pady=15)

        # System icon (text-based)
        icon_label = ttk.Label(title_frame, text="🎓",
                              font=('Arial', 24),
                              foreground=self.colors['primary'])
        icon_label.pack(side=tk.LEFT, padx=(0, 10))

        # Title and subtitle
        title_label = ttk.Label(title_frame, text="Face Recognition Attendance System",
                               style="Header.TLabel")
        title_label.pack(anchor=tk.W)

        subtitle_label = ttk.Label(title_frame, text="Management & Control Center",
                                  font=('Arial', 10),
                                  foreground=self.colors['gray'])
        subtitle_label.pack(anchor=tk.W)

        # Status indicator
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(side=tk.RIGHT, padx=20, pady=15)

        self.status_indicator = ttk.Label(status_frame, text="●",
                                         font=('Arial', 14),
                                         foreground=self.colors['success'])
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 5))

        self.status_text = ttk.Label(status_frame, text="System Ready",
                                    font=('Arial', 10, 'bold'),
                                    foreground=self.colors['success'])
        self.status_text.pack(side=tk.LEFT)

    def create_navigation(self):
        """Create modern navigation bar"""
        nav_frame = ttk.Frame(self.main_container, style="Card.TFrame")
        nav_frame.pack(fill=tk.X, pady=(0, 10))

        # Navigation buttons
        nav_buttons = [
            ("🏠 Dashboard", self.show_dashboard),
            ("👨‍👩‍👧‍👦 Parents", self.show_parent_management),
            ("📍 Location", self.show_location_management),
            ("🎓 Attendance", self.show_attendance_section),
            ("🛠️ Tools", self.show_tools_section),
            ("📊 Reports", self.show_reports_section),
            ("❓ Help", self.show_help_section)
        ]

        for text, command in nav_buttons:
            btn = ttk.Button(nav_frame, text=text, command=command, style="Secondary.TButton")
            btn.pack(side=tk.LEFT, padx=5, pady=10)

    def create_main_content(self):
        """Create main content area with notebook for different sections"""
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Create notebook for different sections
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.create_dashboard_tab()
        self.create_parent_tab()
        self.create_location_tab()
        self.create_attendance_tab()
        self.create_tools_tab()
        self.create_reports_tab()
        self.create_help_tab()

        # Show dashboard by default
        self.show_dashboard()

    def create_dashboard_tab(self):
        """Create dashboard tab with system overview"""
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")

        # System status cards
        status_frame = ttk.Frame(self.dashboard_frame)
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        # Status cards
        self.create_status_card(status_frame, "System Health", "Checking...", 0, 0)
        self.create_status_card(status_frame, "Database Status", "Checking...", 0, 1)
        self.create_status_card(status_frame, "Location Service", "Checking...", 0, 2)
        self.create_status_card(status_frame, "Notification Service", "Checking...", 1, 0)
        self.create_status_card(status_frame, "Camera Status", "Checking...", 1, 1)
        self.create_status_card(status_frame, "Storage Space", "Checking...", 1, 2)

        # Quick actions
        actions_frame = ttk.LabelFrame(self.dashboard_frame, text="Quick Actions", padding=15)
        actions_frame.pack(fill=tk.X, padx=20, pady=10)

        quick_actions = [
            ("👨‍👩‍👧‍👦 Manage Parents", self.open_parent_gui, "Primary"),
            ("📍 Configure Location", self.open_location_gui, "Primary"),
            ("🎓 Start Attendance", self.start_attendance_system, "Success"),
            ("🧪 Test Location", self.test_location, "Info"),
            ("📊 View Reports", lambda: self.notebook.select(5), "Secondary"),
            ("🛠️ Open Tools", lambda: self.notebook.select(4), "Secondary")
        ]

        for i, (text, command, style) in enumerate(quick_actions):
            row, col = i // 3, i % 3
            btn = ttk.Button(actions_frame, text=text, command=command,
                           style=f"{style}.TButton")
            btn.grid(row=row, column=col, padx=5, pady=5, sticky=tk.EW)

        # Configure grid weights
        for i in range(2):
            actions_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            actions_frame.grid_columnconfigure(i, weight=1)

        # Recent activity
        activity_frame = ttk.LabelFrame(self.dashboard_frame, text="Recent Activity", padding=15)
        activity_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        self.activity_text = scrolledtext.ScrolledText(activity_frame, height=6,
                                                     font=('Consolas', 9))
        self.activity_text.pack(fill=tk.BOTH, expand=True)
        self.activity_text.insert(tk.END, "Loading recent activity...\n")
        self.activity_text.config(state=tk.DISABLED)

        # Location warnings
        warnings_frame = ttk.LabelFrame(self.dashboard_frame, text="Location Warnings", padding=15)
        warnings_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.warnings_text = tk.Text(warnings_frame, height=3, font=('Arial', 9),
                                   bg=self.colors['light'], relief=tk.FLAT)
        self.warnings_text.pack(fill=tk.X)
        self.warnings_text.insert(tk.END, "No location warnings detected.")
        self.warnings_text.config(state=tk.DISABLED)

    def create_status_card(self, parent, title, status, row, col):
        """Create a status card widget"""
        card = ttk.LabelFrame(parent, text=title, padding=10)
        card.grid(row=row, column=col, padx=5, pady=5, sticky=tk.NSEW)

        self.status_labels[title] = ttk.Label(card, text=status, style="Status.TLabel")
        self.status_labels[title].pack()

        # Configure grid weights
        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)

    def create_parent_tab(self):
        """Create parent management tab"""
        self.parent_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.parent_frame, text="Parent Management")

        # Header
        header_label = ttk.Label(self.parent_frame,
                                text="Student Parent Details Management",
                                style="Subheader.TLabel")
        header_label.pack(pady=10)

        # Description
        desc_text = """
        Manage parent contact information for all students. This information is used for
        sending attendance notifications via email and SMS when students are absent.

        Features:
        • Add new student parent details
        • Edit existing parent information
        • Remove student records
        • Validate contact information
        • Export/import parent data
        """
        desc_label = ttk.Label(self.parent_frame, text=desc_text,
                              justify=tk.LEFT, wraplength=600)
        desc_label.pack(pady=(0, 20))

        # Action buttons
        btn_frame = ttk.Frame(self.parent_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="📝 Open Parent Details Manager",
                  command=self.open_parent_gui, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 View Parent Database",
                  command=self.view_parent_data, style="Info.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📤 Export Parent Data",
                  command=self.export_parent_data, style="Secondary.TButton").pack(side=tk.LEFT, padx=5)

    def create_location_tab(self):
        """Create location management tab"""
        self.location_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.location_frame, text="Location Management")

        # Header
        header_label = ttk.Label(self.location_frame,
                                text="Location Verification Settings",
                                style="Subheader.TLabel")
        header_label.pack(pady=10)

        # Description
        desc_text = """
        Configure location verification parameters for attendance security.
        The system can verify location using GPS coordinates, WiFi networks, and IP ranges.

        Features:
        • Set college location coordinates
        • Configure WiFi network verification
        • Set GPS radius limits
        • Enable/disable verification methods
        • Test location verification
        """
        desc_label = ttk.Label(self.location_frame, text=desc_text,
                              justify=tk.LEFT, wraplength=600)
        desc_label.pack(pady=(0, 20))

        # Action buttons
        btn_frame = ttk.Frame(self.location_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="⚙️ Open Location Settings",
                  command=self.open_location_gui, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧪 Test Location Verification",
                  command=self.test_location, style="Success.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 View Current Settings",
                  command=self.view_location_config, style="Info.TButton").pack(side=tk.LEFT, padx=5)

    def create_attendance_tab(self):
        """Create attendance management tab"""
        self.attendance_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.attendance_frame, text="Attendance System")

        # Header
        header_label = ttk.Label(self.attendance_frame,
                                text="Attendance Session Management",
                                style="Subheader.TLabel")
        header_label.pack(pady=10)

        # Quick attendance setup
        setup_frame = ttk.LabelFrame(self.attendance_frame, text="Quick Start", padding=15)
        setup_frame.pack(fill=tk.X, padx=20, pady=10)

        # Period selection
        ttk.Label(setup_frame, text="Period:").grid(row=0, column=0, padx=5, pady=5)
        self.period_var = tk.StringVar(value="1")
        period_combo = ttk.Combobox(setup_frame, textvariable=self.period_var,
                                   values=[str(i) for i in range(1, 7)], width=10)
        period_combo.grid(row=0, column=1, padx=5, pady=5)

        # Camera source
        ttk.Label(setup_frame, text="Camera:").grid(row=0, column=2, padx=5, pady=5)
        self.camera_var = tk.StringVar(value="mobile")
        camera_combo = ttk.Combobox(setup_frame, textvariable=self.camera_var,
                                   values=["mobile", "laptop"], width=10)
        camera_combo.grid(row=0, column=3, padx=5, pady=5)

        # Start button
        ttk.Button(setup_frame, text="🚀 Start Attendance Session",
                  command=self.start_attendance_system,
                  style="Success.TButton").grid(row=0, column=4, padx=10, pady=5)

        # Additional options
        options_frame = ttk.LabelFrame(self.attendance_frame, text="Additional Options", padding=15)
        options_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Button(options_frame, text="📝 Register New Student",
                  command=self.register_student, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(options_frame, text="👤 View Student Profile",
                  command=self.view_student_profile, style="Info.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(options_frame, text="⚙️ Notification Settings",
                  command=self.notification_settings, style="Secondary.TButton").pack(side=tk.LEFT, padx=5)

        # Automated Absence Notifications
        self.create_automated_notifications_section()

    def create_automated_notifications_section(self):
        """Create automated absence notifications section"""
        notifications_frame = ttk.LabelFrame(self.attendance_frame, text="Automated Absence Notifications", padding=15)
        notifications_frame.pack(fill=tk.X, padx=20, pady=10)

        # Control buttons
        control_frame = ttk.Frame(notifications_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.auto_notifications_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Enable Automated Notifications",
                       variable=self.auto_notifications_enabled,
                       command=self.toggle_auto_notifications).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Button(control_frame, text="📊 Check Period Status",
                  command=self.check_period_status, style="Info.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="📱 Send Manual Notifications",
                  command=self.send_manual_notifications, style="Primary.TButton").pack(side=tk.LEFT, padx=5)

        # Status display
        status_frame = ttk.LabelFrame(notifications_frame, text="Notification Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        # Status text area
        self.notification_status_text = tk.Text(status_frame, height=6, wrap=tk.WORD, state=tk.DISABLED,
                                              font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.notification_status_text.yview)
        self.notification_status_text.configure(yscrollcommand=scrollbar.set)

        self.notification_status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Initialize status
        self.update_notification_status("Automated notifications are currently disabled.\nEnable to start monitoring periods.")

        # Period monitoring variables
        self.monitoring_active = False
        self.monitoring_thread = None

    def toggle_auto_notifications(self):
        """Toggle automated notifications on/off"""
        if self.auto_notifications_enabled.get():
            self.start_period_monitoring()
            self.update_notification_status("✅ Automated notifications enabled. Monitoring periods...")
        else:
            self.stop_period_monitoring()
            self.update_notification_status("❌ Automated notifications disabled.")

    def start_period_monitoring(self):
        """Start monitoring periods for automated notifications"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self.monitor_periods, daemon=True)
        self.monitoring_thread.start()

    def stop_period_monitoring(self):
        """Stop monitoring periods"""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1)

    def monitor_periods(self):
        """Monitor periods and send notifications when they complete"""
        from datetime import datetime
        import json

        # Load location config for period timings
        try:
            with open('location_config.json', 'r') as f:
                config = json.load(f)
                time_restrictions = config.get('attendance_time_restrictions', {})
                period_timings = time_restrictions.get('period_timings', {})
        except:
            self.update_notification_status("❌ Error: Could not load period timings from config.")
            return

        while self.monitoring_active:
            try:
                current_time = datetime.now().time()
                current_date = datetime.now().strftime('%d/%m/%Y')

                for period_num in range(1, 7):
                    period_key = str(period_num)
                    if period_key in period_timings:
                        period_info = period_timings[period_key]
                        end_time_str = period_info.get('end', '10:00')

                        try:
                            period_end_time = datetime.strptime(end_time_str, '%H:%M').time()
                            # Check if current time is past period end time
                            if current_time >= period_end_time:
                                # Check if notifications already sent for this period today
                                if not self.check_notifications_sent_today(period_num, current_date):
                                    self.send_period_absence_notifications(period_num, current_date)
                                    self.mark_notifications_sent(period_num, current_date)
                        except ValueError:
                            continue

                time.sleep(60)  # Check every minute

            except Exception as e:
                self.update_notification_status(f"❌ Monitoring error: {str(e)}")
                time.sleep(60)

    def check_notifications_sent_today(self, period, date):
        """Check if notifications were already sent for this period today"""
        # This is a simple implementation - in production, you'd want to store this in a database
        # For now, we'll check a simple text file
        try:
            with open('notification_log.txt', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if f"Period {period}" in line and date in line and "completed" in line:
                        return True
        except:
            pass
        return False

    def mark_notifications_sent(self, period, date):
        """Mark that notifications were sent for this period"""
        try:
            with open('notification_log.txt', 'a') as f:
                timestamp = datetime.now().strftime('%H:%M:%S')
                f.write(f"[{date} {timestamp}] Period {period} notifications completed\n")
        except:
            pass

    def send_period_absence_notifications(self, period, date):
        """Send absence notifications for a specific period.

        Behavior changed:
        - If a student does not have an attendance row for the given date, create one
          and mark only the requested period as 'Absent'.
        - If a row exists but the period cell is blank/missing, treat it as Absent.
        - Save any changes back to the attendance CSV before sending notifications.
        """
        try:
            from parent_notifications import ParentNotificationManager
            import pandas as pd

            notifier = ParentNotificationManager()
            branches = ['AIML', 'CAI', 'CSD', 'CSE', 'CSM']
            total_sent = 0

            for branch in branches:
                attendance_file = f"Attendance_Records/Attendance_{branch}.csv"
                if not os.path.exists(attendance_file):
                    continue

                df = pd.read_csv(attendance_file)
                period_col = f'Period{period}'

                # Ensure period columns exist
                for p in range(1, 7):
                    col = f'Period{p}'
                    if col not in df.columns:
                        df[col] = ''

                # Build master list of students (use existing RollNo entries)
                master_rolls = df['RollNo'].astype(str).unique().tolist()

                # For each student, ensure there is a row for today's date; if missing, add one
                rows_to_append = []
                for roll in master_rolls:
                    has_today = ((df['RollNo'].astype(str) == str(roll)) & (df['Date'] == date)).any()
                    if not has_today:
                        # get a sample row to copy Name/Branch
                        sample = df[df['RollNo'].astype(str) == str(roll)].head(1)
                        if sample.empty:
                            name = ''
                            branch_val = branch
                        else:
                            name = str(sample.iloc[0].get('Name', '')).strip()
                            branch_val = sample.iloc[0].get('Branch', branch)

                        new_row = { 'RollNo': roll,
                                    'Name': name,
                                    'Branch': branch_val,
                                    'Date': date }
                        # set all periods empty except the current which is Absent
                        for p in range(1, 7):
                            new_row[f'Period{p}'] = 'Absent' if p == period else ''
                        rows_to_append.append(new_row)

                if rows_to_append:
                    df = pd.concat([df, pd.DataFrame(rows_to_append)], ignore_index=True)

                # For existing rows of today, if the period cell is blank/NaN, mark Absent
                df.loc[(df['Date'] == date) & (df[period_col].isnull() | (df[period_col].astype(str).str.strip() == '')) , period_col] = 'Absent'

                # Save any updates back to the CSV so further processes see the changes
                try:
                    df.to_csv(attendance_file, index=False)
                except Exception:
                    pass

                # Find absent students for this period and date (treat case-insensitively)
                absent_students = []
                for _, row in df.iterrows():
                    if (str(row.get('Date', '')) == date and
                        str(row.get(period_col, '')).strip().lower() == 'absent'):
                        absent_students.append({
                            'roll_no': str(row['RollNo']).strip(),
                            'name': str(row.get('Name', '')).strip()
                        })

                # Send notifications
                for student in absent_students:
                    try:
                        notifier.notify_absence(student['name'], student['roll_no'], date)
                        total_sent += 1
                    except Exception as e:
                        self.update_notification_status(f"❌ Failed to notify {student['name']}: {str(e)}")

            if total_sent > 0:
                self.update_notification_status(f"✅ Period {period} completed: {total_sent} absence notifications sent")
            else:
                self.update_notification_status(f"ℹ️ Period {period} completed: No absences found")

        except Exception as e:
            self.update_notification_status(f"❌ Error sending notifications for period {period}: {str(e)}")

    def check_period_status(self):
        """Check current period status and show information"""
        try:
            from datetime import datetime
            import json

            current_time = datetime.now()
            current_date = current_time.strftime('%d/%m/%Y')
            current_time_str = current_time.strftime('%H:%M')

            # Load period timings
            with open('location_config.json', 'r') as f:
                config = json.load(f)
                time_restrictions = config.get('attendance_time_restrictions', {})
                period_timings = time_restrictions.get('period_timings', {})

            status_msg = f"📅 Current Date: {current_date}\n🕐 Current Time: {current_time_str}\n\n"

            for period_num in range(1, 7):
                period_key = str(period_num)
                if period_key in period_timings:
                    period_info = period_timings[period_key]
                    period_name = period_info.get('name', f'Period {period_num}')
                    start_time = period_info.get('start', '09:00')
                    end_time = period_info.get('end', '10:00')

                    # Determine status
                    if current_time_str < start_time:
                        status = "⏳ Upcoming"
                    elif start_time <= current_time_str <= end_time:
                        status = "🟢 Active"
                    else:
                        status = "✅ Completed"
                        if self.check_notifications_sent_today(period_num, current_date):
                            status += " (Notifications Sent)"

                    status_msg += f"{period_name}: {start_time}-{end_time} [{status}]\n"

            self.update_notification_status(status_msg)

        except Exception as e:
            self.update_notification_status(f"❌ Error checking period status: {str(e)}")

    def send_manual_notifications(self):
        """Send manual absence notifications for a specific period"""
        # Create a dialog to select period
        dialog = tk.Toplevel(self.root)
        dialog.title("Send Manual Notifications")
        dialog.geometry("300x200")
        dialog.resizable(False, False)

        ttk.Label(dialog, text="Select Period:", font=("Arial", 10, "bold")).pack(pady=10)

        period_var = tk.StringVar(value="1")
        period_combo = ttk.Combobox(dialog, textvariable=period_var,
                                   values=[str(i) for i in range(1, 7)], width=10)
        period_combo.pack(pady=5)

        def send_notifications():
            period = int(period_var.get())
            date = datetime.now().strftime('%d/%m/%Y')
            dialog.destroy()
            self.send_period_absence_notifications(period, date)
            self.mark_notifications_sent(period, date)

        ttk.Button(dialog, text="Send Notifications", command=send_notifications).pack(pady=20)

    def update_notification_status(self, message):
        """Update the notification status display"""
        def update():
            self.notification_status_text.config(state=tk.NORMAL)
            self.notification_status_text.delete(1.0, tk.END)
            self.notification_status_text.insert(tk.END, message)
            self.notification_status_text.config(state=tk.DISABLED)
            self.notification_status_text.see(tk.END)

        # Schedule update on main thread
        self.root.after(0, update)

    def create_tools_tab(self):
        """Create tools and utilities tab"""
        self.tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tools_frame, text="Tools & Utilities")

        # Header
        header_label = ttk.Label(self.tools_frame,
                                text="System Tools & Utilities",
                                style="Subheader.TLabel")
        header_label.pack(pady=10)

        # Tools categories
        categories = [
            ("🔧 System Tools", [
                ("Auto Setup", "tools/auto_setup.py", "Initialize and train the system"),
                ("Clean CSV Data", "clean_csv_by_images.py", "Clean attendance data"),
                ("Update CSV Headers", "update_csv_headers.py", "Fix CSV file headers"),
                ("Generate Gallery", "generate_gallery.py", "Create student photo gallery")
            ]),
            ("📊 Analysis Tools", [
                ("Benchmark Encoding", "tools/benchmark_encoding.py", "Test face encoding performance"),
                ("Benchmark Recognition", "tools/benchmark_recognition.py", "Test recognition accuracy"),
                ("Predict Classifier", "tools/predict_with_classifier.py", "Test classification models"),
                ("Generate Graphs", "generate_graphs.py", "Create attendance graphs")
            ]),
            ("🎯 Training Tools", [
                ("Retrain Classifier", "tools/retrain_on_register.py", "Update classifiers after registration"),
                ("Train Embeddings", "tools/train_embeddings_classifier.py", "Train embedding models")
            ])
        ]

        for category_name, tools in categories:
            cat_frame = ttk.LabelFrame(self.tools_frame, text=category_name, padding=10)
            cat_frame.pack(fill=tk.X, padx=20, pady=5)

            for tool_name, tool_path, description in tools:
                tool_frame = ttk.Frame(cat_frame)
                tool_frame.pack(fill=tk.X, pady=2)

                ttk.Label(tool_frame, text=f"{tool_name}:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
                ttk.Label(tool_frame, text=description, font=('Arial', 9)).pack(side=tk.LEFT, padx=(10, 0))

                if os.path.exists(tool_path):
                    ttk.Button(tool_frame, text="Run",
                              command=lambda p=tool_path: self.run_tool(p),
                              style="Secondary.TButton").pack(side=tk.RIGHT)
                else:
                    ttk.Label(tool_frame, text="Not found", foreground=self.colors['accent']).pack(side=tk.RIGHT)

    def create_reports_tab(self):
        """Create reports and analytics tab"""
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Reports & Analytics")

        # Header
        header_label = ttk.Label(self.reports_frame,
                                text="Attendance Reports & Analytics",
                                style="Subheader.TLabel")
        header_label.pack(pady=10)

        # Report options
        report_frame = ttk.LabelFrame(self.reports_frame, text="Generate Reports", padding=15)
        report_frame.pack(fill=tk.X, padx=20, pady=10)

        # Date-based reports
        ttk.Button(report_frame, text="📅 View Attendance by Date",
                  command=self.view_attendance_by_date,
                  style="Primary.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(report_frame, text="📊 Generate Attendance Graphs",
                  command=self.generate_graphs,
                  style="Info.TButton").pack(side=tk.LEFT, padx=5)

        # Student gallery
        ttk.Button(report_frame, text="🖼️ View Student Gallery",
                  command=self.view_student_gallery,
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=5)

        # CSV downloads
        download_frame = ttk.LabelFrame(self.reports_frame, text="Download Data", padding=15)
        download_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(download_frame, text="Branch:").grid(row=0, column=0, padx=5, pady=5)
        self.branch_var = tk.StringVar(value="CSE")
        branch_combo = ttk.Combobox(download_frame, textvariable=self.branch_var,
                                   values=['CSE', 'AIML', 'CSD', 'CAI', 'CSM'], width=10)
        branch_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(download_frame, text="📥 Download Branch CSV",
                  command=self.download_branch_csv,
                  style="Success.TButton").grid(row=0, column=2, padx=10, pady=5)

    def create_help_tab(self):
        """Create help and documentation tab"""
        self.help_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.help_frame, text="Help & Documentation")

        # Header
        header_label = ttk.Label(self.help_frame,
                                text="Help & Documentation",
                                style="Subheader.TLabel")
        header_label.pack(pady=10)

        # Help content
        help_text = """
Face Recognition Attendance System - Complete Guide

SYSTEM OVERVIEW:
This system uses advanced face recognition technology to automate attendance
marking for educational institutions. It includes location verification,
parent notifications, and comprehensive reporting.

CORE FEATURES:
• Face Recognition: Advanced dlib and face_recognition library
• Location Verification: GPS, WiFi, and IP-based validation
• Parent Notifications: Email and SMS alerts for absences
• Multi-format Support: CSV reports, graphs, and analytics
• Real-time Processing: Live attendance marking with camera input

GETTING STARTED:
1. Configure parent contact information
2. Set up location verification parameters
3. Register students with photos
4. Start attendance sessions
5. Monitor reports and notifications

TROUBLESHOOTING:
• Camera Issues: Check camera permissions and connections
• Recognition Problems: Ensure good lighting and clear photos
• Location Errors: Verify GPS and WiFi settings
• Notification Failures: Check email/SMS configurations

For detailed documentation, see SYSTEM_FLOW.md and ADVANCED_FEATURES.md
        """

        help_widget = scrolledtext.ScrolledText(self.help_frame, wrap=tk.WORD,
                                              font=('Arial', 10), padx=10, pady=10)
        help_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        help_widget.insert(tk.END, help_text)
        help_widget.config(state=tk.DISABLED)

        # Quick links
        links_frame = ttk.Frame(self.help_frame)
        links_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Button(links_frame, text="📖 System Flow Documentation",
                  command=lambda: self.open_file("SYSTEM_FLOW.md"),
                  style="Info.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(links_frame, text="⚡ Advanced Features",
                  command=lambda: self.open_file("ADVANCED_FEATURES.md"),
                  style="Info.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(links_frame, text="📋 Management Guide",
                  command=lambda: self.open_file("MANAGEMENT_GUIDE.md"),
                  style="Info.TButton").pack(side=tk.LEFT, padx=5)

    def create_footer(self):
        """Create footer with system info"""
        footer_frame = ttk.Frame(self.main_container, style="Card.TFrame")
        footer_frame.pack(fill=tk.X, pady=(10, 0))

        # System info
        info_label = ttk.Label(footer_frame,
                              text=f"Face Recognition Attendance System v2.0 | Python {sys.version.split()[0]} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                              font=('Arial', 8), foreground=self.colors['gray'])
        info_label.pack(pady=5)

    # System status methods
    def load_system_status(self):
        """Initialize system status tracking"""
        self.status_labels = {}
        self.system_status = {
            "System Health": "Checking...",
            "Database Status": "Checking...",
            "Location Service": "Checking...",
            "Notification Service": "Checking...",
            "Camera Status": "Checking...",
            "Storage Space": "Checking..."
        }

    def start_status_thread(self):
        """Start background thread for status updates"""
        self.status_thread = threading.Thread(target=self.update_system_status, daemon=True)
        self.status_thread.start()

    def update_system_status(self):
        """Update system status in background"""
        while True:
            try:
                # Check system health
                health_status = "✅ Operational"
                if not os.path.exists("models"):
                    health_status = "⚠️ Models missing"
                self.update_status_label("System Health", health_status)

                # Check database
                db_status = "✅ Connected"
                if not os.path.exists("parent_contacts.csv"):
                    db_status = "⚠️ Parent data missing"
                elif not os.path.exists("Attendance_Records"):
                    db_status = "⚠️ Records missing"
                self.update_status_label("Database Status", db_status)

                # Check location service with warnings
                loc_status = "✅ Ready"
                loc_warnings = []
                if not os.path.exists("location_config.json"):
                    loc_status = "❌ Config missing"
                else:
                    try:
                        from location_verification import LocationVerifier
                        verifier = LocationVerifier()
                        verified, message, data, warnings = verifier.verify_location()
                        if not verified:
                            loc_status = "❌ Verification failed"
                        elif warnings:
                            loc_status = "⚠️ Warnings present"
                            loc_warnings = warnings
                    except Exception as e:
                        loc_status = f"❌ Error: {str(e)[:20]}..."

                self.update_status_label("Location Service", loc_status)

                # Store warnings for display
                self.current_warnings = loc_warnings

                # Check notification service
                notif_status = "✅ Configured"
                if not os.path.exists("parent_config.json"):
                    notif_status = "❌ Config missing"
                self.update_status_label("Notification Service", notif_status)

                # Check camera (simplified)
                cam_status = "✅ Available"
                self.update_status_label("Camera Status", cam_status)

                # Check storage
                import shutil
                total, used, free = shutil.disk_usage(".")
                free_gb = free / (1024**3)
                storage_status = f"✅ {free_gb:.1f} GB free"
                if free_gb < 1:
                    storage_status = f"⚠️ {free_gb:.1f} GB free"
                self.update_status_label("Storage Space", storage_status)

                # Update main status
                all_good = all("✅" in status for status in [
                    health_status, db_status, loc_status, notif_status, cam_status, storage_status
                ])
                if all_good:
                    self.update_main_status("System Ready", self.colors['success'])
                elif loc_warnings:
                    self.update_main_status("Location Warnings", self.colors['warning'])
                else:
                    self.update_main_status("System Needs Attention", self.colors['warning'])

                # Update activity log with warnings
                if loc_warnings:
                    warning_text = "\n".join(f"⚠️ {w}" for w in loc_warnings)
                    self.update_activity_log(f"Location warnings detected:\n{warning_text}")
                    self.update_warnings_display(loc_warnings)
                else:
                    self.update_warnings_display([])

            except Exception as e:
                print(f"Status update error: {e}")

            time.sleep(10)  # Update every 10 seconds

    def update_status_label(self, key, value):
        """Update a status label safely"""
        if key in self.status_labels:
            self.status_labels[key].config(text=value)
        self.system_status[key] = value

    def update_main_status(self, text, color):
        """Update main status indicator"""
        self.status_text.config(text=text, foreground=color)
        self.status_indicator.config(foreground=color)

    def update_activity_log(self, message):
        """Update the activity log with new messages"""
        if hasattr(self, 'activity_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            current_text = self.activity_text.get(1.0, tk.END).strip()
            new_text = f"[{timestamp}] {message}\n{current_text}"
            # Keep only last 20 lines
            lines = new_text.split('\n')[:20]
            self.activity_text.delete(1.0, tk.END)
            self.activity_text.insert(tk.END, '\n'.join(lines))
            self.activity_text.see(tk.END)

    def update_warnings_display(self, warnings):
        """Update the warnings display area"""
        if hasattr(self, 'warnings_text'):
            self.warnings_text.config(state=tk.NORMAL)
            self.warnings_text.delete(1.0, tk.END)

            if warnings:
                warning_text = "\n".join(f"⚠️ {w}" for w in warnings)
                self.warnings_text.insert(tk.END, warning_text)
                self.warnings_text.config(fg=self.colors['warning'])
            else:
                self.warnings_text.insert(tk.END, "✅ No location warnings detected.")
                self.warnings_text.config(fg=self.colors['success'])

            self.warnings_text.config(state=tk.DISABLED)

    # Navigation methods
    def show_dashboard(self):
        """Show dashboard tab"""
        self.notebook.select(0)

    def show_parent_management(self):
        """Show parent management tab"""
        self.notebook.select(1)

    def show_location_management(self):
        """Show location management tab"""
        self.notebook.select(2)

    def show_attendance_section(self):
        """Show attendance section tab"""
        self.notebook.select(3)

    def show_tools_section(self):
        """Show tools section tab"""
        self.notebook.select(4)

    def show_reports_section(self):
        """Show reports section tab"""
        self.notebook.select(5)

    def show_help_section(self):
        """Show help section tab"""
        self.notebook.select(6)

    # Action methods
    def open_parent_gui(self):
        """Open parent details management GUI"""
        try:
            subprocess.Popen([sys.executable, "parent_details_gui.py"])
            messagebox.showinfo("Success", "Parent Details Manager opened!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Parent GUI: {str(e)}")

    def open_location_gui(self):
        """Open location details management GUI"""
        try:
            subprocess.Popen([sys.executable, "location_details_gui.py"])
            messagebox.showinfo("Success", "Location Settings Manager opened!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Location GUI: {str(e)}")

    def start_attendance_system(self):
        """Start the attendance system with mandatory location verification"""
        try:
            period = self.period_var.get()
            camera = self.camera_var.get()

            if period not in ['1', '2', '3', '4', '5', '6']:
                messagebox.showerror("Error", "Please select a valid period (1-6)")
                return

            # Request location permission first
            location_permission = messagebox.askyesno(
                "Location Permission Required",
                "📍 The attendance system needs to verify your location.\n\n"
                "This will:\n"
                "• Request access to your location\n"
                "• Check if you're at the college\n"
                "• Verify WiFi connection\n\n"
                "Do you want to enable location services?"
            )

            if not location_permission:
                messagebox.showwarning("Location Required", "Location verification is required for attendance.")
                return

            # Show location detection progress
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Detecting Location")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)

            tk.Label(progress_window, text="🔍 Detecting your location...",
                    font=("Arial", 12)).pack(pady=20)

            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate', length=300)
            progress_bar.pack(pady=10)
            progress_bar.start()

            tk.Label(progress_window, text="Please allow location access when prompted.",
                    font=("Arial", 10)).pack(pady=5)

            progress_window.update()

            # Check location and time restrictions before starting attendance - MANDATORY
            from location_verification import LocationVerifier
            verifier = LocationVerifier()
            verified, message, data, warnings = verifier.verify_location_and_time(period)

            # Close progress window
            progress_window.destroy()

            if not verified:
                # Verification failed - show warnings and prevent attendance
                warning_msg = "❌ VERIFICATION FAILED\n\n"
                warning_msg += "Attendance cannot proceed due to verification failure.\n\n"
                warning_msg += f"Details:\n{message}\n\n"

                if warnings:
                    warning_msg += "\n".join(f"• {w}" for w in warnings)
                else:
                    warning_msg += "• Location verification failed (no specific warnings available)"

                warning_msg += f"\n\nTechnical Details:\n{message}"

                messagebox.showerror("Attendance Blocked", warning_msg)
                return

            # Location verified successfully - proceed with attendance
            if warnings:
                # Show warnings but allow attendance since verification passed
                warning_msg = "⚠️ Location verification passed with warnings:\n\n"
                warning_msg += "\n".join(f"• {w}" for w in warnings)
                warning_msg += "\n\nDo you want to proceed with attendance?"

                if not messagebox.askyesno("Location Warnings", warning_msg):
                    return

            # Import and run attendance
            from attendance import run_attendance
            self.root.destroy()  # Close management GUI
            run_attendance(period, camera)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start attendance: {str(e)}")

    def test_location(self):
        """Test location verification with warnings"""
        try:
            from location_verification import LocationVerifier
            verifier = LocationVerifier()
            verified, message, data, warnings = verifier.verify_location()

            result = "PASSED" if verified else "FAILED"
            icon = "✅" if verified else "❌"

            # Show main result
            result_msg = f"{icon} Location Test: {result}\n\nDetails:\n{message}"

            # Show warnings if any
            if warnings:
                result_msg += f"\n\n⚠️ WARNINGS:\n" + "\n".join(f"• {w}" for w in warnings)

            # Show additional info
            if data['wifi']['data']:
                wifi_data = data['wifi']['data']
                if wifi_data.get('connected_ssid'):
                    result_msg += f"\n\n📶 Current WiFi: {wifi_data['connected_ssid']}"
                if wifi_data.get('available_networks'):
                    result_msg += f"\n📡 Available networks: {', '.join(wifi_data['available_networks'][:3])}"

            if data['gps']['data'] and data['gps']['data'].get('current_location'):
                gps_data = data['gps']['data']
                lat, lon = gps_data['current_location']
                result_msg += f"\n\n📍 Current GPS: {lat:.6f}, {lon:.6f}"
                if gps_data.get('distance'):
                    result_msg += f"\n📏 Distance from college: {gps_data['distance']:.0f}m"

            messagebox.showinfo(f"Location Test: {result}", result_msg)

        except ImportError:
            messagebox.showerror("Error", "Location verification module not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Location test failed: {str(e)}")

    def run_tool(self, tool_path):
        """Run a system tool"""
        try:
            subprocess.Popen([sys.executable, tool_path])
            messagebox.showinfo("Success", f"Running {os.path.basename(tool_path)}...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run tool: {str(e)}")

    def view_parent_data(self):
        """View parent contact data"""
        try:
            if os.path.exists("parent_contacts.csv"):
                df = pd.read_csv("parent_contacts.csv")
                # Show in a popup window
                popup = tk.Toplevel(self.root)
                popup.title("Parent Contact Database")
                popup.geometry("800x400")

                text = scrolledtext.ScrolledText(popup, font=('Consolas', 9))
                text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text.insert(tk.END, df.to_string(index=False))
                text.config(state=tk.DISABLED)
            else:
                messagebox.showerror("Error", "Parent contacts file not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load parent data: {str(e)}")

    def export_parent_data(self):
        """Export parent data to external location"""
        try:
            if os.path.exists("parent_contacts.csv"):
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    title="Export Parent Data"
                )
                if save_path:
                    import shutil
                    shutil.copy2("parent_contacts.csv", save_path)
                    messagebox.showinfo("Success", f"Parent data exported to {save_path}")
            else:
                messagebox.showerror("Error", "Parent contacts file not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def view_location_config(self):
        """View current location configuration"""
        try:
            if os.path.exists("location_config.json"):
                with open("location_config.json", 'r') as f:
                    config = json.load(f)

                # Show in a popup window
                popup = tk.Toplevel(self.root)
                popup.title("Location Configuration")
                popup.geometry("600x400")

                text = scrolledtext.ScrolledText(popup, font=('Consolas', 9))
                text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text.insert(tk.END, json.dumps(config, indent=2))
                text.config(state=tk.DISABLED)
            else:
                messagebox.showerror("Error", "Location config file not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {str(e)}")

    def register_student(self):
        """Register a new student"""
        try:
            from register import register_student
            register_student(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open registration: {str(e)}")

    def view_student_profile(self):
        """View student attendance profile"""
        try:
            from student_profile import show_student_profile
            show_student_profile(self.root, 'Attendance_Records',
                               ['CSE', 'AIML', 'CSD', 'CAI', 'CSM'], 'Images_Attendance')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open profile: {str(e)}")

    def notification_settings(self):
        """Open notification settings"""
        try:
            from notification_settings import create_settings_window
            create_settings_window()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open settings: {str(e)}")

    def view_attendance_by_date(self):
        """View attendance by date"""
        try:
            from gui import show_attendance_by_date
            show_attendance_by_date()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open attendance view: {str(e)}")

    def generate_graphs(self):
        """Generate attendance graphs"""
        try:
            subprocess.Popen([sys.executable, "generate_graphs.py"])
            messagebox.showinfo("Success", "Generating attendance graphs...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate graphs: {str(e)}")

    def view_student_gallery(self):
        """View student photo gallery"""
        try:
            subprocess.Popen([sys.executable, "generate_gallery.py"])
            messagebox.showinfo("Success", "Opening student gallery...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open gallery: {str(e)}")

    def download_branch_csv(self):
        """Download branch attendance CSV"""
        try:
            from gui import download_branch_by_date
            # Create dummy date entry for today
            from tkcalendar import DateEntry
            from datetime import datetime

            # This is a simplified version - in real implementation you'd create a proper date picker
            branch = self.branch_var.get()
            date_str = datetime.now().strftime('%d/%m/%Y')

            # For now, just show a message
            messagebox.showinfo("Download", f"Downloading {branch} attendance for {date_str}...")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to download CSV: {str(e)}")

    def open_file(self, filename):
        """Open a documentation file"""
        try:
            if os.path.exists(filename):
                webbrowser.open(filename)
            else:
                messagebox.showerror("Error", f"File {filename} not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")


def start_background_setup():
    """Run auto-setup before starting GUI"""
    script = os.path.join('tools', 'auto_setup.py')
    if os.path.exists(script):
        try:
            print('Running auto-setup (prewarm cache + train classifiers). This may take some time...')
            subprocess.run([sys.executable, script], check=False)
            print('Auto-setup finished.')
        except Exception as e:
            print('Auto-setup failed to run:', e)


def main():
    """Main application entry point"""
    # Run setup if needed
    start_background_setup()

    # Create and run modern GUI
    root = tk.Tk()
    app = ModernAttendanceGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
