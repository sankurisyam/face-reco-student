# student_profile.py
# Student attendance profile viewer with percentage and color-coded visualization

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
from datetime import datetime
from PIL import Image, ImageTk
try:
    from tkcalendar import DateEntry
except Exception:
    DateEntry = None

class StudentProfileWindow:
    """GUI window to display student attendance profile with percentage and visualization"""
    
    def __init__(self, parent, attendance_folder, branches_list, images_path='Images_Attendance'):
        self.parent = parent
        self.attendance_folder = attendance_folder
        self.branches_list = branches_list
        self.images_path = images_path
        self.periods = ['Period1', 'Period2', 'Period3', 'Period4', 'Period5', 'Period6']
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Student Attendance Profile")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        
        # Search frame
        search_frame = ttk.Frame(self.window)
        search_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="Search Student:").pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        
        # Branch filter
        ttk.Label(search_frame, text="Branch:").pack(side=tk.LEFT, padx=5)
        self.branch_var = tk.StringVar(value=self.branches_list[0] if branches_list else "All")
        branch_combo = ttk.Combobox(search_frame, textvariable=self.branch_var, 
                                     values=["All"] + self.branches_list, width=10, state="readonly")
        branch_combo.pack(side=tk.LEFT, padx=5)
        branch_combo.bind('<<ComboboxSelected>>', lambda e: self._on_search_change(None))
        
        # Date filter (optional)
        ttk.Label(search_frame, text="Date:").pack(side=tk.LEFT, padx=5)
        if DateEntry:
            # Use date pattern matching CSV format (dd/mm/YYYY)
            try:
                self.date_entry = DateEntry(search_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
            except Exception:
                # Fallback to default
                self.date_entry = DateEntry(search_frame, width=12)
            self.date_entry.pack(side=tk.LEFT, padx=5)
            ttk.Button(search_frame, text="Apply Date", command=self._on_date_change).pack(side=tk.LEFT, padx=2)
            ttk.Button(search_frame, text="Clear Date", command=self._clear_date).pack(side=tk.LEFT, padx=2)
        else:
            # Fallback: no tkcalendar available
            self.date_entry = None

        # currently selected date filter (string YYYY-MM-DD) or None
        self.date_filter = None
        
        # Results listbox
        ttk.Label(self.window, text="Select a student:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.student_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        self.student_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.student_listbox.bind('<<ListboxSelect>>', self._on_student_select)
        scrollbar.config(command=self.student_listbox.yview)
        
        # Profile display frame
        ttk.Separator(self.window, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)
        
        profile_frame = ttk.LabelFrame(self.window, text="Student Profile", padding=10)
        profile_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create 2-column layout: photo on left, attendance on right
        left_frame = ttk.Frame(profile_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, expand=False)
        
        ttk.Label(left_frame, text="Student Photo", font=("Arial", 12, "bold")).pack(pady=5)
        # Photo label container with fixed size
        photo_container = tk.Frame(left_frame, bg="#f0f0f0", width=420, height=420)
        photo_container.pack(padx=5, pady=5)
        photo_container.pack_propagate(False)  # Don't shrink
        
        self.photo_label = tk.Label(photo_container, bg="#f0f0f0")
        self.photo_label.pack(expand=True)
        
        right_frame = ttk.Frame(profile_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        ttk.Label(right_frame, text="Attendance Details", font=("Arial", 12, "bold")).pack(pady=5)
        self.profile_text = tk.Text(right_frame, height=20, width=50, font=("Courier", 9))
        self.profile_text.pack(fill=tk.BOTH, expand=True)
        self.profile_text.config(state=tk.DISABLED)
        
        # Store current profile data
        self.current_profile_data = None
        
        # Load all students initially
        self._load_all_students()
    
    def _load_all_students(self):
        """Load all students from attendance CSVs"""
        self.all_students = {}  # {(rollno, name, branch): data}
        
        for branch in self.branches_list:
            csv_file = os.path.join(self.attendance_folder, f'Attendance_{branch}.csv')
            if os.path.exists(csv_file):
                try:
                    df = pd.read_csv(csv_file)
                    for _, row in df.iterrows():
                        rollno = str(row['RollNo']).strip()
                        name = str(row['Name']).strip()
                        key = (rollno, name, branch)
                        if key not in self.all_students:
                            self.all_students[key] = {'branch': branch}
                except Exception as e:
                    print(f"Error loading {csv_file}: {e}")
    
    def _on_search_change(self, event):
        """Update student list based on search"""
        self.student_listbox.delete(0, tk.END)
        
        search_text = self.search_var.get().lower().strip()
        branch_filter = self.branch_var.get()
        
        for (rollno, name, branch) in sorted(self.all_students.keys()):
            # Apply filters
            if branch_filter != "All" and branch != branch_filter:
                continue
            if search_text and search_text not in rollno.lower() and search_text not in name.lower():
                continue
            
            # Add to listbox
            display_text = f"{rollno:15} {name:20} {branch}"
            self.student_listbox.insert(tk.END, display_text)
    
    def _on_student_select(self, event):
        """Display selected student's profile"""
        selection = self.student_listbox.curselection()
        if not selection:
            return
        
        display_text = self.student_listbox.get(selection[0])
        parts = display_text.split()
        rollno = parts[0]
        branch = parts[-1]
        
        # Find full name
        name = None
        for (r, n, b) in self.all_students.keys():
            if r == rollno and b == branch:
                name = n
                break
        
        if name:
            self._show_profile(rollno, name, branch)
    
    def _show_profile(self, rollno, name, branch):
        """Display detailed attendance profile with photo"""
        csv_file = os.path.join(self.attendance_folder, f'Attendance_{branch}.csv')
        
        if not os.path.exists(csv_file):
            messagebox.showerror("Error", f"No attendance file for {branch}")
            return
        
        try:
            df = pd.read_csv(csv_file)
            student_df = df[df['RollNo'] == rollno]
            
            if student_df.empty:
                messagebox.showinfo("Not Found", f"Student {rollno} not found")
                return
            
            # Load and display student photo
            self._load_student_photo(rollno, branch)
            
            # Calculate attendance
            attendance_data = self._calculate_attendance(student_df)
            
            # Store profile data for browser view
            self.current_profile_data = {
                'rollno': rollno,
                'name': name,
                'branch': branch,
                'attendance': attendance_data,
                'student_df': student_df
            }
            
            # Format profile
            profile_text = self._format_profile(rollno, name, branch, attendance_data, student_df)
            
            # Update text widget
            self.profile_text.config(state=tk.NORMAL)
            self.profile_text.delete(1.0, tk.END)
            self.profile_text.insert(1.0, profile_text)
            self.profile_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading profile: {e}")

    def _on_date_change(self):
        """Apply date filter from DateEntry and refresh current profile if loaded"""
        if not getattr(self, 'date_entry', None):
            messagebox.showwarning("Date Filter", "Date picker not available (tkcalendar not installed)")
            return
        try:
            val = self.date_entry.get()
            if val:
                self.date_filter = val
            else:
                self.date_filter = None
            # Refresh current profile view if any
            if self.current_profile_data:
                data = self.current_profile_data
                self._show_profile(data['rollno'], data['name'], data['branch'])
        except Exception as e:
            messagebox.showerror("Date Error", str(e))

    def _clear_date(self):
        """Clear date filter"""
        self.date_filter = None
        if getattr(self, 'date_entry', None):
            try:
                # reset DateEntry to today
                self.date_entry.set_date(datetime.now())
            except Exception:
                pass
        if self.current_profile_data:
            data = self.current_profile_data
            self._show_profile(data['rollno'], data['name'], data['branch'])
    def _load_student_photo(self, rollno, branch):
        """Load and display student photo (4x4 size)"""
        try:
            # Find image in Images_Attendance/[Branch]/ folder
            branch_path = os.path.join(self.images_path, branch)
            
            if not os.path.exists(branch_path):
                self.photo_label.config(text="📁 Branch folder not found", bg="#f0f0f0")
                return
            
            # Look for image by rollno
            found_image = None
            for filename in os.listdir(branch_path):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    if filename.startswith(rollno):
                        found_image = os.path.join(branch_path, filename)
                        break
            
            # Fallback: search by contains
            if not found_image:
                for filename in os.listdir(branch_path):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')) and rollno in filename:
                        found_image = os.path.join(branch_path, filename)
                        break
            
            if not found_image:
                self.photo_label.config(text="📷 No photo found", bg="#f0f0f0")
                return
            
            # Load image and resize to 4x4 (400x400 pixels)
            img = Image.open(found_image)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Create square canvas with white background
            square_img = Image.new('RGB', (400, 400), color='white')
            offset = ((400 - img.width) // 2, (400 - img.height) // 2)
            square_img.paste(img, offset)
            
            # Convert to PhotoImage and display
            self.photo_image = ImageTk.PhotoImage(square_img)
            self.photo_label.config(image=self.photo_image, text='')
            
        except Exception as e:
            self.photo_label.config(text=f"Error: {str(e)[:20]}", bg="#f0f0f0")
    
    def _calculate_attendance(self, student_df):
        """Calculate attendance statistics across ALL dates"""
        stats = {
            'total_periods': 0,
            'attended': 0,
            'absent': 0,
            'attendance_percentage': 0,
            'by_period': {},
            'by_date': {},  # NEW: day-wise breakdown
            'total_days': 0
        }
        
        # Calculate attendance across ALL rows (all dates)
        for period in self.periods:
            if period in student_df.columns:
                # Count across ALL dates for this period
                present_count = (student_df[period].astype(str).str.lower().str.strip() == 'present').sum()
                absent_count = (student_df[period].astype(str).str.lower().str.strip() == 'absent').sum()
                
                # Only count if there are records
                if present_count + absent_count > 0:
                    stats['by_period'][period] = {
                        'present': int(present_count),
                        'absent': int(absent_count),
                        'total': int(present_count + absent_count),
                        'percentage': (present_count / (present_count + absent_count)) * 100
                    }
                    stats['attended'] += present_count
                    stats['total_periods'] += present_count + absent_count
        
        # Calculate day-wise attendance
        if 'Date' in student_df.columns:
            for date_val in student_df['Date'].unique():
                day_row = student_df[student_df['Date'] == date_val]
                day_stats = {'attended': 0, 'absent': 0, 'total': 0, 'details': {}}
                
                for period in self.periods:
                    if period in day_row.columns:
                        status = str(day_row[period].values[0]).strip().lower() if len(day_row[period].values) > 0 else 'n/a'
                        if status in ['present', 'absent']:
                            day_stats['details'][period] = status
                            day_stats['total'] += 1
                            if status == 'present':
                                day_stats['attended'] += 1
                            else:
                                day_stats['absent'] += 1
                
                if day_stats['total'] > 0:
                    day_stats['percentage'] = (day_stats['attended'] / day_stats['total']) * 100
                    stats['by_date'][str(date_val)] = day_stats
                    stats['total_days'] += 1
        
        # Overall percentage across all periods
        if stats['total_periods'] > 0:
            stats['attendance_percentage'] = (stats['attended'] / stats['total_periods']) * 100
        else:
            stats['attendance_percentage'] = 0
        
        return stats
    
    def _format_profile(self, rollno, name, branch, stats, student_df):
        """Format profile display text with colors"""
        lines = []
        lines.append("=" * 85)
        lines.append(f"STUDENT ATTENDANCE PROFILE")
        lines.append("=" * 85)
        lines.append("")
        
        # Basic info
        lines.append(f"Roll Number  : {rollno}")
        lines.append(f"Name         : {name}")
        lines.append(f"Branch       : {branch}")
        lines.append("")
        
        # Attendance summary
        lines.append("-" * 85)
        lines.append("ATTENDANCE SUMMARY")
        lines.append("-" * 85)
        
        total = stats['total_periods']
        attended = stats['attended']
        absent = stats['absent']
        percentage = stats['attendance_percentage']
        
        # Visual percentage bar
        bar_length = 50
        filled = int((percentage / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        lines.append(f"Total Periods : {total}")
        lines.append(f"Attended      : {attended}")
        lines.append(f"Absent        : {absent}")
        lines.append(f"Percentage    : {percentage:.1f}%")
        lines.append(f"Progress      : [{bar}] {percentage:.1f}%")
        lines.append("")
        
        # Attendance status color legend
        lines.append("COLOR CODE:")
        lines.append("  ✓ = PRESENT (Attended)")
        lines.append("  ✗ = ABSENT (Not Attended)")
        lines.append("")
        
        # Period-wise breakdown
        lines.append("-" * 85)
        lines.append("PERIOD-WISE ATTENDANCE")
        lines.append("-" * 85)
        
        for period in self.periods:
            p_stats = stats['by_period'].get(period)
            if p_stats:
                marker = f"{p_stats['present']} present, {p_stats['absent']} absent ({p_stats['percentage']:.1f}%)"
            else:
                marker = "- NOT RECORDED"
            lines.append(f"{period:10} : {marker}")

        lines.append("")

        # If a date filter is set, show selected-date attendance details
        if getattr(self, 'date_filter', None):
            sel = self.date_filter
            day_stats = stats['by_date'].get(sel)
            lines.append("-" * 85)
            lines.append(f"SELECTED DATE: {sel}")
            if day_stats:
                lines.append(f"Day Percentage: {day_stats.get('percentage', 0):.1f}% ({day_stats.get('attended',0)}/{day_stats.get('total',0)})")
                for period in self.periods:
                    if period in day_stats['details']:
                        status = day_stats['details'][period]
                        marker = '✓ PRESENT' if status == 'present' else '✗ ABSENT'
                    else:
                        marker = '- NOT RECORDED'
                    lines.append(f"{period:10} : {marker}")
            else:
                lines.append(f"No attendance records for selected date: {sel}")

        lines.append("-" * 85)
        lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 85)

        return "\n".join(lines)
        
        return "\n".join(lines)


def show_student_profile(parent, attendance_folder, branches_list, images_path='Images_Attendance'):
    """Open student profile window"""
    StudentProfileWindow(parent, attendance_folder, branches_list, images_path)
