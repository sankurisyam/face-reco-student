#!/usr/bin/env python3
"""
Setup script for Location Verification and Parent Notifications
Run this once to configure the system
"""

import os
import sys
import json

def setup_system():
    """Main setup function"""
    print("\n" + "="*60)
    print("College Attendance System - Advanced Features Setup")
    print("="*60)
    
    while True:
        print("\nWhat would you like to set up?")
        print("1. Location Verification (GPS/WiFi geofencing)")
        print("2. Parent Notifications (Email/SMS)")
        print("3. Both features")
        print("4. View current configuration")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            setup_location()
        elif choice == '2':
            setup_notifications()
        elif choice == '3':
            setup_location()
            setup_notifications()
        elif choice == '4':
            view_configurations()
        elif choice == '5':
            print("\nSetup complete! The system is ready to use.")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

def setup_location():
    """Setup location verification"""
    print("\n" + "-"*60)
    print("LOCATION VERIFICATION SETUP")
    print("-"*60)
    
    try:
        from location_verification import setup_college_location
        setup_college_location()
    except ImportError:
        print("Error: location_verification module not found")
        print("Make sure location_verification.py is in the project directory")

def setup_notifications():
    """Setup parent notifications"""
    print("\n" + "-"*60)
    print("PARENT NOTIFICATION SETUP")
    print("-"*60)
    
    try:
        from parent_notifications import setup_parent_notifications
        setup_parent_notifications()
    except ImportError:
        print("Error: parent_notifications module not found")
        print("Make sure parent_notifications.py is in the project directory")

def view_configurations():
    """View current configurations"""
    print("\n" + "-"*60)
    print("CURRENT CONFIGURATIONS")
    print("-"*60)
    
    # Check location config
    if os.path.exists('location_config.json'):
        print("\n📍 Location Configuration (location_config.json):")
        with open('location_config.json', 'r') as f:
            config = json.load(f)
            print(f"  College: {config.get('college_name', 'Not set')}")
            print(f"  Latitude: {config.get('latitude', 'Not set')}")
            print(f"  Longitude: {config.get('longitude', 'Not set')}")
            print(f"  Radius: {config.get('radius_meters', 'Not set')}m")
            print(f"  GPS Enabled: {config.get('enable_gps', False)}")
            print(f"  WiFi Enabled: {config.get('enable_wifi', False)}")
            print(f"  WiFi Networks: {config.get('wifi_ssids', [])}")
    else:
        print("\n📍 Location Configuration: Not yet configured")
    
    # Check parent config
    if os.path.exists('parent_config.json'):
        print("\n📧 Parent Notification Configuration (parent_config.json):")
        with open('parent_config.json', 'r') as f:
            config = json.load(f)
            print(f"  Email Enabled: {config['email'].get('enabled', False)}")
            if config['email'].get('enabled'):
                print(f"  Sender: {config['email'].get('sender_name', 'Not set')}")
                print(f"  SMTP Server: {config['email'].get('smtp_server', 'Not set')}")
            print(f"  SMS Enabled: {config['sms'].get('enabled', False)}")
            if config['sms'].get('enabled'):
                print(f"  SMS Provider: {config['sms'].get('provider', 'Not set')}")
            print(f"  Send on Absence: {config['notifications'].get('send_on_absence', False)}")
            print(f"  Low Attendance Threshold: {config['notifications'].get('low_attendance_threshold', 0)}%")
    else:
        print("\n📧 Parent Notification Configuration: Not yet configured")
    
    # Check parent contacts
    if os.path.exists('parent_contacts.csv'):
        import pandas as pd
        df = pd.read_csv('parent_contacts.csv')
        print(f"\n📋 Parent Contacts (parent_contacts.csv):")
        print(f"  Total students configured: {len(df)}")
        print("\n  Sample entries:")
        print(df.head(3).to_string(index=False))
        if len(df) > 3:
            print(f"  ... and {len(df) - 3} more")
    else:
        print("\n📋 Parent Contacts: Not yet configured")

if __name__ == "__main__":
    try:
        setup_system()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)
