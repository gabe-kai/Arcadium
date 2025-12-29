#!/usr/bin/env python3
"""
Test script to verify token authentication flow between Wiki and Auth services.
Run this after logging in to test if token verification works.
"""

import json
import sys

import requests

# Get token from user input
print("Please paste your JWT token (from browser localStorage 'auth_token'):")
token = input().strip()

if not token:
    print("Error: No token provided")
    sys.exit(1)

# Test 1: Verify token with Auth Service directly
print("\n=== Test 1: Direct Auth Service Verification ===")
auth_url = "http://localhost:8000/api/auth/verify"
try:
    response = requests.post(
        auth_url,
        json={"token": token},
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if response.status_code == 200:
        print("✅ Token is valid according to Auth Service")
    else:
        print("❌ Token is invalid according to Auth Service")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 2: Try to create a page with the token
print("\n=== Test 2: Wiki Service Page Creation ===")
wiki_url = "http://localhost:5000/api/pages"
try:
    response = requests.post(
        wiki_url,
        json={
            "title": "Test Page from Script",
            "content": "# Test Content",
            "slug": "test-page-from-script",
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        timeout=10,
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if response.status_code == 201:
        print("✅ Page creation succeeded")
    elif response.status_code == 401:
        print("❌ Page creation failed: Authentication error")
    else:
        print(f"⚠️  Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n=== Done ===")
