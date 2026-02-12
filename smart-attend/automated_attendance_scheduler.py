#!/usr/bin/env python3
"""
Automated Attendance Scheduler
Automatically runs attendance sessions and sends notifications based on class timings
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import os
import sys
import subprocess
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('attendance_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedAttendanceScheduler:
    """Automated attendance scheduler based on class timings"""

    def __init__(self, config_file='automated_config.json'):
        self.config_file = config_file
        self.config = self.load_config()

        # Class timings (end times) - from config
        self.class_timings = self.config.get('class_timings', {
            'Period1': '10:00',
            'Period2': '11:00',
            'Period3': '12:15',
            'Period4': '13:15',
            'Period5': '15:10',
            'Period6': '16:05',
            'Period7': '17:00',
        })

        self.class_schedule = self.config.get('class_schedule', {})
        self.camera_settings = self.config.get('camera_settings', {'default_source': 'mobile'})
        self.notification_settings = self.config.get('notification_settings', {'enabled': True})
        self.system_settings = self.config.get('system_settings', {'check_interval_seconds': 30})

        self.running = False
        self.scheduler_thread = None

    def load_config(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading config {self.config_file}: {e}")

        logger.info(f"Using default configuration")
        return {}

    def run_attendance_for_period(self, period):
        """Run attendance session for a specific period"""
        try:
            logger.info(f"🚀 Starting automated attendance for {period}")

            # Import here to avoid circular imports
            from attendance import run_attendance

            # Get camera settings from config
            camera_source = self.camera_settings.get('default_source', 'mobile')
            automated = self.system_settings.get('automated_mode', True)

            logger.info(f"Running attendance for {period} with {camera_source} camera in automated mode")

            # Run the attendance session
            # Note: This will run the full attendance session and send notifications
            run_attendance(period, camera_source, automated)

            logger.info(f"✅ Completed automated attendance for {period}")

        except Exception as e:
            logger.error(f"❌ Error running attendance for {period}: {e}")
            # Retry logic
            max_retries = self.system_settings.get('max_retry_attempts', 3)
            # Could implement retry logic here if needed

    def schedule_attendance_sessions(self):
        """Schedule attendance sessions based on class timings"""
        logger.info("📅 Scheduling automated attendance sessions...")

        for period, end_time in self.class_timings.items():
            # Schedule attendance to run at the end of each period
            schedule.every().day.at(end_time).do(self.run_attendance_for_period, period=period)
            logger.info(f"📋 Scheduled {period} attendance for {end_time}")

    def start_scheduler(self):
        """Start the automated attendance scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        logger.info("🎯 Starting Automated Attendance Scheduler")
        logger.info("Class timings:")
        for period, time in self.class_timings.items():
            logger.info(f"  {period}: Runs at {time}")

        self.schedule_attendance_sessions()

        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("✅ Automated Attendance Scheduler started successfully!")

    def stop_scheduler(self):
        """Stop the automated attendance scheduler"""
        logger.info("🛑 Stopping Automated Attendance Scheduler")
        self.running = False
        schedule.clear()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("✅ Scheduler stopped")

    def _run_scheduler(self):
        """Run the scheduler loop"""
        logger.info("⏰ Scheduler loop started")
        check_interval = self.system_settings.get('check_interval_seconds', 30)

        while self.running:
            try:
                schedule.run_pending()
                time.sleep(check_interval)  # Configurable check interval
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait longer on error

        logger.info("⏰ Scheduler loop ended")

    def get_next_runs(self):
        """Get information about next scheduled runs"""
        next_runs = []
        now = datetime.now()

        for period, end_time in self.class_timings.items():
            # Parse the time
            hour, minute = map(int, end_time.split(':'))
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If the time has passed today, schedule for tomorrow
            if scheduled_time <= now:
                scheduled_time += timedelta(days=1)

            next_runs.append({
                'period': period,
                'scheduled_time': scheduled_time,
                'time_string': scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
            })

        # Sort by time
        next_runs.sort(key=lambda x: x['scheduled_time'])

        return next_runs

    def get_status(self):
        """Get scheduler status"""
        status = {
            'running': self.running,
            'class_timings': self.class_timings,
            'next_runs': self.get_next_runs() if self.running else []
        }
        return status

def create_desktop_shortcut():
    """Create a desktop shortcut for easy access"""
    try:
        # Create a batch file for easy starting
        batch_content = '''@echo off
cd /d "%~dp0"
python automated_attendance_scheduler.py
pause
'''

        batch_path = os.path.join(os.path.expanduser("~"), "Desktop", "Start_Automated_Attendance.bat")

        with open(batch_path, 'w') as f:
            f.write(batch_content)

        logger.info(f"✅ Desktop shortcut created: {batch_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create desktop shortcut: {e}")
        return False

def main():
    """Main function for automated attendance scheduler"""
    print("🎓 Automated Attendance Scheduler")
    print("=" * 50)
    print("This system automatically runs attendance sessions")
    print("and sends absence notifications based on class timings.")
    print()

    scheduler = AutomatedAttendanceScheduler()

    print("📅 Class Timings:")
    for period, time in scheduler.class_timings.items():
        print(f"  {period}: Runs at {time}")
    print()

    while True:
        print("Options:")
        print("1. Start Automated Scheduler")
        print("2. Stop Scheduler")
        print("3. Check Status")
        print("4. View Next Runs")
        print("5. Create Desktop Shortcut")
        print("6. Exit")

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == '1':
            if scheduler.running:
                print("❌ Scheduler is already running!")
            else:
                scheduler.start_scheduler()
                print("✅ Scheduler started! Attendance will run automatically.")

        elif choice == '2':
            if not scheduler.running:
                print("❌ Scheduler is not running!")
            else:
                scheduler.stop_scheduler()
                print("✅ Scheduler stopped!")

        elif choice == '3':
            status = scheduler.get_status()
            print(f"Running: {status['running']}")
            if status['running']:
                print(f"Next runs: {len(status['next_runs'])} scheduled")

        elif choice == '4':
            next_runs = scheduler.get_next_runs()
            if next_runs:
                print("📋 Next Scheduled Runs:")
                for run in next_runs[:7]:  # Show next 7 runs
                    print(f"  {run['period']}: {run['time_string']}")
            else:
                print("No runs scheduled")

        elif choice == '5':
            if create_desktop_shortcut():
                print("✅ Desktop shortcut created!")
                print("You can now double-click the shortcut on your desktop")
                print("to start the automated attendance system.")
            else:
                print("❌ Failed to create desktop shortcut")

        elif choice == '6':
            if scheduler.running:
                scheduler.stop_scheduler()
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please try again.")

        print()

if __name__ == "__main__":
    main()