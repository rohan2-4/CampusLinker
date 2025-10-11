-- Sample data for Campus Linker system

-- Insert sample courses
INSERT INTO course (course_name, course_code, duration_years) VALUES
('Bachelor of Business Administration', 'BBA', 3),
('Bachelor of Commerce', 'BCOM', 3),
('Bachelor of Science', 'BSC', 3),
('Master of Business Administration', 'MBA', 2),
('Master of Commerce', 'MCOM', 2),
('Master of Science', 'MSC', 2),
('Data Science', 'DS', 2);

-- Insert sample exam types
INSERT INTO exam (exam_type, exam_fee) VALUES
('Semester 1', 1500.00),
('Semester 2', 1500.00),
('Semester 3', 1500.00),
('Semester 4', 1500.00),
('Semester 5', 1500.00),
('Semester 6', 1500.00),
('Final Exam', 2000.00);

-- Insert sample registration
INSERT INTO registration (username, password, email_id, mobile_no) VALUES
('admin', 'admin123', 'admin@skylink.edu', '9876543210'),
('student1', 'pass123', 'student1@skylink.edu', '9876543211');

-- Insert sample admission
INSERT INTO admission (
    registration_id, student_name, course_name, email_id, date_of_birth,
    father_name, mother_name, mobile_no, aadhar_no, address, state, district,
    pincode, gender, previous_year_cgpa, obtain_marks, total_marks, percentage,
    passing_year, status
) VALUES (
    2, 'John Doe', 'Bachelor of Business Administration', 'john.doe@skylink.edu',
    '2000-05-15', 'Robert Doe', 'Mary Doe', '9876543211', '123456789012',
    '123 Main Street, City Center', 'Maharashtra', 'Mumbai', '400001',
    'Male', 8.5, 450, 500, 90.0, 2022, 'Approved'
);

-- Insert sample student
INSERT INTO student (admission_id, student_name, course_name) VALUES
(1, 'John Doe', 'Bachelor of Business Administration');

-- Insert sample result
INSERT INTO result (
    student_id, exam_id, course_name, subject, obtain_marks, total_marks,
    grade, exam_type, cgpa, result_status
) VALUES (
    1, 1, 'Bachelor of Business Administration', 'Business Mathematics',
    85, 100, 'A', 'Semester 1', 8.5, 'Pass'
);

-- Insert sample fee record
INSERT INTO fee (
    admission_id, student_name, course_name, exam_category, amount,
    payment_method, payment_status
) VALUES (
    1, 'John Doe', 'Bachelor of Business Administration', 'Semester 1',
    1500.00, 'Online', 'Paid'
);
