import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import re
import requests

class LocationDetailsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Location Details Management - Face Recognition Attendance System")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Set theme
        style = ttk.Style()
        style.theme_use('clam')

        # Colors
        self.primary_color = "#2E8B57"
        self.secondary_color = "#32CD32"
        self.accent_color = "#FF6347"

        self.config_file = "location_config.json"
        self.load_config()

        self.create_widgets()
        self.load_existing_config()

    def load_config(self):
        """Load location configuration from JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                # Load from sample config
                sample_file = "location_config_sample.json"
                if os.path.exists(sample_file):
                    with open(sample_file, 'r') as f:
                        self.config = json.load(f)
                else:
                    # Default configuration
                    self.config = {
                        "college_name": "",
                        "latitude": 0.0,
                        "longitude": 0.0,
                        "radius_meters": 500,
                        "wifi_ssids": [],
                        "enable_gps": True,
                        "enable_wifi": True,
                        "enable_ip_check": False,
                        "allowed_ip_ranges": [],
                        "verification_required": False
                    }
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            self.config = {}

    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Location Details Management",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Basic Settings Tab
        basic_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(basic_frame, text="Basic Settings")

        # Advanced Settings Tab
        advanced_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(advanced_frame, text="Advanced Settings")

        # Create basic settings
        self.create_basic_settings(basic_frame)

        # Create advanced settings
        self.create_advanced_settings(advanced_frame)

        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        # Buttons
        ttk.Button(btn_frame, text="Save Configuration", command=self.save_config,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Test Location", command=self.test_location).pack(side=tk.LEFT)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))

        # Configure styles
        style = ttk.Style()
        style.configure("Accent.TButton", background=self.primary_color, foreground="white")

    def reverse_geocode_location(self, lat, lng, api_key=None):
        """Convert coordinates to place name using OpenStreetMap Nominatim API (detailed addresses)"""
        try:
            # Use OpenStreetMap Nominatim API for detailed addresses
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&addressdetails=1"
            headers = {'User-Agent': 'Face-Recognition-Attendance-System/1.0'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'display_name' in data:
                    return data['display_name']
                elif 'error' in data:
                    return f"API Error: {data['error']}"
                else:
                    return "Unknown location - No address found"
            else:
                return f"HTTP Error: {response.status_code}"

        except Exception as e:
            return f"Connection Error: {str(e)}"

    def detect_location_name(self):
        """Detect place name from entered coordinates"""
        try:
            lat_str = self.latitude_var.get().strip()
            lng_str = self.longitude_var.get().strip()

            if not lat_str or not lng_str:
                messagebox.showwarning("Coordinates Required", "Please enter both latitude and longitude first.")
                return

            try:
                lat = float(lat_str)
                lng = float(lng_str)
            except ValueError:
                messagebox.showerror("Invalid Coordinates", "Please enter valid numeric coordinates.")
                return

            # Validate coordinate ranges
            if not (-90 <= lat <= 90):
                messagebox.showerror("Invalid Latitude", "Latitude must be between -90 and 90 degrees.")
                return
            if not (-180 <= lng <= 180):
                messagebox.showerror("Invalid Longitude", "Longitude must be between -180 and 180 degrees.")
                return

            self.status_var.set("Detecting location name...")
            self.root.update()

            location_name = self.reverse_geocode_location(lat, lng)

            if location_name and not location_name.startswith("Connection Error") and not location_name.startswith("API Error"):
                self.location_name_var.set(location_name)
                self.status_var.set(f"Detected: {location_name[:50]}...")
                messagebox.showinfo("Location Detected", f"Coordinates correspond to:\n\n{location_name}")
            else:
                self.status_var.set("Location detection failed")
                if location_name:
                    messagebox.showerror("Detection Failed", f"Could not detect location:\n{location_name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect location: {str(e)}")
            self.status_var.set("Location detection failed")

    def create_basic_settings(self, parent):
        """Create basic location settings"""
        # College Name
        ttk.Label(parent, text="College Name *:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.college_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.college_name_var, width=40).grid(row=0, column=1, padx=(10, 20), pady=5)

        # Latitude and Longitude with detection
        ttk.Label(parent, text="Latitude *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.latitude_var = tk.StringVar()
        lat_entry = ttk.Entry(parent, textvariable=self.latitude_var, width=25)
        lat_entry.grid(row=1, column=1, padx=(10, 5), pady=5, sticky=tk.W)
        ttk.Label(parent, text="(e.g., 16.234386)").grid(row=1, column=2, sticky=tk.W, pady=5)

        ttk.Label(parent, text="Longitude *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.longitude_var = tk.StringVar()
        lng_entry = ttk.Entry(parent, textvariable=self.longitude_var, width=25)
        lng_entry.grid(row=2, column=1, padx=(10, 5), pady=5, sticky=tk.W)
        ttk.Button(parent, text="Detect Location", command=self.detect_location_name,
                  style="Accent.TButton").grid(row=2, column=1, padx=(200, 20), pady=5)
        ttk.Label(parent, text="(e.g., 80.548087)").grid(row=2, column=2, sticky=tk.W, pady=5)

        # Detected Location Name
        ttk.Label(parent, text="Detected Location:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.location_name_var = tk.StringVar()
        location_entry = ttk.Entry(parent, textvariable=self.location_name_var, width=40, state='readonly')
        location_entry.grid(row=3, column=1, padx=(10, 20), pady=5)
        ttk.Label(parent, text="(Auto-detected from coordinates)").grid(row=3, column=2, sticky=tk.W, pady=5)

        # Radius
        ttk.Label(parent, text="Radius (meters) *:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.radius_var = tk.StringVar()
        radius_entry = ttk.Entry(parent, textvariable=self.radius_var, width=40)
        radius_entry.grid(row=4, column=1, padx=(10, 20), pady=5)
        ttk.Label(parent, text="(max distance allowed)").grid(row=4, column=2, sticky=tk.W, pady=5)

        # WiFi SSIDs
        ttk.Label(parent, text="WiFi Networks *:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        wifi_frame = ttk.Frame(parent)
        wifi_frame.grid(row=5, column=1, padx=(10, 20), pady=5, sticky=tk.W)

        self.wifi_text = scrolledtext.ScrolledText(wifi_frame, width=30, height=4)
        self.wifi_text.pack()

        ttk.Label(parent, text="One SSID per line").grid(row=5, column=2, sticky=tk.W, pady=5)

        # Verification Required
        ttk.Label(parent, text="Require Location Verification *:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.verification_var = tk.BooleanVar()
        ttk.Checkbutton(parent, variable=self.verification_var).grid(row=6, column=1, sticky=tk.W, padx=(10, 20), pady=5)

        # Required fields note
        note_label = ttk.Label(parent, text="* Required fields", foreground=self.accent_color)
        note_label.grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))

    def create_advanced_settings(self, parent):
        """Create advanced location settings"""
        # GPS Enable
        ttk.Label(parent, text="Enable GPS Verification:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.gps_var = tk.BooleanVar()
        ttk.Checkbutton(parent, variable=self.gps_var).grid(row=0, column=1, sticky=tk.W, padx=(10, 20), pady=5)

        # WiFi Enable
        ttk.Label(parent, text="Enable WiFi Verification:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.wifi_var = tk.BooleanVar()
        ttk.Checkbutton(parent, variable=self.wifi_var).grid(row=1, column=1, sticky=tk.W, padx=(10, 20), pady=5)

        # IP Check Enable
        ttk.Label(parent, text="Enable IP Range Check:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ip_var = tk.BooleanVar()
        ttk.Checkbutton(parent, variable=self.ip_var).grid(row=2, column=1, sticky=tk.W, padx=(10, 20), pady=5)

        # IP Ranges
        ttk.Label(parent, text="Allowed IP Ranges:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        ip_frame = ttk.Frame(parent)
        ip_frame.grid(row=3, column=1, padx=(10, 20), pady=5, sticky=tk.W)

        self.ip_text = scrolledtext.ScrolledText(ip_frame, width=30, height=4)
        self.ip_text.pack()

        ttk.Label(parent, text="One range per line (e.g., 192.168.1.0/24)").grid(row=3, column=2, sticky=tk.W, pady=5)

        # Help text
        help_text = """
