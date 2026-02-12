#!/usr/bin/env python3
"""
Test script to verify location detection functionality in the GUI
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from location_details_gui import LocationDetailsGUI
import tkinter as tk

def test_location_detection():
    """Test the location detection functionality"""
    print("Testing Location Detection GUI...")

    # Create a minimal GUI instance for testing
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    app = LocationDetailsGUI(root)

    # Set test coordinates
    app.latitude_var.set("16.234386")
    app.longitude_var.set("80.548087")

    print("Set coordinates: 16.234386, 80.548087")

    # Test the reverse geocoding function directly
    location_name = app.reverse_geocode_location(16.234386, 80.548087)
    print(f"Detected location: {location_name}")

    # Check if it's detailed
    if "vignan junior college" in location_name.lower():
        print("✓ Detailed address detected successfully!")
        print("✓ Contains expected location name")
    else:
        print("✗ Location detection may not be working correctly")

    root.destroy()
    return location_name

if __name__ == "__main__":
    result = test_location_detection()
    print(f"\nFinal result: {result}")