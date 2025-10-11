-- Campus Linker Database Schema
-- Creating all tables based on the provided design

-- Registration table
CREATE TABLE IF NOT EXISTS registration (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email_id VARCHAR(100) UNIQUE NOT NULL,
    mobile_no VARCHAR(15) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admission table
CREATE TABLE IF NOT EXISTS admission (
    admission_id INT PRIMARY KEY AUTO_INCREMENT,
    registration_id INT,
    student_name VARCHAR(100) NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    email_id VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    father_name VARCHAR(100) NOT NULL,
    mother_name VARCHAR(100) NOT NULL,
    mobile_no VARCHAR(15) NOT NULL,
    aadhar_no VARCHAR(12) UNIQUE NOT NULL,
    address TEXT NOT NULL,
    state VARCHAR(50) NOT NULL,
    district VARCHAR(50) NOT NULL,
    pincode VARCHAR(6) NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    previous_year_cgpa DECIMAL(3,2),
    obtain_marks INT,
    total_marks INT,
    percentage DECIMAL(5,2),
    passing_year YEAR,
    photo_path VARCHAR(255),
    id_proof_path VARCHAR(255),
    sign_path VARCHAR(255),
    previous_year_marklist_path VARCHAR(255),
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (registration_id) REFERENCES registration(id)
);

-- Student table
CREATE TABLE IF NOT EXISTS student (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    admission_id INT,
    student_name VARCHAR(100) NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    activity_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admission(admission_id)
);

-- Course table
CREATE TABLE IF NOT EXISTS course (
    course_id INT PRIMARY KEY AUTO_INCREMENT,
    course_name VARCHAR(100) NOT NULL,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    duration_years INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity table
CREATE TABLE IF NOT EXISTS activity (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    course_name VARCHAR(100) NOT NULL,
    activity_category VARCHAR(100) NOT NULL,
    activity_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id)
);

-- Exam table
CREATE TABLE IF NOT EXISTS exam (
    exam_id INT PRIMARY KEY AUTO_INCREMENT,
    exam_type VARCHAR(50) NOT NULL,
    exam_fee DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Result table
CREATE TABLE IF NOT EXISTS result (
    result_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    exam_id INT,
    course_name VARCHAR(100) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    obtain_marks INT NOT NULL,
    total_marks INT NOT NULL,
    grade VARCHAR(2),
    exam_type VARCHAR(50),
    cgpa DECIMAL(3,2),
    result_status ENUM('Pass', 'Fail', 'ATKT') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id)
);

-- Fee Management table
CREATE TABLE IF NOT EXISTS fee (
    fee_id INT PRIMARY KEY AUTO_INCREMENT,
    admission_id INT,
    student_name VARCHAR(100) NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    exam_category VARCHAR(100),
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status ENUM('Pending', 'Paid', 'Failed') DEFAULT 'Pending',
    payment_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admission(admission_id)
);

-- Social Activity table
CREATE TABLE IF NOT EXISTS social_activity (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    course_name VARCHAR(100) NOT NULL,
    activity_category VARCHAR(100) NOT NULL,
    activity_date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id)
);
