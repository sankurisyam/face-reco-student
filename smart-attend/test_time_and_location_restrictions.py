import pytest
from datetime import datetime, timedelta

from location_verification import LocationVerifier


def make_time_str(dt):
    return dt.strftime('%H:%M')


def test_check_attendance_time_restrictions_disabled():
    """Test that time restrictions can be disabled"""
    v = LocationVerifier()
    v.config['attendance_time_restrictions'] = {
        'enabled': False,
        'period_timings': {}
    }
    allowed, msg, info = v.check_attendance_time_restrictions(1)
    assert allowed is True
    assert 'disabled' in msg.lower()


def test_check_attendance_time_restrictions_allowed():
    """Test attendance allowed within time window"""
    v = LocationVerifier()
    now = datetime.now()
    
    # Create a window that covers current time
    start = (now - timedelta(hours=1)).strftime('%H:%M')
    end = (now + timedelta(hours=1)).strftime('%H:%M')
    
    v.config['attendance_time_restrictions'] = {
        'enabled': True,
        'grace_period_minutes': 15,
        'period_timings': {
            '1': {'name': 'Period 1', 'start': start, 'end': end}
        }
    }

    allowed, msg, info = v.check_attendance_time_restrictions(1)
    assert allowed is True
    assert info['status'] == 'allowed'
    assert 'Period 1' in msg


def test_check_attendance_time_restrictions_too_early():
    """Test attendance blocked before start time"""
    v = LocationVerifier()
    now = datetime.now()

    # start is 1 hour in future
    start_future = (now + timedelta(hours=1)).strftime('%H:%M')
    end_future = (now + timedelta(hours=2)).strftime('%H:%M')

    v.config['attendance_time_restrictions'] = {
        'enabled': True,
        'grace_period_minutes': 0,
        'period_timings': {
            '2': {'name': 'Period 2', 'start': start_future, 'end': end_future}
        }
    }

    allowed, msg, info = v.check_attendance_time_restrictions(2)
    assert allowed is False
    assert info['status'] == 'too_early'


def test_check_attendance_time_restrictions_too_late():
    """Test attendance blocked after end time + grace"""
    v = LocationVerifier()
    now = datetime.now()

    # end is 30 minutes in the past (enough to pass start_time check but fail end_time)
    start_past = (now - timedelta(hours=1)).strftime('%H:%M')
    end_past = (now - timedelta(minutes=30)).strftime('%H:%M')

    v.config['attendance_time_restrictions'] = {
        'enabled': True,
        'grace_period_minutes': 0,  # no grace period
        'period_timings': {
            '3': {'name': 'Period 3', 'start': start_past, 'end': end_past}
        }
    }
    allowed, msg, info = v.check_attendance_time_restrictions(3)
    assert allowed is False
    assert info['status'] == 'too_late'


def test_check_attendance_time_restrictions_missing_period():
    """Test no timing defined for a period"""
    v = LocationVerifier()
    v.config['attendance_time_restrictions'] = {
        'enabled': True, 
        'period_timings': {}
    }
    allowed, msg, info = v.check_attendance_time_restrictions(99)
    assert allowed is False
    assert 'No timing defined for period' in msg


def test_verify_location_and_time_time_blocked():
    """Test location check is skipped when time is not allowed"""
    v = LocationVerifier()
    now = datetime.now()
    # set time restrictions to block (future window)
    start_future = (now + timedelta(hours=1)).strftime('%H:%M')
    end_future = (now + timedelta(hours=2)).strftime('%H:%M')
    v.config['attendance_time_restrictions'] = {
        'enabled': True,
        'grace_period_minutes': 0,
        'period_timings': {
            '1': {'name': 'Period 1', 'start': start_future, 'end': end_future}
        }
    }

    verified, message, data, warnings = v.verify_location_and_time(1)
    assert verified is False
    assert 'TIME RESTRICTION' in message
    assert data['overall'] is False


def test_verify_location_and_time_location_failed(monkeypatch):
    """Test verification fails when location check fails"""
    v = LocationVerifier()
    now = datetime.now()
    
    # allow time (past start, before end + grace)
    start = (now - timedelta(hours=1)).strftime('%H:%M')
    end = (now + timedelta(hours=1)).strftime('%H:%M')
    
    v.config['attendance_time_restrictions'] = {
        'enabled': True,
        'grace_period_minutes': 15,
        'period_timings': {
            '1': {'name': 'Period 1', 'start': start, 'end': end}
        }
    }

    # patch verify_location to simulate failure
    def fake_verify_location():
        return False, 'GPS/WiFi failed', {'gps': {}, 'wifi': {}}, ['gps warning']

    monkeypatch.setattr(v, 'verify_location', fake_verify_location)

    verified, message, data, warnings = v.verify_location_and_time(1)
    assert verified is False
    assert 'LOCATION VERIFICATION FAILED' in message
    assert warnings == ['gps warning']


def test_verify_location_and_time_success(monkeypatch):
    """Test verification succeeds when both time and location pass"""
    v = LocationVerifier()
    now = datetime.now()
    
    # allow time
    start = (now - timedelta(hours=1)).strftime('%H:%M')
    end = (now + timedelta(hours=1)).strftime('%H:%M')
    
    v.config['attendance_time_restrictions'] = {
        'enabled': True,
        'grace_period_minutes': 15,
        'period_timings': {
            '1': {'name': 'Period 1', 'start': start, 'end': end}
        }
    }

    def fake_verify_location():
        return True, 'WiFi verified', {'wifi': {}}, []

    monkeypatch.setattr(v, 'verify_location', fake_verify_location)

    verified, message, data, warnings = v.verify_location_and_time(1)
    assert verified is True
    assert data['overall'] is True
    assert 'VERIFICATION PASSED' in message
    assert warnings == []
