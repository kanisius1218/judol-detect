#!/usr/bin/env python3
"""Clean up redundant files"""
import os

files_to_remove = [
    'FINAL_SUMMARY.md',
    'FOLDER_STRUCTURE_COMPLETE.md'
]

for file in files_to_remove:
    try:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ Removed: {file}")
        else:
            print(f"⊘ Not found: {file}")
    except Exception as e:
        print(f"✗ Error removing {file}: {e}")

print("\nCleanup complete!")