Location Verification Methods:
• GPS: Checks if device is within specified radius of college coordinates
• WiFi: Verifies connection to allowed college WiFi networks
• IP Range: Checks if device IP is within allowed ranges

At least one verification method must be enabled.
If verification is required, attendance cannot proceed without passing at least one check.
        """
        help_label = ttk.Label(parent, text=help_text, justify=tk.LEFT, background="#f0f0f0", padding=10)
        help_label.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=(20, 0))

    def load_existing_config(self):
        """Load existing configuration into form fields"""
        # Basic settings
        self.college_name_var.set(self.config.get('college_name', ''))
        self.latitude_var.set(str(self.config.get('latitude', '')))
        self.longitude_var.set(str(self.config.get('longitude', '')))
        self.location_name_var.set('')  # Clear detected location on load
        self.radius_var.set(str(self.config.get('radius_meters', '')))
        self.verification_var.set(self.config.get('verification_required', False))

        # WiFi SSIDs
        wifi_ssids = self.config.get('wifi_ssids', [])
        self.wifi_text.delete(1.0, tk.END)
        for ssid in wifi_ssids:
            self.wifi_text.insert(tk.END, ssid + '\n')

        # Advanced settings
        self.gps_var.set(self.config.get('enable_gps', True))
        self.wifi_var.set(self.config.get('enable_wifi', True))
        self.ip_var.set(self.config.get('enable_ip_check', False))

        # IP ranges
        ip_ranges = self.config.get('allowed_ip_ranges', [])
        self.ip_text.delete(1.0, tk.END)
        for ip_range in ip_ranges:
            self.ip_text.insert(tk.END, ip_range + '\n')

        self.status_var.set("Configuration loaded successfully")

    def validate_input(self):
        """Validate input fields"""
        college_name = self.college_name_var.get().strip()
        latitude = self.latitude_var.get().strip()
        longitude = self.longitude_var.get().strip()
        radius = self.radius_var.get().strip()

        # Check required fields
        if not college_name:
            messagebox.showerror("Validation Error", "College Name is required!")
            self.notebook.select(0)  # Switch to basic settings tab
            return False

        if not latitude:
            messagebox.showerror("Validation Error", "Latitude is required!")
            self.notebook.select(0)
            return False

        if not longitude:
            messagebox.showerror("Validation Error", "Longitude is required!")
            self.notebook.select(0)
            return False

        if not radius:
            messagebox.showerror("Validation Error", "Radius is required!")
            self.notebook.select(0)
            return False

        # Validate numeric fields
        try:
            lat_val = float(latitude)
            if not (-90 <= lat_val <= 90):
                raise ValueError("Latitude must be between -90 and 90")
        except ValueError:
            messagebox.showerror("Validation Error", "Latitude must be a valid number between -90 and 90!")
            self.notebook.select(0)
            return False

        try:
            lon_val = float(longitude)
            if not (-180 <= lon_val <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        except ValueError:
            messagebox.showerror("Validation Error", "Longitude must be a valid number between -180 and 180!")
            self.notebook.select(0)
            return False

        try:
            radius_val = int(radius)
            if radius_val <= 0:
                raise ValueError("Radius must be positive")
        except ValueError:
            messagebox.showerror("Validation Error", "Radius must be a positive integer!")
            self.notebook.select(0)
            return False

        # Check WiFi SSIDs
        wifi_text = self.wifi_text.get(1.0, tk.END).strip()
        if not wifi_text:
            messagebox.showerror("Validation Error", "At least one WiFi network is required!")
            self.notebook.select(0)
            return False

        # Check that at least one verification method is enabled
        if not (self.gps_var.get() or self.wifi_var.get() or self.ip_var.get()):
            messagebox.showerror("Validation Error", "At least one verification method must be enabled!")
            self.notebook.select(1)  # Switch to advanced settings tab
            return False

        return True

    def save_config(self):
        """Save configuration to JSON file"""
        if not self.validate_input():
            return

        # Build configuration
        wifi_ssids = [line.strip() for line in self.wifi_text.get(1.0, tk.END).split('\n') if line.strip()]
        ip_ranges = [line.strip() for line in self.ip_text.get(1.0, tk.END).split('\n') if line.strip()]

        config = {
            "college_name": self.college_name_var.get().strip(),
            "latitude": float(self.latitude_var.get().strip()),
            "longitude": float(self.longitude_var.get().strip()),
            "radius_meters": int(self.radius_var.get().strip()),
            "wifi_ssids": wifi_ssids,
            "enable_gps": self.gps_var.get(),
            "enable_wifi": self.wifi_var.get(),
            "enable_ip_check": self.ip_var.get(),
            "allowed_ip_ranges": ip_ranges,
            "verification_required": self.verification_var.get()
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)

            self.config = config
            self.status_var.set("Configuration saved successfully")

            messagebox.showinfo("Success", "Location configuration saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset to default settings?"):
            # Load sample config
            sample_file = "location_config_sample.json"
            if os.path.exists(sample_file):
                with open(sample_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "college_name": "Your College Name",
                    "latitude": 28.5355,
                    "longitude": 77.3910,
                    "radius_meters": 500,
                    "wifi_ssids": ["College_WiFi", "Campus_Network", "Student_WiFi"],
                    "enable_gps": True,
                    "enable_wifi": True,
                    "enable_ip_check": False,
                    "allowed_ip_ranges": ["192.168.1.0/24", "10.0.0.0/8"],
                    "verification_required": False
                }

            self.load_existing_config()
            self.status_var.set("Reset to default settings")

    def test_location(self):
        """Test current location verification with warnings"""
        try:
            from location_verification import LocationVerifier
            verifier = LocationVerifier()
            verified, message, data, warnings = verifier.verify_location()

            result = "PASSED" if verified else "FAILED"
            title = f"Location Test: {result}"

            # Show main result
            detail_message = f"Status: {result}\n\nDetails:\n{message}"

            # Show warnings if any
            if warnings:
                detail_message += f"\n\n⚠️ WARNINGS:\n" + "\n".join(f"• {w}" for w in warnings)

            # Show additional info
            if data['wifi']['data']:
                wifi_data = data['wifi']['data']
                if wifi_data.get('connected_ssid'):
                    detail_message += f"\n\n📶 Current WiFi: {wifi_data['connected_ssid']}"
                if wifi_data.get('available_networks'):
                    detail_message += f"\n📡 Available networks: {', '.join(wifi_data['available_networks'][:5])}"

            if data['gps']['data'] and data['gps']['data'].get('current_location'):
                gps_data = data['gps']['data']
                lat, lon = gps_data['current_location']
                detail_message += f"\n\n📍 Current GPS: {lat:.6f}, {lon:.6f}"
                if gps_data.get('distance'):
                    detail_message += f"\n📏 Distance from college: {gps_data['distance']:.0f}m"

            if verified:
                messagebox.showinfo(title, detail_message)
            else:
                messagebox.showwarning(title, detail_message)

        except ImportError:
            messagebox.showerror("Error", "Location verification module not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Location test failed: {str(e)}")

def main():
    root = tk.Tk()
    app = LocationDetailsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()