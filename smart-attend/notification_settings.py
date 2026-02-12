#!/usr/bin/env python3
"""
Automatic Notification Settings Manager
Control automatic per-period notifications
"""

import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

class NotificationSettingsManager:
    def __init__(self, config_file='parent_config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return self.get_default_config()

    def get_default_config(self):
        """Return default configuration"""
        return {
            "notifications": {
                "auto_send_per_period": True,
                "auto_send_delay_seconds": 30
            }
        }

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")
            return False

    def update_auto_send_settings(self, enabled, delay_seconds):
        """Update automatic sending settings"""
        if 'notifications' not in self.config:
            self.config['notifications'] = {}

        self.config['notifications']['auto_send_per_period'] = enabled
        self.config['notifications']['auto_send_delay_seconds'] = delay_seconds

        return self.save_config()

def create_settings_window():
    """Create the settings window"""
    settings_window = tk.Toplevel()
    settings_window.title("Automatic Notification Settings")
    settings_window.geometry("400x300")

    manager = NotificationSettingsManager()

    # Title
    title_label = tk.Label(settings_window, text="Automatic Per-Period Notifications",
                          font=("Arial", 14, "bold"))
    title_label.pack(pady=20)

    # Auto-send checkbox
    auto_send_var = tk.BooleanVar(value=manager.config.get('notifications', {}).get('auto_send_per_period', True))

    auto_send_check = tk.Checkbutton(settings_window,
                                    text="Enable automatic notifications after each period",
                                    variable=auto_send_var,
                                    font=("Arial", 10))
    auto_send_check.pack(pady=10)

    # Delay setting
    delay_frame = tk.Frame(settings_window)
    delay_frame.pack(pady=10)

    delay_label = tk.Label(delay_frame, text="Delay before auto-advance (seconds):",
                          font=("Arial", 10))
    delay_label.pack()

    current_delay = manager.config.get('notifications', {}).get('auto_send_delay_seconds', 30)
    delay_var = tk.StringVar(value=str(current_delay))

    delay_entry = tk.Entry(delay_frame, textvariable=delay_var, width=10, font=("Arial", 10))
    delay_entry.pack(pady=5)

    # Info text
    info_text = """
How it works:
• After each period ends, absence notifications are sent automatically
• System waits for the specified delay, then shows period completion
• Parents receive immediate alerts when students are absent
• Enable this for hands-free operation during class sessions
    """

    info_label = tk.Label(settings_window, text=info_text, font=("Arial", 9),
                         justify="left", fg="blue")
    info_label.pack(pady=10)

    def save_settings():
        try:
            delay_seconds = int(delay_var.get())
            if delay_seconds < 5:
                messagebox.showwarning("Invalid Delay", "Delay must be at least 5 seconds")
                return
            if delay_seconds > 300:
                messagebox.showwarning("Invalid Delay", "Delay cannot exceed 5 minutes (300 seconds)")
                return

            if manager.update_auto_send_settings(auto_send_var.get(), delay_seconds):
                messagebox.showinfo("Success", "Settings saved successfully!")
                settings_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to save settings")

        except ValueError:
            messagebox.showerror("Invalid Input", "Delay must be a valid number")

    # Save button
    save_button = tk.Button(settings_window, text="Save Settings",
                           command=save_settings, bg="green", fg="white",
                           font=("Arial", 11, "bold"), width=15)
    save_button.pack(pady=20)

    # Current status
    status_text = f"Current Status: {'Enabled' if auto_send_var.get() else 'Disabled'} ({current_delay}s delay)"
    status_label = tk.Label(settings_window, text=status_text, font=("Arial", 9), fg="green")
    status_label.pack()

def main():
    """Main function for command line usage"""
    print("Automatic Notification Settings Manager")
    print("=" * 50)

    manager = NotificationSettingsManager()

    current_auto = manager.config.get('notifications', {}).get('auto_send_per_period', True)
    current_delay = manager.config.get('notifications', {}).get('auto_send_delay_seconds', 30)

    print(f"Current auto-send: {'Enabled' if current_auto else 'Disabled'}")
    print(f"Current delay: {current_delay} seconds")

    print("\nOptions:")
    print("1. Enable automatic notifications")
    print("2. Disable automatic notifications")
    print("3. Change delay time")
    print("4. Exit")

    while True:
        choice = input("\nEnter choice (1-4): ").strip()

        if choice == '1':
            manager.update_auto_send_settings(True, current_delay)
            print("✅ Automatic notifications enabled")
            current_auto = True

        elif choice == '2':
            manager.update_auto_send_settings(False, current_delay)
            print("❌ Automatic notifications disabled")
            current_auto = False

        elif choice == '3':
            try:
                new_delay = int(input("Enter delay in seconds (5-300): "))
                if 5 <= new_delay <= 300:
                    manager.update_auto_send_settings(current_auto, new_delay)
                    print(f"✅ Delay updated to {new_delay} seconds")
                    current_delay = new_delay
                else:
                    print("❌ Delay must be between 5-300 seconds")
            except ValueError:
                print("❌ Invalid number")

        elif choice == '4':
            print("Goodbye!")
            break

        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        # GUI mode
        root = tk.Tk()
        root.withdraw()  # Hide main window
        create_settings_window()
        root.mainloop()
    else:
        # Command line mode
        main()