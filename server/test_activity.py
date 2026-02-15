import requests

url = "http://localhost:5000/api/ml/recognize/activity"
headers = {
    "Authorization": "Bearer YOUR_TOKEN_HERE",
    "Content-Type": "application/json"
}

data = {
    "device_id": "baeb2051-b987-4b68-aa3b-1caa41c23a50",
    "accelerometer_x": 0.5,
    "accelerometer_y": 0.3,
    "accelerometer_z": 9.8,
    "gyroscope_x": 0.1,
    "gyroscope_y": 0.05,
    "gyroscope_z": 0.02
}

response = requests.post(url, json=data, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")