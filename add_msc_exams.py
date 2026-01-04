import sqlite3

DB_PATH = 'data/campus_linker.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check existing exams
print("Current exams for M.Sc:")
cursor.execute('SELECT exam_id, exam_name, subject, course_name FROM exam WHERE course_name = "M.Sc"')
existing = cursor.fetchall()
if existing:
    for exam in existing:
        print(f'  ID: {exam[0]}, Name: {exam[1]}, Subject: {exam[2]}, Course: {exam[3]}')
else:
    print("  No exams found for M.Sc")

# Delete any existing M.Sc exams first to avoid duplicates
cursor.execute('DELETE FROM exam WHERE course_name = "M.Sc"')
conn.commit()
print("\nCleared existing M.Sc exams")

# Insert M.Sc exams
msc_exams = [
    ('Midterm Exam 2025', 'Physics', 'Midterm', 'M.Sc', '2025-03-17', '09:00', 180, 100, 'Bring calculator and ID card'),
    ('Midterm Exam 2025', 'Chemistry', 'Midterm', 'M.Sc', '2025-03-18', '10:00', 180, 100, 'No electronic devices allowed'),
    ('Final Exam 2025', 'Advanced Mathematics', 'Final', 'M.Sc', '2025-05-21', '14:00', 180, 100, 'Open book exam'),
    ('Final Exam 2025', 'Quantum Mechanics', 'Final', 'M.Sc', '2025-05-22', '14:00', 180, 100, 'Bring scientific calculator'),
]

cursor.executemany('''
    INSERT INTO exam (exam_name, subject, exam_type, course_name, exam_date, exam_time, duration, max_marks, instructions)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', msc_exams)
conn.commit()
print(f"✅ Added {len(msc_exams)} exams for M.Sc course")

# Verify insertion
cursor.execute('SELECT exam_id, exam_name, subject, course_name FROM exam WHERE course_name = "M.Sc"')
result = cursor.fetchall()
print("\nNew M.Sc exams:")
for exam in result:
    print(f'  ID: {exam[0]}, Name: {exam[1]}, Subject: {exam[2]}, Course: {exam[3]}')

conn.close()
print("\n✅ Database update completed!")
