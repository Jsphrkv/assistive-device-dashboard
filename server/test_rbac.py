#!/usr/bin/env python3
"""
Test RBAC (Role-Based Access Control)
"""

import requests
import json

API_URL = "http://localhost:5000/api"

def login(username, password):
    """Login and get token"""
    response = requests.post(
        f"{API_URL}/auth/login",
        json={'username': username, 'password': password}
    )
    if response.status_code == 200:
        return response.json()['token']
    return None

def test_user_permissions():
    """Test what a regular user can and cannot do"""
    print("\n" + "="*60)
    print("Testing USER Permissions")
    print("="*60)
    
    # Login as user
    token = login('user', 'user123')
    headers = {'Authorization': f'Bearer {token}'}
    
    # ✅ Should work: Read detections
    print("\n1. User reading detections (should work):")
    response = requests.get(f"{API_URL}/detections", headers=headers)
    print(f"   Status: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # ✅ Should work: Read statistics
    print("\n2. User reading statistics (should work):")
    response = requests.get(f"{API_URL}/statistics/daily", headers=headers)
    print(f"   Status: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # ✅ Should work: Update allowed settings
    print("\n3. User updating sensitivity (should work):")
    response = requests.put(
        f"{API_URL}/settings",
        headers=headers,
        json={'sensitivity': 80, 'alertMode': 'audio'}
    )
    print(f"   Status: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # ❌ Should FAIL: Update admin-only settings
    print("\n4. User updating distance threshold (should FAIL):")
    response = requests.put(
        f"{API_URL}/settings",
        headers=headers,
        json={'distanceThreshold': 150}
    )
    print(f"   Status: {response.status_code} {'✓ BLOCKED' if response.status_code == 403 else '✗ NOT BLOCKED!'}")
    if response.status_code == 403:
        print(f"   Message: {response.json().get('message')}")
    
    # ❌ Should FAIL: View global settings
    print("\n5. User viewing global settings (should FAIL):")
    response = requests.get(f"{API_URL}/settings/global", headers=headers)
    print(f"   Status: {response.status_code} {'✓ BLOCKED' if response.status_code == 403 else '✗ NOT BLOCKED!'}")

def test_admin_permissions():
    """Test what an admin can do"""
    print("\n" + "="*60)
    print("Testing ADMIN Permissions")
    print("="*60)
    
    # Login as admin
    token = login('admin', 'admin123')
    headers = {'Authorization': f'Bearer {token}'}
    
    # ✅ Should work: Update all settings
    print("\n1. Admin updating distance threshold (should work):")
    response = requests.put(
        f"{API_URL}/settings",
        headers=headers,
        json={'distanceThreshold': 150, 'ultrasonicEnabled': False}
    )
    print(f"   Status: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # ✅ Should work: View global settings
    print("\n2. Admin viewing global settings (should work):")
    response = requests.get(f"{API_URL}/settings/global", headers=headers)
    print(f"   Status: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")

def main():
    print("\n" + "="*60)
    print("RBAC Testing Suite")
    print("="*60)
    print("Make sure backend is running on http://localhost:5000")
    
    # Test user permissions
    test_user_permissions()
    
    # Test admin permissions
    test_admin_permissions()
    
    print("\n" + "="*60)
    print("✓ RBAC Tests Complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()