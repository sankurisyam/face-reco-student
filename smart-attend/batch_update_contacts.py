#!/usr/bin/env python3
"""
Batch Update Parent Contacts
Update parent contacts from a CSV file or individual entries
"""

import pandas as pd
import os
import sys

def update_from_csv(update_file):
    """Update parent contacts from another CSV file"""
    if not os.path.exists(update_file):
        print(f"Error: {update_file} not found!")
        return False

    try:
        # Load existing contacts
        existing_file = 'parent_contacts.csv'
        if os.path.exists(existing_file):
            existing_df = pd.read_csv(existing_file, dtype={'Parent_Mobile1': str, 'Parent_Mobile2': str})
        else:
            existing_df = pd.DataFrame(columns=['Roll_No', 'Student_Name', 'Parent_Email', 'Parent_Mobile1', 'Parent_Mobile2'])

        # Load update data
        update_df = pd.read_csv(update_file, dtype={'Parent_Mobile1': str, 'Parent_Mobile2': str})

        print(f"Loaded {len(update_df)} contacts to update...")

        # Update existing contacts
        updated_count = 0
        for idx, row in update_df.iterrows():
            roll_no = str(row['Roll_No']).strip().upper()

            # Remove existing entry
            existing_df = existing_df[existing_df['Roll_No'] != roll_no]

            # Add updated entry
            new_row = {
                'Roll_No': roll_no,
                'Student_Name': str(row['Student_Name']).strip().upper(),
                'Parent_Email': str(row.get('Parent_Email', '')).strip(),
                'Parent_Mobile1': str(row.get('Parent_Mobile1', '')).strip(),
                'Parent_Mobile2': str(row.get('Parent_Mobile2', '')).strip()
            }
            existing_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
            updated_count += 1

        # Save updated contacts
        existing_df.to_csv(existing_file, index=False)
        print(f"✓ Successfully updated {updated_count} parent contacts!")
        return True

    except Exception as e:
        print(f"Error updating contacts: {e}")
        return False

def create_sample_update_file():
    """Create a sample update CSV file"""
    sample_data = {
        'Roll_No': ['22FE5A001', '22FE5A002', '22FE5A003'],
        'Student_Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'Parent_Email': ['father.john@email.com', 'mother.jane@email.com', 'parent.bob@email.com'],
        'Parent_Mobile1': ['+919876543210', '+919876543212', '+919876543214'],
        'Parent_Mobile2': ['+919876543211', '+919876543213', '']
    }

    df = pd.DataFrame(sample_data)
    df.to_csv('parent_contacts_update_sample.csv', index=False)
    print("✓ Created sample update file: parent_contacts_update_sample.csv")
    print("Edit this file with your actual parent contact information.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Batch Parent Contact Update Tool")
        print("Usage:")
        print("  python batch_update_contacts.py <update_csv_file>")
        print("  python batch_update_contacts.py --sample")
        print("")
        print("Examples:")
        print("  python batch_update_contacts.py my_contacts.csv")
        print("  python batch_update_contacts.py --sample")
        sys.exit(1)

    if sys.argv[1] == "--sample":
        create_sample_update_file()
    else:
        update_file = sys.argv[1]
        if update_from_csv(update_file):
            print("Batch update completed successfully!")
        else:
            print("Batch update failed!")
            sys.exit(1)