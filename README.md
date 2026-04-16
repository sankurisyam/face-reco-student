# Smart Attendance System Using Face Recognition and Location-Based Verification

Short summary: Smart-Attend is a local, Tkinter-based attendance system that uses face recognition (dlib/face_recognition/OpenCV) to record period-wise attendance, notify parents/teachers, and provide management tools for school/college staff.

## Key features implemented so far

- Face-based attendance capture (IP camera or laptop webcam)
- Per-branch attendance and branch-restricted sessions
- Period-wise attendance windows with configurable start/end and grace minutes
- Automatic "mark Absent + notify parents" if attendance not taken by period end
- Teacher notification and teacher-confirmation workflow to suppress alerts
- GUI management center (parent management, location config, period timings editor, teacher-contacts editor)
- Per-branch teacher contact management via GUI (saved to `parent_config.json`)
- SMS / Email notification integration (configurable in `parent_config.json`)
- CSV-backed storage (`Attendance_Records/Attendance_<BRANCH>.csv`), and image gallery in `Images_Attendance/`

## Files & important modules

- `main.py` — Management GUI, period monitoring, notification orchestration
- `attendance.py` — Camera capture, recognition, per-period attendance writing
- `parent_notifications.py` — Email/SMS notification helpers
- `location_verification.py` — GPS/WiFi/IP location checks for attendance
- `period_timings_gui.py` — Admin GUI to edit period start/end and grace minutes
- `teacher_contacts_gui.py` — New GUI to manage default + per-branch teacher contacts (saves to `parent_config.json`)
- `location_details_gui.py` — Configure college location and verification settings
- `parent_details_gui.py` — Manage parent contact list
- `management_center.py` — Higher-level management UI (launch other tools)
- `Images_Attendance/` — Student face images used for recognition
- `Attendance_Records/` — CSV attendance records per branch

## Configuration

- `location_config.json` — college location, verification, and `attendance_time_restrictions` (college_hours, period_timings, grace)
- `parent_config.json` — SMTP/SMS provider settings and notification templates

## How period timing enforcement works

- Attendance is only allowed during `college_hours` and the selected `period` window (both configured in `location_config.json`).
- Each period can have a small `grace_minutes` after its end; attendance after this grace is blocked and shows a warning.
- Admins can edit timings via the Management Center → "Edit Period Timings".

## UI notes

- Start Attendance now requires selecting a `Branch` (e.g., CSE, AIML). Only that branch's students are processed.
- Teachers can "confirm" that they took attendance to prevent auto-alerts/auto-marking.

## Tests

- `test_branch_filter.py` — unit test for branch-based student discovery

## Quick start

1. Install dependencies from `requirements.txt` (use the provided virtual environment recommended):
   pip install -r requirements.txt
2. Configure `location_config.json` and `parent_config.json`.
3. Run the Management Center: `python management_center.py` and open the required tools.

---

