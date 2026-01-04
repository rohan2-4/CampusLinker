#!/usr/bin/env python3
"""
Fresh database setup for Campus Linker
This will create a clean database with all required tables
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def fresh_database_setup():
    """Create a fresh SQLite database with all required tables"""
    
    # Create database directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Remove existing database if it exists
    if os.path.exists('data/campus_linker.db'):
        os.remove('data/campus_linker.db')
        print("🗑️  Removed existing database")
    
    # Connect to SQLite database
    conn = sqlite3.connect('data/campus_linker.db')
    cursor = conn.cursor()
    
    print("🔄 Creating database tables...")
    
    # Create tables in correct order to handle foreign keys
    cursor.execute('''
        CREATE TABLE registration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email_id TEXT UNIQUE NOT NULL,
            mobile_no TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE course (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            course_code TEXT UNIQUE NOT NULL,
            duration_years INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE admission (
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
        CREATE TABLE student (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_id INTEGER,
            student_name TEXT NOT NULL,
            course_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admission_id) REFERENCES admission(admission_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE exam (
            exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_type TEXT NOT NULL,
            exam_fee REAL DEFAULT 0,
            exam_name TEXT NOT NULL,
            course_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            exam_date DATE NOT NULL,
            exam_time TIME NOT NULL,
            duration INTEGER NOT NULL,
            max_marks INTEGER NOT NULL,
            instructions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE result (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            exam_id INTEGER,
            course_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            obtain_marks INTEGER DEFAULT 0,
            total_marks INTEGER DEFAULT 0,
            grade TEXT,
            exam_type TEXT,
            cgpa REAL,
            result_status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student(student_id),
            FOREIGN KEY (exam_id) REFERENCES exam(exam_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE fee (
            fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_id INTEGER,
            student_name TEXT NOT NULL,
            course_name TEXT NOT NULL,
            total_fee REAL NOT NULL DEFAULT 0,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT DEFAULT 'Pending',
            payment_date TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admission_id) REFERENCES admission(admission_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE social_activity (
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
    
    cursor.execute('''
        CREATE TABLE course_fee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            fee_category TEXT NOT NULL,
            amount REAL NOT NULL
        )
    ''')
    
    print("✅ All tables created successfully!")
    
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
        INSERT INTO course (course_name, course_code, duration_years)
        VALUES (?, ?, ?)
    ''', courses)
    print("✅ Courses inserted")
    
    # Insert sample users
    admin_password = generate_password_hash('admin123')
    student_password = generate_password_hash('student123')
    
    cursor.execute('''
        INSERT INTO registration (username, password, email_id, mobile_no, role)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin', admin_password, 'admin@skylink.edu', '9876543210', 'admin'))
    
    cursor.execute('''
        INSERT INTO registration (username, password, email_id, mobile_no, role)
        VALUES (?, ?, ?, ?, ?)
    ''', ('student', student_password, 'student@skylink.edu', '9876543211', 'student'))
    print("✅ Users created")
    
    # Insert sample course fees
    course_fees = [
        ('BBA', 'Admission Fee', 5000.0),
        ('BBA', 'Tuition Fee', 20000.0),
        ('BBA', 'Exam Fee', 1500.0),
        ('B.Com', 'Admission Fee', 4500.0),
        ('B.Com', 'Tuition Fee', 18000.0),
        ('B.Com', 'Exam Fee', 1200.0),
        ('B.Sc', 'Admission Fee', 5200.0),
        ('B.Sc', 'Tuition Fee', 22000.0),
        ('B.Sc', 'Exam Fee', 1600.0),
        ('M.Sc', 'Admission Fee', 5000.0),
        ('M.Sc', 'Tuition Fee', 22000.0),
        ('M.Sc', 'Exam Fee', 1500.0),
        ('M.Sc', 'Library Fee', 500.0),
        ('M.Sc', 'Hostel Fee', 15000.0),
        ('M.Sc', 'Other Fee', 0.0),
    ]
    
    cursor.executemany('''
        INSERT INTO course_fee (course_name, fee_category, amount)
        VALUES (?, ?, ?)
    ''', course_fees)
    print("✅ Course fees inserted")
    
    # Insert sample exams
    sample_exams = [
        ('Midterm Exam 2025', 'Mathematics', 'Midterm', 'BBA', '2025-03-15', '10:00', 180, 100, 'Bring calculator and ID card'),
        ('Final Exam 2025', 'Computer Science', 'Final', 'BBA', '2025-05-20', '14:00', 180, 100, 'No electronic devices allowed'),
        ('Midterm Exam 2025', 'Accounting', 'Midterm', 'B.Com', '2025-03-16', '10:00', 180, 100, 'Open book exam'),
        ('Midterm Exam 2025', 'Physics', 'Midterm', 'M.Sc', '2025-03-17', '09:00', 180, 100, 'Bring calculator and ID card'),
        ('Midterm Exam 2025', 'Chemistry', 'Midterm', 'M.Sc', '2025-03-18', '10:00', 180, 100, 'No electronic devices allowed'),
        ('Final Exam 2025', 'Advanced Mathematics', 'Final', 'M.Sc', '2025-05-21', '14:00', 180, 100, 'Open book exam'),
        ('Final Exam 2025', 'Quantum Mechanics', 'Final', 'M.Sc', '2025-05-22', '14:00', 180, 100, 'Bring scientific calculator'),
    ]
    
    cursor.executemany('''
        INSERT INTO exam (exam_name, subject, exam_type, course_name, exam_date, exam_time, duration, max_marks, instructions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_exams)
    print("✅ Sample exams inserted")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Fresh database setup completed successfully!")
    print("📁 Database location: data/campus_linker.db")
    print("👤 Admin user: admin / admin123")
    print("👤 Student user: student / student123")
    print("\n🚀 You can now run the application!")

if __name__ == '__main__':
    fresh_database_setup()