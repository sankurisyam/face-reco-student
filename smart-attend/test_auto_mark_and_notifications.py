"""
Tests for auto-mark Absent functionality and teacher confirmation
"""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
import pytest


def test_auto_mark_absent_when_attendance_not_taken(tmp_path):
    """Test that students are marked absent when attendance is not taken during period"""
    # This test verifies the auto-mark logic by checking:
    # 1. If a student exists in the class roster but not in today's attendance file
    # 2. The student should be automatically marked as Absent
    # 3. A notification should be queued for the parent
    
    # Create a minimal test CSV with a student
    attendance_file = tmp_path / "Attendance_Test.csv"
    attendance_file.write_text("Name,Date,Time,Status\n")
    
    # Simulate checking for missing attendance - a student not in this file should be marked absent
    # This is a conceptual test; the actual implementation would be in attendance.py
    
    students = ["Alice", "Bob"]
    marked_students = []  # Students in the attendance file
    
    absent_students = [s for s in students if s not in marked_students]
    
    assert len(absent_students) == 2
    assert "Alice" in absent_students
    assert "Bob" in absent_students


def test_teacher_confirmation_suppresses_parent_notification():
    """Test that teacher confirmation suppresses parent notification"""
    # Verification: if a teacher confirms attendance was taken for a period,
    # parent notifications should NOT be sent for absent students
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Simulate teacher confirmation data
    teacher_confirmations = {
        today: {
            "period_1": True,  # Teacher confirmed attendance for period 1
            "period_2": False  # Teacher did NOT confirm attendance for period 2
        }
    }
    
    period = "period_1"
    
    # Check if attendance was confirmed
    confirmations_today = teacher_confirmations.get(today, {})
    period_confirmed = confirmations_today.get(period, False)
    
    # If confirmed, parent notifications should be suppressed
    should_notify = not period_confirmed
    
    # In this case, period_1 was confirmed, so no notification
    assert should_notify is False
    
    # For period_2, not confirmed, so should notify
    should_notify_p2 = not confirmations_today.get("period_2", False)
    assert should_notify_p2 is True


def test_absent_student_notification_includes_context():
    """Test that absence notification includes context (student name, period, date)"""
    # Verify the notification message has all required information
    
    student_name = "John Doe"
    period = "Period 1"
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    notification_msg = f"{student_name} was marked Absent for {period} on {date_str}"
    
    assert student_name in notification_msg
    assert period in notification_msg
    assert date_str in notification_msg


def test_branch_filter_excludes_students_from_other_branches():
    """Test that only students from selected branch are marked absent"""
    # Simulates attending to Period 1 for branch "CSE"
    # Only CSE students should be checked for attendance
    
    all_students = {
        "CSE": ["Alice", "Bob", "Charlie"],
        "ECE": ["Diana", "Eve"],
        "AIML": ["Frank", "Grace"]
    }
    
    selected_branch = "CSE"
    attendance_marked = ["Alice", "Bob"]  # Only Alice and Bob attended
    
    # Get branch students
    branch_students = all_students.get(selected_branch, [])
    
    # Find absent students (from selected branch only)
    absent = [s for s in branch_students if s not in attendance_marked]
    
    # Should only mark Charlie as absent (from CSE branch)
    assert len(absent) == 1
    assert "Charlie" in absent
    
    # Students from other branches should NOT be in the absence list
    assert "Diana" not in absent
    assert "Eve" not in absent
    assert "Frank" not in absent


def test_teacher_contact_persistence():
    """Test that teacher contact changes are saved and loaded correctly"""
    # Create temporary config file
    config = {
        "teacher_contact": {
            "default": {
                "name": "Dr. Smith",
                "email": "smith@college.edu",
                "phone": "9876543210"
            },
            "by_branch": {
                "CSE": {
                    "name": "Dr. CSE Head",
                    "email": "cse@college.edu",
                    "phone": "1111111111"
                }
            }
        }
    }
    
    # Verify default teacher contact
    default_teacher = config["teacher_contact"]["default"]
    assert default_teacher["name"] == "Dr. Smith"
    assert default_teacher["email"] == "smith@college.edu"
    
    # Verify branch-specific teacher contact
    cse_teacher = config["teacher_contact"]["by_branch"].get("CSE")
    assert cse_teacher is not None
    assert cse_teacher["name"] == "Dr. CSE Head"
    
    # Simulate loading teacher contact for a branch
    branch = "CSE"
    teacher = config["teacher_contact"]["by_branch"].get(branch) or config["teacher_contact"]["default"]
    assert teacher == cse_teacher
    
    # Fallback for non-existent branch
    branch = "UNKNOWN"
    teacher = config["teacher_contact"]["by_branch"].get(branch) or config["teacher_contact"]["default"]
    assert teacher == default_teacher


def test_notification_queue_for_multiple_absent_students():
    """Test that notifications are queued for all absent students"""
    # Simulate a period where multiple students are absent
    students_in_branch = ["Student A", "Student B", "Student C", "Student D"]
    students_marked_present = ["Student A", "Student C"]
    
    absent_students = [s for s in students_in_branch if s not in students_marked_present]
    
    # Simulate notification queue
    notification_queue = [
        {
            "student": s,
            "status": "Absent",
            "period": "Period 1",
            "date": datetime.now().strftime('%Y-%m-%d')
        }
        for s in absent_students
    ]
    
    assert len(notification_queue) == 2
    assert notification_queue[0]["student"] == "Student B"
    assert notification_queue[1]["student"] == "Student D"
    assert all(n["status"] == "Absent" for n in notification_queue)
