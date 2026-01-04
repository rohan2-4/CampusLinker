import sqlite3

conn = sqlite3.connect('data/campus.db')
cursor = conn.cursor()

# Check exams
print('=== EXAMS IN DATABASE ===')
cursor.execute('SELECT exam_id, exam_name, subject, course_name, exam_date FROM exam')
exams = cursor.fetchall()
if exams:
    for exam in exams:
        print(f'ID: {exam[0]}, Name: {exam[1]}, Subject: {exam[2]}, Course: {exam[3]}, Date: {exam[4]}')
else:
    print('No exams found')

# Check student course
print('\n=== STUDENT INFO ===')
cursor.execute('SELECT student_id, course_name FROM student LIMIT 5')
students = cursor.fetchall()
for student in students:
    print(f'Student ID: {student[0]}, Course: {student[1]}')

conn.close()
