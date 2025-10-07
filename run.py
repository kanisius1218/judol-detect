#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convenience runner script for the spam moderator.
Run from project root: python run.py
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# Import and run
from src.main import main

if __name__ == "__main__":
    main()
