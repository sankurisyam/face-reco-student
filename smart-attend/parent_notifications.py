# parent_notifications.py
"""
Parent Notification System Module
Sends SMS and Email notifications to parents about student attendance
"""

import smtplib
import json
import os
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParentNotificationManager:
    """Manage parent notifications via SMS and Email"""
    
    def __init__(self, config_file='parent_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.parent_contacts = self.load_parent_contacts()
        
    def load_config(self):
        """Load notification configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration"""
        return {
            "email": {
                "enabled": True,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your_email@gmail.com",
                "sender_password": "your_app_password",  # Use app-specific password for Gmail
                "sender_name": "College Attendance System"
            },
            "sms": {
                "enabled": False,
                "provider": "twilio",  # Options: twilio, aws_sns, fast2sms
                "account_sid": "",
                "auth_token": "",
                "from_number": "+1234567890"
            },
            "notifications": {
                "send_daily_summary": True,
                "send_on_absence": True,
                "send_on_low_attendance": True,
                "low_attendance_threshold": 75,  # Send alert if below 75%
                "send_time": "16:00",  # Time to send daily summary (HH:MM)
                "weekly_report": True,
                "weekly_report_day": "Friday"  # Day of week for weekly report
            },
            "templates": {
                "attendance_marked": "Attendance marked for {student_name} ({roll_no}) on {date} at {time}",
                "absence_alert": "ALERT: {student_name} ({roll_no}) was absent on {date}. Contact them!",
                "low_attendance_alert": "WARNING: {student_name}'s attendance is {attendance_percentage}% (Threshold: {threshold}%)",
                "daily_summary": "Daily Attendance Summary for {student_name}: Present: {present} | Absent: {absent} | Percentage: {percentage}%"
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        logger.info(f"Config saved to {self.config_file}")
    
    def load_parent_contacts(self):
        """Load parent contact information from CSV"""
        contacts_file = 'parent_contacts.csv'
        if os.path.exists(contacts_file):
            try:
                df = pd.read_csv(contacts_file, dtype={'Parent_Mobile1': str, 'Parent_Mobile2': str, 'Parent_Mobile': str})
                # Expected columns: Roll_No, Student_Name, Parent_Email, Parent_Mobile1, Parent_Mobile2
                # Handle backward compatibility with Parent_Mobile
                records = df.to_dict('records')
                for record in records:
                    # Clean phone numbers - ensure they start with +
                    for key in ['Parent_Mobile1', 'Parent_Mobile2', 'Parent_Mobile']:
                        if key in record and pd.notna(record[key]):
                            phone = str(record[key]).strip()
                            if not phone.startswith('+'):
                                phone = '+' + phone
                            record[key] = phone
                    # Handle backward compatibility
                    if 'Parent_Mobile' in record and record['Parent_Mobile'] and not record.get('Parent_Mobile1'):
                        record['Parent_Mobile1'] = record['Parent_Mobile']
                return records
            except Exception as e:
                logger.error(f"Error loading parent contacts: {e}")
        return []
    
    def get_parent_contact(self, roll_no):
        """Get parent contact for a student"""
        for contact in self.parent_contacts:
            if str(contact.get('Roll_No', '')).strip() == str(roll_no).strip():
                return contact
        return None
    
    def send_email(self, recipient_email, subject, body, is_html=False):
        """Send email notification"""
        if not self.config['email']['enabled']:
            logger.warning("Email notifications disabled")
            return False
        
        try:
            sender_email = self.config['email']['sender_email']
            sender_password = self.config['email']['sender_password']
            smtp_server = self.config['email']['smtp_server']
            smtp_port = self.config['email']['smtp_port']
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config['email']['sender_name']} <{sender_email}>"
            msg['To'] = recipient_email
            
            # Attach body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_sms(self, phone_number, message):
        """Send SMS notification"""
        if not self.config['sms']['enabled']:
            logger.warning("SMS notifications disabled")
            return False
        
        provider = self.config['sms']['provider']
        
        try:
            if provider == 'twilio':
                return self._send_sms_twilio(phone_number, message)
            elif provider == 'fast2sms':
                return self._send_sms_fast2sms(phone_number, message)
            elif provider == 'aws_sns':
                return self._send_sms_aws_sns(phone_number, message)
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
        
        return False
    
    def _send_sms_twilio(self, phone_number, message):
        """Send SMS using Twilio"""
        try:
            from twilio.rest import Client
            
            account_sid = self.config['sms']['account_sid']
            auth_token = self.config['sms']['auth_token']
            from_number = self.config['sms']['from_number']
            
            client = Client(account_sid, auth_token)
            msg = client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )
            logger.info(f"SMS sent via Twilio to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Twilio SMS failed: {e}")
            return False
    
    def _send_sms_fast2sms(self, phone_number, message):
        """Send SMS using Fast2SMS"""
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            headers = {
                'authorization': self.config['sms']['auth_token']
            }
            payload = {
                'route': 'q',
                'numbers': phone_number,
                'message': message
            }
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"SMS sent via Fast2SMS to {phone_number}")
                return True
        except Exception as e:
            logger.error(f"Fast2SMS failed: {e}")
        return False
    
    def _send_sms_aws_sns(self, phone_number, message):
        """Send SMS using AWS SNS"""
        try:
            import boto3
            
            client = boto3.client('sns')
            response = client.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            logger.info(f"SMS sent via AWS SNS to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"AWS SNS failed: {e}")
        return False
    
    def notify_attendance_marked(self, student_name, roll_no, date, time):
        """Notify parent that attendance was marked"""
        parent = self.get_parent_contact(roll_no)
        if not parent:
            logger.warning(f"No parent contact found for {roll_no}")
            return False
        
        message = self.config['templates']['attendance_marked'].format(
            student_name=student_name,
            roll_no=roll_no,
            date=date,
            time=time
        )
        
        # Send SMS to both mobile numbers if enabled
        if self.config['sms']['enabled']:
            if parent.get('Parent_Mobile1'):
                self.send_sms(parent['Parent_Mobile1'], message)
            if parent.get('Parent_Mobile2'):
                self.send_sms(parent['Parent_Mobile2'], message)
            # Fallback to Parent_Mobile if the above are not available
            if not parent.get('Parent_Mobile1') and not parent.get('Parent_Mobile2') and parent.get('Parent_Mobile'):
                self.send_sms(parent['Parent_Mobile'], message)
    
    def notify_absence(self, student_name, roll_no, date, note: str = None):
        """Alert parent of student absence. Optional `note` will be appended to the message."""
        parent = self.get_parent_contact(roll_no)
        if not parent:
            return False

        message = self.config['templates']['absence_alert'].format(
            student_name=student_name,
            roll_no=roll_no,
            date=date
        )

        if note:
            # Append note on a new line for email/SMS
            message = f"{message}\n{note}"

        success = True
        if parent.get('Parent_Email'):
            self.send_email(
                parent['Parent_Email'],
                "ALERT: Student Absence",
                message
            )

        # Send SMS to both mobile numbers if enabled
        if self.config['sms']['enabled']:
            if parent.get('Parent_Mobile1'):
                self.send_sms(parent['Parent_Mobile1'], message)
            if parent.get('Parent_Mobile2'):
                self.send_sms(parent['Parent_Mobile2'], message)
            # Fallback to Parent_Mobile if the above are not available
            if not parent.get('Parent_Mobile1') and not parent.get('Parent_Mobile2') and parent.get('Parent_Mobile'):
                self.send_sms(parent['Parent_Mobile'], message)

        return success
    
    def notify_low_attendance(self, student_name, roll_no, attendance_percentage):
        """Alert parent if attendance falls below threshold"""
        threshold = self.config['notifications']['low_attendance_threshold']
        
        if attendance_percentage >= threshold:
            return False
        
        parent = self.get_parent_contact(roll_no)
        if not parent:
            return False
        
        message = self.config['templates']['low_attendance_alert'].format(
            student_name=student_name,
            roll_no=roll_no,
            attendance_percentage=attendance_percentage,
            threshold=threshold
        )
        
        success = True
        if parent.get('Parent_Email'):
            self.send_email(
                parent['Parent_Email'],
                "WARNING: Low Attendance",
                message
            )
        
        # Send SMS to both mobile numbers if enabled
        if self.config['sms']['enabled']:
            if parent.get('Parent_Mobile1'):
                self.send_sms(parent['Parent_Mobile1'], message)
            if parent.get('Parent_Mobile2'):
                self.send_sms(parent['Parent_Mobile2'], message)
            # Fallback to Parent_Mobile if the above are not available
            if not parent.get('Parent_Mobile1') and not parent.get('Parent_Mobile2') and parent.get('Parent_Mobile'):
                self.send_sms(parent['Parent_Mobile'], message)
        
        return success

    def notify_period_summary(self, student_name, roll_no, date, period, status):
        """Send a short period-wise attendance status to the parent."""
        parent = self.get_parent_contact(roll_no)
        if not parent:
            return False

        message = self.config['templates'].get('period_summary',
                                              "Period {period} status for {student_name} ({roll_no}) on {date}: {status}").format(
            student_name=student_name,
            roll_no=roll_no,
            date=date,
            period=period,
            status=status
        )

        # Email (optional) — use plain text
        if parent.get('Parent_Email'):
            self.send_email(parent['Parent_Email'], f"Period {period} Attendance Status", message)

        # SMS (if enabled)
        if self.config['sms']['enabled']:
            if parent.get('Parent_Mobile1'):
                self.send_sms(parent['Parent_Mobile1'], message)
            if parent.get('Parent_Mobile2'):
                self.send_sms(parent['Parent_Mobile2'], message)
            if not parent.get('Parent_Mobile1') and not parent.get('Parent_Mobile2') and parent.get('Parent_Mobile'):
                self.send_sms(parent['Parent_Mobile'], message)

        return True

    def notify_teacher_attendance_missing(self, branch, period, date, details=None):
        """Notify the class teacher that attendance was not taken for a branch/period."""
        # Try to get branch-specific teacher; otherwise use default
        teacher_cfg = None
        if isinstance(self.config.get('teacher_contact'), dict):
            by_branch = self.config.get('teacher_contact', {}).get('by_branch', {})
            teacher_cfg = by_branch.get(branch) or self.config.get('teacher_contact', {}).get('default')

        if not teacher_cfg:
            logger.warning("No teacher contact configured; cannot notify teacher.")
            return False

        message = self.config['templates'].get('teacher_attendance_missing',
                                               "Attendance not taken for {branch} on {date} for Period {period}.").format(
            branch=branch,
            date=date,
            period=period
        )
        if details:
            message += f"\nDetails: {details}"

        # Send email to teacher if available
        if teacher_cfg.get('email'):
            self.send_email(teacher_cfg['email'], f"Attendance Missing — {branch} Period {period}", message)

        # Send SMS to teacher if configured and SMS is enabled
        if self.config['sms']['enabled'] and teacher_cfg.get('mobile'):
            self.send_sms(teacher_cfg['mobile'], message)

        return True
    
    def send_daily_summary(self, student_name, roll_no, present, absent, percentage):
        """Send daily attendance summary to parent"""
        parent = self.get_parent_contact(roll_no)
        if not parent:
            return False
        
        message = self.config['templates']['daily_summary'].format(
            student_name=student_name,
            present=present,
            absent=absent,
            percentage=percentage
        )
        
        html_body = f"""
        <html>
            <body>
                <h2>Daily Attendance Summary</h2>
                <p><b>Student:</b> {student_name} ({roll_no})</p>
                <table border="1" cellpadding="10">
                    <tr>
                        <td><b>Present</b></td>
                        <td>{present}</td>
                    </tr>
                    <tr>
                        <td><b>Absent</b></td>
                        <td>{absent}</td>
                    </tr>
                    <tr>
                        <td><b>Attendance %</b></td>
                        <td>{percentage}%</td>
                    </tr>
                </table>
                <p>Regards,<br>College Attendance System</p>
            </body>
        </html>
        """
        
        if parent.get('Parent_Email'):
            self.send_email(
                parent['Parent_Email'],
                "Daily Attendance Summary",
                html_body,
                is_html=True
            )
        
        return True


def setup_parent_notifications():
    """Interactive setup for parent notifications"""
    print("\n=== Parent Notification Setup ===")
    
    manager = ParentNotificationManager()
    config = manager.config
    
    print("\n--- Email Configuration ---")
    config['email']['enabled'] = input("Enable email notifications? (y/n): ").lower() == 'y'
    if config['email']['enabled']:
        config['email']['sender_email'] = input(f"Sender email [{config['email']['sender_email']}]: ") or config['email']['sender_email']
        config['email']['sender_password'] = input("App-specific password (from Gmail): ")
        config['email']['sender_name'] = input(f"Sender name [{config['email']['sender_name']}]: ") or config['email']['sender_name']
    
    print("\n--- SMS Configuration (Optional) ---")
    config['sms']['enabled'] = input("Enable SMS notifications? (y/n): ").lower() == 'y'
    if config['sms']['enabled']:
        print("Providers: twilio, fast2sms, aws_sns")
        config['sms']['provider'] = input(f"Provider [{config['sms']['provider']}]: ") or config['sms']['provider']
        
        if config['sms']['provider'] == 'twilio':
            config['sms']['account_sid'] = input("Twilio Account SID: ")
            config['sms']['auth_token'] = input("Twilio Auth Token: ")
            config['sms']['from_number'] = input("Twilio phone number: ")
        elif config['sms']['provider'] == 'fast2sms':
            config['sms']['auth_token'] = input("Fast2SMS API Key: ")
    
    print("\n--- Notification Settings ---")
    config['notifications']['send_on_absence'] = input("Send alerts on absence? (y/n): ").lower() == 'y'
    config['notifications']['send_on_low_attendance'] = input("Send alerts on low attendance? (y/n): ").lower() == 'y'
    
    if config['notifications']['send_on_low_attendance']:
        try:
            config['notifications']['low_attendance_threshold'] = int(
                input(f"Low attendance threshold % [{config['notifications']['low_attendance_threshold']}]: ") 
                or config['notifications']['low_attendance_threshold']
            )
        except ValueError:
            pass
    
    manager.save_config()
    print("✓ Notification configuration saved!")
    
    # Create sample parent contacts CSV
    if not os.path.exists('parent_contacts.csv'):
        print("\n=== Creating Parent Contacts File ===")
        sample_data = {
            'Roll_No': ['22FE5A001', '22FE5A002', '22FE5A003'],
            'Student_Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Parent_Email': ['parent1@email.com', 'parent2@email.com', 'parent3@email.com'],
            'Parent_Mobile': ['+919876543210', '+919876543211', '+919876543212']
        }
        df = pd.DataFrame(sample_data)
        df.to_csv('parent_contacts.csv', index=False)
        print("✓ Sample parent_contacts.csv created!")
        print("  Please edit it with actual parent contact information")


if __name__ == "__main__":
    setup_parent_notifications()
