#!/usr/bin/env python
"""Debug script to run tests one at a time"""

import subprocess
import sys
import time

test_names = [
    "test_health_check",
    "test_list_pages_empty",
    "test_list_pages_with_page",
    "test_list_pages_with_filters",
    "test_get_page",
    "test_get_page_not_found",
    "test_get_page_draft_visibility",
    "test_create_page_requires_auth",
    "test_create_page_success",
    "test_create_page_missing_title",
    "test_create_page_viewer_forbidden",
    "test_update_page_requires_auth",
    "test_update_page_success",
    "test_update_page_wrong_owner",
    "test_update_page_admin_can_edit_any",
    "test_delete_page_requires_auth",
    "test_delete_page_success",
    "test_delete_page_with_children",
]

print("Running tests one at a time to find the hanging test...\n")

for i, test_name in enumerate(test_names, 1):
    print(f"[{i}/{len(test_names)}] Running {test_name}...", flush=True)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        f"tests/test_api/test_page_routes.py::{test_name}",
        "-v",
        "--tb=short",
        "--no-cov",
    ]

    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"  ✓ PASSED in {elapsed:.2f}s")
        else:
            print(f"  ✗ FAILED in {elapsed:.2f}s")
            print(f"  Output: {result.stdout[:200]}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("  ⚠ TIMEOUT after 10s - THIS TEST IS HANGING!")
        print("  This is likely the problematic test.")
        break
    except Exception as e:
        print(f"  ✗ ERROR: {e}")

    print()

print("\nDone!")
