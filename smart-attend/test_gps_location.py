#!/usr/bin/env python3
"""
Test the new GPS location detection with permission request
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from location_verification import LocationVerifier

def test_gps_location():
    """Test the new GPS location detection"""

    print("Testing New GPS Location Detection")
    print("=" * 40)

    verifier = LocationVerifier()

    print("Configuration:")
    print(f"GPS Enabled: {verifier.config['enable_gps']}")
    print(f"WiFi Enabled: {verifier.config['enable_wifi']}")
    print(f"College Coordinates: {verifier.config['latitude']}, {verifier.config['longitude']}")
    print(f"Radius: {verifier.config['radius_meters']} meters")
    print()

    print("Testing GPS location detection...")
    print("Note: This may open a browser window to request location permission.")
    print("Please allow location access when prompted.")
    print()

    # Test GPS location
    location = verifier.get_device_location_gps()

    if location:
        lat, lon, accuracy = location
        print("✅ GPS Location obtained!")
        print(f"Latitude: {lat:.6f}")
        print(f"Longitude: {lon:.6f}")
        print(f"Accuracy: {accuracy:.1f} meters")

        # Calculate distance from college
        distance = verifier.calculate_distance(lat, lon,
                                             verifier.config['latitude'],
                                             verifier.config['longitude'])

        print(f"Distance from college: {distance:.1f} meters")
        print(f"Within radius: {'✅ YES' if distance <= verifier.config['radius_meters'] else '❌ NO'}")

    else:
        print("❌ GPS location detection failed")
        print("This could be due to:")
        print("- Location permission denied")
        print("- GPS/location services disabled")
        print("- Network issues")

    print()
    print("Testing full location verification...")

    # Test full verification
    verified, message, data, warnings = verifier.verify_location()

    print(f"Overall Verified: {verified}")
    print(f"Message: {message}")
    if warnings:
        print(f"Warnings: {warnings}")

if __name__ == "__main__":
    test_gps_location()