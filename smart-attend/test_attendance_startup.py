#!/usr/bin/env python3
"""
Test attendance system startup with location verification
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_attendance_startup():
    """Test if attendance system can start with current location verification"""

    print("Testing Attendance System Startup")
    print("=" * 40)

    try:
        from location_verification import LocationVerifier

        print("1. Checking location verification...")
        verifier = LocationVerifier()
        verified, message, data, warnings = verifier.verify_location()

        print(f"   Location Verified: {verified}")
        print(f"   Message: {message}")

        if verified:
            print("   ✅ Location verification passed!")
            print("\n2. Attendance system should start successfully.")
            print("   The system will now allow attendance when connected to college WiFi.")
            return True
        else:
            print("   ❌ Location verification failed!")
            print(f"   Warnings: {warnings}")
            print("\n2. Attendance system will be blocked.")
            return False

    except Exception as e:
        print(f"❌ Error testing attendance system: {e}")
        return False

if __name__ == "__main__":
    success = test_attendance_startup()
    if success:
        print("\n🎉 SUCCESS: Attendance system is ready!")
    else:
        print("\n💥 FAILURE: Attendance system has issues.")