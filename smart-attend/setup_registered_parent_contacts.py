#!/usr/bin/env python3
"""
Quick Parent Contact Setup for Registered Students
Automatically creates parent contacts for all currently registered students
"""

import os
import pandas as pd

def get_registered_students():
    """Get all currently registered students"""
    students = []
    images_path = 'Images_Attendance'

    if not os.path.exists(images_path):
        return students

    for branch_folder in os.listdir(images_path):
        branch_dir = os.path.join(images_path, branch_folder)
        if os.path.isdir(branch_dir) and not branch_folder.startswith('_'):
            for img_file in os.listdir(branch_dir):
                name_no_ext = os.path.splitext(img_file)[0]
                parts = name_no_ext.split('_')
                if len(parts) == 3:
                    roll, name, branch = parts
                    students.append({
                        'Roll_No': roll.upper(),
                        'Student_Name': name.upper(),
                        'Branch': branch.upper()
                    })

    return students

def create_parent_contacts():
    """Create parent contacts for all registered students"""
    students = get_registered_students()

    if not students:
        print("No registered students found!")
        return

    print(f"Found {len(students)} registered students:")
    for student in students:
        print(f"  - {student['Roll_No']}: {student['Student_Name']} ({student['Branch']})")

    # Create parent contacts with sample data
    parent_contacts = []
    base_mobile = 9876543210

    for i, student in enumerate(students):
        # Generate sample parent contact info
        roll_no = student['Roll_No']
        student_name = student['Student_Name']

        # Create email from student name
        email_name = student_name.lower().replace(' ', '.').replace('.', '')
        parent_email = f"parent.{email_name}@email.com"

        # Generate mobile numbers
        mobile1 = f"+91{base_mobile + i*2}"
        mobile2 = f"+91{base_mobile + i*2 + 1}"

        parent_contacts.append({
            'Roll_No': roll_no,
            'Student_Name': student_name,
            'Parent_Email': parent_email,
            'Parent_Mobile1': mobile1,
            'Parent_Mobile2': mobile2
        })

    # Save to CSV
    df = pd.DataFrame(parent_contacts)
    df.to_csv('parent_contacts.csv', index=False)

    print(f"\n✓ Created parent contacts for {len(parent_contacts)} students!")
    print("Parent contact file: parent_contacts.csv")
    print("\nSample parent contacts created:")
    for contact in parent_contacts[:3]:  # Show first 3
        print(f"  {contact['Roll_No']}: {contact['Student_Name']}")
        print(f"    Email: {contact['Parent_Email']}")
        print(f"    Mobile: {contact['Parent_Mobile1']}, {contact['Parent_Mobile2']}")

    if len(parent_contacts) > 3:
        print(f"  ... and {len(parent_contacts) - 3} more")

    print("\n⚠️  IMPORTANT: Replace the sample email addresses and phone numbers")
    print("   with real parent contact information before using the system!")

def main():
    print("Parent Contact Setup for Registered Students")
    print("=" * 50)

    confirm = input("This will create parent contacts for all registered students. Continue? (y/n): ").strip().lower()

    if confirm == 'y':
        create_parent_contacts()
        print("\nNext steps:")
        print("1. Edit parent_contacts.csv with real parent information")
        print("2. Test notifications: python -c \"from parent_notifications import ParentNotificationManager; n = ParentNotificationManager(); n.notify_absence('STUDENT_NAME', 'ROLL_NO', '02/02/2026')\"")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()