#!/usr/bin/env python3
"""
Simple database setup script for Campus Linker
This script creates a SQLite database for testing purposes
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def create_sqlite_database():
    """Create SQLite database with all required tables"""
    
    # Create database directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect('data/campus_linker.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email_id TEXT UNIQUE NOT NULL,
            mobile_no TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            course_code TEXT UNIQUE NOT NULL,
            duration_years INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admission (
            admission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_id INTEGER,
            student_name TEXT NOT NULL,
            course_name TEXT NOT NULL,
            email_id TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            father_name TEXT NOT NULL,
            mother_name TEXT NOT NULL,
            mobile_no TEXT NOT NULL,
            aadhar_no TEXT UNIQUE NOT NULL,
            address TEXT NOT NULL,
            state TEXT NOT NULL,
            district TEXT NOT NULL,
            pincode TEXT NOT NULL,
            gender TEXT NOT NULL,
            previous_year_cgpa REAL,
            obtain_marks INTEGER,
            total_marks INTEGER,
            percentage REAL,
            passing_year INTEGER,
            photo_path TEXT,
            id_proof_path TEXT,
            sign_path TEXT,
            previous_year_marklist_path TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (registration_id) REFERENCES registration(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_id INTEGER,
            student_name TEXT NOT NULL,
            course_name TEXT NOT NULL,
            activity_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admission_id) REFERENCES admission(admission_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam (
            exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_type TEXT NOT NULL,
            exam_fee REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS result (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            exam_id INTEGER,
            course_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            obtain_marks INTEGER NOT NULL,
            total_marks INTEGER NOT NULL,
            grade TEXT,
            exam_type TEXT,
            cgpa REAL,
            result_status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student(student_id),
            FOREIGN KEY (exam_id) REFERENCES exam(exam_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fee (
            fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_id INTEGER,
            student_name TEXT NOT NULL,
            course_name TEXT NOT NULL,
            exam_category TEXT,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT DEFAULT 'Pending',
            payment_date TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admission_id) REFERENCES admission(admission_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS social_activity (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_name TEXT NOT NULL,
            activity_category TEXT NOT NULL,
            activity_date DATE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student(student_id)
        )
    ''')
    
    # Insert sample courses
    courses = [
        ('BBA', 'BBA001', 3),
        ('B.Com', 'BCOM001', 3),
        ('B.Sc', 'BSC001', 3),
        ('MBA', 'MBA001', 2),
        ('M.Com', 'MCOM001', 2),
        ('M.Sc', 'MSC001', 2),
        ('Data Science', 'DS001', 2)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO course (course_name, course_code, duration_years)
        VALUES (?, ?, ?)
    ''', courses)
    
    # Insert sample user for testing
    test_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO registration (username, password, email_id, mobile_no)
        VALUES (?, ?, ?, ?)
    ''', ('admin', test_password, 'admin@skylink.edu', '9876543210'))
    
    conn.commit()
    conn.close()
    
    print("✅ SQLite database created successfully!")
    print("📁 Database location: data/campus_linker.db")
    print("👤 Test user created: admin / admin123")

if __name__ == '__main__':
    create_sqlite_database()
