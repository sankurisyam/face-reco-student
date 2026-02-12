import requests

def reverse_geocode_location(lat, lon):
    """
    Reverse geocode latitude and longitude to get detailed location address using OpenStreetMap Nominatim API.
    Returns the full display_name from the API response.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {
            'User-Agent': 'Face-Recognition-Attendance-System/1.0'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if 'display_name' in data:
            return data['display_name']
        else:
            return "Location not found"

    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

# Test the function with the coordinates
if __name__ == "__main__":
    lat = 16.234386
    lon = 80.548087

    print("Testing reverse geocoding with OpenStreetMap...")
    print(f"Coordinates: {lat}, {lon}")
    print("Fetching detailed address...")

    address = reverse_geocode_location(lat, lon)
    print(f"Detailed Address: {address}")