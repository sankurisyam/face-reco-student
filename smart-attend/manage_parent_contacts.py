#!/usr/bin/env python3
"""
Parent Contact Management Script
Allows manual editing of parent contact information
"""

import pandas as pd
import os
import sys

def load_parent_contacts():
    """Load parent contacts from CSV"""
    contacts_file = 'parent_contacts.csv'
    if os.path.exists(contacts_file):
        try:
            df = pd.read_csv(contacts_file, dtype={'Parent_Mobile1': str, 'Parent_Mobile2': str})
            return df
        except Exception as e:
            print(f"Error loading contacts: {e}")
            return pd.DataFrame()
    else:
        print("No parent_contacts.csv found. Creating new one...")
        return pd.DataFrame(columns=['Roll_No', 'Student_Name', 'Parent_Email', 'Parent_Mobile1', 'Parent_Mobile2'])

def save_parent_contacts(df):
    """Save parent contacts to CSV"""
    try:
        df.to_csv('parent_contacts.csv', index=False)
        print("✓ Parent contacts saved successfully!")
        return True
    except Exception as e:
        print(f"Error saving contacts: {e}")
        return False

def add_or_update_contact(df, roll_no, student_name, parent_email, parent_mobile1, parent_mobile2):
    """Add or update a parent contact"""
    # Remove existing entry for this roll no
    df = df[df['Roll_No'] != roll_no]

    # Add new entry
    new_row = {
        'Roll_No': roll_no.upper(),
        'Student_Name': student_name.upper(),
        'Parent_Email': parent_email.strip() if parent_email else '',
        'Parent_Mobile1': parent_mobile1.strip() if parent_mobile1 else '',
        'Parent_Mobile2': parent_mobile2.strip() if parent_mobile2 else ''
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df

def display_contacts(df):
    """Display all parent contacts"""
    if df.empty:
        print("No parent contacts found.")
        return

    print("\n" + "="*80)
    print("CURRENT PARENT CONTACTS")
    print("="*80)
    for idx, row in df.iterrows():
        print(f"\n{idx+1}. Roll No: {row['Roll_No']}")
        print(f"   Student: {row['Student_Name']}")
        print(f"   Email: {row['Parent_Email']}")
        print(f"   Mobile 1: {row['Parent_Mobile1']}")
        print(f"   Mobile 2: {row['Parent_Mobile2']}")
    print("="*80)

def interactive_mode():
    """Interactive mode for managing parent contacts"""
    df = load_parent_contacts()

    while True:
        print("\n" + "="*50)
        print("PARENT CONTACT MANAGEMENT")
        print("="*50)
        print("1. View all contacts")
        print("2. Add/Update contact")
        print("3. Delete contact")
        print("4. Save and exit")
        print("5. Exit without saving")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == '1':
            display_contacts(df)

        elif choice == '2':
            print("\nADD/UPDATE PARENT CONTACT")
            roll_no = input("Roll No: ").strip()
            if not roll_no:
                print("Roll No is required!")
                continue

            student_name = input("Student Name: ").strip()
            parent_email = input("Parent Email: ").strip()
            parent_mobile1 = input("Parent Mobile 1 (with country code, e.g., +91XXXXXXXXXX): ").strip()
            parent_mobile2 = input("Parent Mobile 2 (optional): ").strip()

            df = add_or_update_contact(df, roll_no, student_name, parent_email, parent_mobile1, parent_mobile2)
            print("✓ Contact added/updated!")

        elif choice == '3':
            roll_no = input("Enter Roll No to delete: ").strip().upper()
            if roll_no in df['Roll_No'].values:
                df = df[df['Roll_No'] != roll_no]
                print(f"✓ Contact for {roll_no} deleted!")
            else:
                print(f"Contact for {roll_no} not found.")

        elif choice == '4':
            if save_parent_contacts(df):
                print("Changes saved. Exiting...")
                break
            else:
                print("Failed to save. Try again.")

        elif choice == '5':
            confirm = input("Exit without saving? (y/n): ").strip().lower()
            if confirm == 'y':
                print("Exiting without saving...")
                break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Parent Contact Management Script")
        print("Usage: python manage_parent_contacts.py")
        print("Run interactively to manage parent contact information.")
    else:
        interactive_mode()