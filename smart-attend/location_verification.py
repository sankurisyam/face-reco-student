# location_verification.py
"""
College Location Verification Module
Uses GPS and WiFi geofencing to verify student is at college during attendance
"""

import requests
import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocationVerifier:
    """Verify student location using GPS/WiFi data"""
    
    def __init__(self, config_file='location_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Load location configuration from file"""
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
            "college_name": "Your College Name",
            "latitude": 0.0,  # Set your college latitude
            "longitude": 0.0,  # Set your college longitude
            "radius_meters": 500,  # Acceptance radius in meters
            "wifi_ssids": ["College_WiFi", "Campus_Network"],  # Expected WiFi networks
            "enable_gps": True,
            "enable_wifi": True,
            "enable_ip_check": False,
            "allowed_ip_ranges": ["192.168.1.0/24"],  # Internal IP ranges
            "verification_required": False  # Make location verification mandatory
        }
    
    def save_config(self):
        """Save current config to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        logger.info(f"Config saved to {self.config_file}")
    
    def get_device_location_gps(self):
        """
        Get device location from GPS with user permission
        Returns: (latitude, longitude, accuracy) or None
        """
        try:
            # Method 1: Try Windows Location Services
            location = self.get_windows_location()
            if location:
                return location

            # Method 2: Try browser geolocation (requires user permission)
            location = self.get_browser_location()
            if location:
                return location

            # Method 3: Fallback to IP-based (less accurate)
            logger.warning("GPS methods failed, falling back to IP-based location")
            response = requests.get('https://ipinfo.io/json', timeout=5)
            if response.status_code == 200:
                data = response.json()
                loc = data.get('loc', '').split(',')
                if len(loc) == 2:
                    return float(loc[0]), float(loc[1]), 10000  # Approximate accuracy
            return None
        except Exception as e:
            logger.warning(f"GPS location fetch failed: {e}")
            return None

    def get_windows_location(self):
        """
        Try to get location from Windows Location Services
        Returns: (latitude, longitude, accuracy) or None
        """
        try:
            import subprocess
            # Try to get location using Windows location command
            result = subprocess.run(
                ['powershell', '-Command',
                 'Add-Type -AssemblyName System.Device; ' +
                 '$watcher = New-Object System.Device.Location.GeoCoordinateWatcher; ' +
                 '$watcher.Start(); ' +
                 'Start-Sleep -Milliseconds 1000; ' +
                 'if ($watcher.Position.Location.IsUnknown -eq $false) { ' +
                 '$watcher.Position.Location.Latitude.ToString() + "," + $watcher.Position.Location.Longitude.ToString() ' +
                 '} else { "Unknown" }'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip() != "Unknown":
                coords = result.stdout.strip().split(',')
                if len(coords) == 2:
                    try:
                        lat = float(coords[0])
                        lon = float(coords[1])
                        return lat, lon, 10  # Good accuracy for GPS
                    except ValueError:
                        pass
        except Exception as e:
            logger.debug(f"Windows location failed: {e}")
        return None

    def get_browser_location(self):
        """
        Get location using browser geolocation API
        Opens a browser window to request permission
        Returns: (latitude, longitude, accuracy) or None
        """
        try:
            # Create a simple HTML file for geolocation
            html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>Location Permission - Face Recognition Attendance</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .container { max-width: 600px; margin: 0 auto; }
        .button { background: #4CAF50; color: white; padding: 15px 30px;
                 border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        .status { margin: 20px 0; padding: 10px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📍 Location Permission Required</h1>
        <p>The attendance system needs to verify your location.</p>
        <p>Please click "Allow" when your browser asks for location permission.</p>

        <div id="status" class="status">Waiting for location permission...</div>

        <button id="getLocation" class="button">Get My Location</button>
        <button id="cancel" class="button" style="background: #f44336; margin-left: 10px;">Cancel</button>

        <script>
            let locationObtained = false;

            document.getElementById('getLocation').addEventListener('click', function() {
                document.getElementById('status').innerHTML = 'Requesting location permission...';
                document.getElementById('status').className = 'status';

                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            const lat = position.coords.latitude;
                            const lon = position.coords.longitude;
                            const acc = position.coords.accuracy;

                            document.getElementById('status').innerHTML =
                                `✅ Location obtained!<br>Latitude: ${lat.toFixed(6)}<br>Longitude: ${lon.toFixed(6)}<br>Accuracy: ${acc.toFixed(0)}m`;
                            document.getElementById('status').className = 'status success';

                            // Send location to Python server
                            fetch('http://localhost:8080/location', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ lat: lat, lon: lon, accuracy: acc })
                            }).then(() => {
                                locationObtained = true;
                                setTimeout(() => window.close(), 2000);
                            });
                        },
                        function(error) {
                            let errorMsg = 'Location access denied or failed';
                            switch(error.code) {
                                case error.PERMISSION_DENIED:
                                    errorMsg = 'Location permission denied. Please allow location access.';
                                    break;
                                case error.POSITION_UNAVAILABLE:
                                    errorMsg = 'Location information unavailable.';
                                    break;
                                case error.TIMEOUT:
                                    errorMsg = 'Location request timed out.';
                                    break;
                            }
                            document.getElementById('status').innerHTML = '❌ ' + errorMsg;
                            document.getElementById('status').className = 'status error';
                        },
                        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                    );
                } else {
                    document.getElementById('status').innerHTML = '❌ Geolocation not supported by this browser';
                    document.getElementById('status').className = 'status error';
                }
            });

            document.getElementById('cancel').addEventListener('click', function() {
                window.close();
            });

            // Auto-close after 30 seconds if no action
            setTimeout(() => {
                if (!locationObtained) {
                    window.close();
                }
            }, 30000);
        </script>
    </div>
</body>
</html>'''

            # Write HTML file
            with open('location_permission.html', 'w') as f:
                f.write(html_content)

            # Start local server to receive location data
            import http.server
            import socketserver
            import threading
            import time

            location_data = None

            class LocationHandler(http.server.BaseHTTPRequestHandler):
                def do_POST(self):
                    nonlocal location_data
                    if self.path == '/location':
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        location_data = json.loads(post_data.decode('utf-8'))
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b'Location received')

                def log_message(self, format, *args):
                    pass  # Suppress server logs

            # Start server in background thread
            with socketserver.TCPServer(("", 8080), LocationHandler) as httpd:
                server_thread = threading.Thread(target=httpd.serve_forever)
                server_thread.daemon = True
                server_thread.start()

                # Open browser
                import webbrowser
                webbrowser.open('file://' + os.path.abspath('location_permission.html'))

                # Wait for location data or timeout
                start_time = time.time()
                while location_data is None and (time.time() - start_time) < 15:
                    time.sleep(0.5)

                httpd.shutdown()

            # Clean up HTML file
            if os.path.exists('location_permission.html'):
                os.remove('location_permission.html')

            if location_data:
                return location_data['lat'], location_data['lon'], location_data.get('accuracy', 10)

        except Exception as e:
            logger.debug(f"Browser location failed: {e}")
        return None
    
    def get_current_wifi_connection(self):
        """
        Get the currently connected WiFi network name
        Returns: connected SSID or None
        """
        try:
            import subprocess
            # Get current WiFi connection
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if 'SSID' in line and 'BSSID' not in line:
                    ssid = line.split(':')[1].strip() if ':' in line else ''
                    if ssid:
                        return ssid
            return None
        except Exception as e:
            logger.warning(f"Current WiFi detection failed: {e}")
            return None

    def get_available_wifi_networks(self):
        """
        Get list of available WiFi networks
        Returns: List of available SSID names
        """
        try:
            import subprocess
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'networks', 'mode=Bssid'],
                capture_output=True,
                text=True,
                timeout=5
            )
            networks = []
            for line in result.stdout.split('\n'):
                if 'SSID' in line and not line.strip().startswith('SSID'):
                    ssid = line.split(':')[1].strip() if ':' in line else ''
                    if ssid and ssid not in networks:
                        networks.append(ssid)
            return networks
        except Exception as e:
            logger.warning(f"Available WiFi detection failed: {e}")
            return []
    
    def get_device_ip(self):
        """Get device's external IP address"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            if response.status_code == 200:
                return response.json()['ip']
            return None
        except Exception:
            return None
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in meters (Haversine formula)"""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Radius of earth in meters
        return c * r
    
    def verify_gps_location(self):
        """Verify if device is within acceptable radius of college"""
        if not self.config['enable_gps']:
            return True, "GPS verification disabled", None

        location = self.get_device_location_gps()
        if not location:
            return False, "Could not get GPS location", {
                'warning': 'GPS location unavailable',
                'current_location': None,
                'distance': None
            }

        lat, lon, accuracy = location
        distance = self.calculate_distance(
            lat, lon,
            self.config['latitude'],
            self.config['longitude']
        )

        if distance <= self.config['radius_meters']:
            return True, f"Location verified: {distance:.0f}m from college", {
                'warning': None,
                'current_location': (lat, lon),
                'distance': distance
            }
        else:
            warning_msg = f"You are {distance:.0f}m away from college (max allowed: {self.config['radius_meters']}m)"
            return False, f"Location outside college: {distance:.0f}m away (max allowed: {self.config['radius_meters']}m)", {
                'warning': warning_msg,
                'current_location': (lat, lon),
                'distance': distance
            }
    
    def verify_wifi_location(self):
        """Verify if device is connected to college WiFi"""
        if not self.config['enable_wifi']:
            return True, "WiFi verification disabled", None

        # Get currently connected WiFi
        connected_ssid = self.get_current_wifi_connection()
        available_networks = self.get_available_wifi_networks()

        if not connected_ssid:
            return False, "No WiFi connection detected", {
                'warning': 'No WiFi connection found',
                'connected_ssid': None,
                'available_networks': available_networks
            }

        # Check if connected to allowed WiFi
        allowed_ssids = self.config['wifi_ssids']
        if connected_ssid in allowed_ssids:
            return True, f"Connected to college WiFi: {connected_ssid}", {
                'warning': None,
                'connected_ssid': connected_ssid,
                'available_networks': available_networks
            }
        else:
            warning_msg = f"Connected to unauthorized WiFi: '{connected_ssid}'. Please connect to: {', '.join(allowed_ssids)}"
            return False, f"Not on college WiFi. Connected to: {connected_ssid}", {
                'warning': warning_msg,
                'connected_ssid': connected_ssid,
                'available_networks': available_networks
            }
    
    def verify_ip_location(self):
        """Verify if device is on college IP range"""
        if not self.config['enable_ip_check']:
            return True, "IP verification disabled"
        
        ip = self.get_device_ip()
        if not ip:
            return False, "Could not determine IP address"
        
        # This is a simplified check; proper implementation would check IP ranges
        return True, f"IP: {ip}"
    
    def verify_location(self):
        """
        Comprehensive location verification with warnings
        Returns: (is_verified, message, location_data, warnings)
        """
        location_data = {
            'timestamp': datetime.now().isoformat(),
            'gps': {'verified': False, 'message': '', 'data': None},
            'wifi': {'verified': False, 'message': '', 'data': None},
            'ip': {'verified': False, 'message': '', 'data': None},
            'overall': False
        }

        warnings = []

        # GPS verification
        if self.config['enable_gps']:
            gps_ok, gps_msg, gps_data = self.verify_gps_location()
            location_data['gps']['verified'] = gps_ok
            location_data['gps']['message'] = gps_msg
            location_data['gps']['data'] = gps_data
            if gps_data and gps_data.get('warning'):
                warnings.append(gps_data['warning'])

        # WiFi verification
        if self.config['enable_wifi']:
            wifi_ok, wifi_msg, wifi_data = self.verify_wifi_location()
            location_data['wifi']['verified'] = wifi_ok
            location_data['wifi']['message'] = wifi_msg
            location_data['wifi']['data'] = wifi_data
            if wifi_data and wifi_data.get('warning'):
                warnings.append(wifi_data['warning'])

        # IP verification
        if self.config['enable_ip_check']:
            ip_ok, ip_msg = self.verify_ip_location()
            location_data['ip']['verified'] = ip_ok
            location_data['ip']['message'] = ip_msg

        # Overall verification - More practical approach
        # If WiFi verification passes, allow attendance (GPS is bonus, not requirement)
        # This prevents IP-based geolocation inaccuracies from blocking valid attendance
        wifi_verified = location_data['wifi']['verified'] if self.config['enable_wifi'] else False
        gps_verified = location_data['gps']['verified'] if self.config['enable_gps'] else True
        ip_verified = location_data['ip']['verified'] if self.config['enable_ip_check'] else True

        # Primary check: WiFi verification (most reliable for campus)
        if self.config['enable_wifi'] and wifi_verified:
            overall_verified = True
            verification_note = "WiFi verified"
        # Secondary check: GPS verification (if WiFi not available/enabled)
        elif self.config['enable_gps'] and gps_verified:
            overall_verified = True
            verification_note = "GPS verified"
        # Fallback: IP verification
        elif self.config['enable_ip_check'] and ip_verified:
            overall_verified = True
            verification_note = "IP verified"
        else:
            overall_verified = False
            verification_note = "No verification method passed"

        location_data['overall'] = overall_verified

        message = (
            f"GPS: {location_data['gps']['message']}\n"
            f"WiFi: {location_data['wifi']['message']}\n"
            f"Overall: {'Verified' if overall_verified else 'Failed'} ({verification_note})"
        )

        return overall_verified, message, location_data, warnings

    def check_attendance_time_restrictions(self, period):
        """
        Check if attendance is allowed for the given period based on time restrictions
        Returns: (is_allowed, message, time_info)
        """
        time_restrictions = self.config.get('attendance_time_restrictions', {})
        if not time_restrictions.get('enabled', False):
            return True, "Time restrictions disabled", {}

        period_timings = time_restrictions.get('period_timings', {})
        grace_period = time_restrictions.get('grace_period_minutes', 15)

        if str(period) not in period_timings:
            return False, f"No timing defined for period {period}", {}

        period_info = period_timings[str(period)]
        period_name = period_info.get('name', f'Period {period}')
        start_time_str = period_info.get('start', '09:00')
        end_time_str = period_info.get('end', '10:00')

        # Parse times
        now = datetime.now()
        current_time = now.time()

        try:
            start_hour, start_min = map(int, start_time_str.split(':'))
            end_hour, end_min = map(int, end_time_str.split(':'))

            start_time = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0).time()
            end_time = now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0).time()

            # Add grace period to end time
            from datetime import timedelta
            grace_timedelta = timedelta(minutes=grace_period)
            end_time_with_grace = (datetime.combine(now.date(), end_time) + grace_timedelta).time()

        except (ValueError, AttributeError) as e:
            return False, f"Invalid time format for period {period}: {e}", {}

        time_info = {
            'period_name': period_name,
            'start_time': start_time_str,
            'end_time': end_time_str,
            'grace_period': grace_period,
            'current_time': current_time.strftime('%H:%M:%S'),
            'end_time_with_grace': end_time_with_grace.strftime('%H:%M:%S')
        }

        # Check if current time is within allowed window
        if current_time < start_time:
            time_info['status'] = 'too_early'
            return False, f"❌ {period_name} attendance not started yet.\nStarts at {start_time_str}, current time: {time_info['current_time']}", time_info

        if current_time > end_time_with_grace:
            time_info['status'] = 'too_late'
            return False, f"❌ {period_name} attendance time expired.\nEnded at {end_time_str} (grace: {grace_period}min), current time: {time_info['current_time']}", time_info

        time_info['status'] = 'allowed'
        return True, f"✅ {period_name} attendance allowed.\nTime window: {start_time_str} - {end_time_str} (grace: {grace_period}min)", time_info

    def verify_location_and_time(self, period):
        """
        Comprehensive verification including location and time restrictions
        Returns: (is_verified, message, data, warnings)
        """
        # First check time restrictions
        time_allowed, time_message, time_info = self.check_attendance_time_restrictions(period)

        if not time_allowed:
            return False, f"TIME RESTRICTION: {time_message}", {
                'location': None,
                'time': time_info,
                'overall': False
            }, []

        # If time is allowed, check location
        loc_verified, loc_message, loc_data, loc_warnings = self.verify_location()

        if not loc_verified:
            return False, f"LOCATION VERIFICATION FAILED\n\n{loc_message}", {
                'location': loc_data,
                'time': time_info,
                'overall': False
            }, loc_warnings

        # Both time and location verified
        return True, f"✅ VERIFICATION PASSED\n\nTime: {time_message}\nLocation: {loc_message}", {
            'location': loc_data,
            'time': time_info,
            'overall': True
        }, loc_warnings


def setup_college_location():
    """Interactive setup for college location"""
    print("\n=== College Location Setup ===")
    print("You can set up location verification for your college")
    
    verifier = LocationVerifier()
    config = verifier.config
    
    config['college_name'] = input(f"College name [{config['college_name']}]: ") or config['college_name']
    
    try:
        config['latitude'] = float(input(f"College latitude [{config['latitude']}]: ") or config['latitude'])
        config['longitude'] = float(input(f"College longitude [{config['longitude']}]: ") or config['longitude'])
        config['radius_meters'] = int(input(f"Acceptance radius in meters [{config['radius_meters']}]: ") or config['radius_meters'])
    except ValueError:
        print("Invalid coordinates")
    
    print("\nWiFi Networks at college (comma-separated):")
    ssids = input(f"[{', '.join(config['wifi_ssids'])}]: ")
    if ssids:
        config['wifi_ssids'] = [s.strip() for s in ssids.split(',')]
    
    config['enable_gps'] = input("Enable GPS verification? (y/n): ").lower() == 'y'
    config['enable_wifi'] = input("Enable WiFi verification? (y/n): ").lower() == 'y'
    
    verifier.save_config()
    print("✓ Location configuration saved!")


if __name__ == "__main__":
    setup_college_location()
