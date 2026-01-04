#!/usr/bin/env python
"""Add M.Sc exams to the database"""
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import ensure_sample_exams

if __name__ == '__main__':
    print("Adding sample exams...")
    ensure_sample_exams()
    print("Done!")
