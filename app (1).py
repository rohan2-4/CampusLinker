from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database configuration - Using SQLite for easier setup
DB_PATH = 'data/campus_linker.db'

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    """Get database connection"""
    try:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row  # Enable column access by name
        return connection
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Home page with course information and login/registration"""
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM registration WHERE username = ?", (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user[2], password):  # password is at index 2
                    session['user_id'] = user[0]  # id is at index 0
                    session['username'] = user[1]  # username is at index 1
                    flash('Login successful!', 'success')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password!', 'error')
                
                cursor.close()
                conn.close()
            except Exception as e:
                flash('Database error. Please try again later.', 'error')
                print(f"Database error: {e}")
        else:
            flash('Database connection failed. Please check if MySQL is running.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email_id = request.form['email_id']
        mobile_no = request.form['mobile_no']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if username or email already exists
                cursor.execute("SELECT * FROM registration WHERE username = ? OR email_id = ?", 
                             (username, email_id))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    flash('Username or email already exists!', 'error')
                else:
                    hashed_password = generate_password_hash(password)
                    cursor.execute("""
                        INSERT INTO registration (username, password, email_id, mobile_no)
                        VALUES (?, ?, ?, ?)
                    """, (username, hashed_password, email_id, mobile_no))
                    conn.commit()
                    flash('Registration successful! Please login.', 'success')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('login'))
                
                cursor.close()
                conn.close()
            except Exception as e:
                flash('Database error. Please try again later.', 'error')
                print(f"Database error: {e}")
        else:
            flash('Database connection failed. Please check if MySQL is running.', 'error')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('home'))

@app.route('/admission', methods=['GET', 'POST'])
def admission():
    """Admission management"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle file uploads
        photo = request.files.get('photo')
        id_proof = request.files.get('id_proof')
        sign = request.files.get('sign')
        marklist = request.files.get('marklist')
        
        photo_path = id_proof_path = sign_path = marklist_path = None
        
        # Save uploaded files
        if photo and allowed_file(photo.filename):
            photo_filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            photo.save(photo_path)
        
        if id_proof and allowed_file(id_proof.filename):
            id_proof_filename = secure_filename(id_proof.filename)
            id_proof_path = os.path.join(app.config['UPLOAD_FOLDER'], id_proof_filename)
            id_proof.save(id_proof_path)
        
        if sign and allowed_file(sign.filename):
            sign_filename = secure_filename(sign.filename)
            sign_path = os.path.join(app.config['UPLOAD_FOLDER'], sign_filename)
            sign.save(sign_path)
        
        if marklist and allowed_file(marklist.filename):
            marklist_filename = secure_filename(marklist.filename)
            marklist_path = os.path.join(app.config['UPLOAD_FOLDER'], marklist_filename)
            marklist.save(marklist_path)
        
        # Get form data
        form_data = {
            'registration_id': session['user_id'],
            'student_name': request.form['student_name'],
            'course_name': request.form['course_name'],
            'email_id': request.form['email_id'],
            'date_of_birth': request.form['date_of_birth'],
            'father_name': request.form['father_name'],
            'mother_name': request.form['mother_name'],
            'mobile_no': request.form['mobile_no'],
            'aadhar_no': request.form['aadhar_no'],
            'address': request.form['address'],
            'state': request.form['state'],
            'district': request.form['district'],
            'pincode': request.form['pincode'],
            'gender': request.form['gender'],
            'previous_year_cgpa': request.form.get('previous_year_cgpa'),
            'obtain_marks': request.form.get('obtain_marks'),
            'total_marks': request.form.get('total_marks'),
            'percentage': request.form.get('percentage'),
            'passing_year': request.form.get('passing_year'),
            'photo_path': photo_path,
            'id_proof_path': id_proof_path,
            'sign_path': sign_path,
            'previous_year_marklist_path': marklist_path
        }
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO admission (
                    registration_id, student_name, course_name, email_id, date_of_birth,
                    father_name, mother_name, mobile_no, aadhar_no, address, state, district,
                    pincode, gender, previous_year_cgpa, obtain_marks, total_marks, percentage,
                    passing_year, photo_path, id_proof_path, sign_path, previous_year_marklist_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                form_data['registration_id'], form_data['student_name'], form_data['course_name'], 
                form_data['email_id'], form_data['date_of_birth'], form_data['father_name'], 
                form_data['mother_name'], form_data['mobile_no'], form_data['aadhar_no'], 
                form_data['address'], form_data['state'], form_data['district'], form_data['pincode'], 
                form_data['gender'], form_data['previous_year_cgpa'], form_data['obtain_marks'], 
                form_data['total_marks'], form_data['percentage'], form_data['passing_year'], 
                form_data['photo_path'], form_data['id_proof_path'], form_data['sign_path'], 
                form_data['previous_year_marklist_path']
            ))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Admission application submitted successfully!', 'success')
            return redirect(url_for('dashboard'))
    
    # Get courses for dropdown
    conn = get_db_connection()
    courses = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT course_name FROM course")
            raw_courses = cursor.fetchall()
            
            # Convert tuples to dictionaries for template compatibility
            for row in raw_courses:
                courses.append({'course_name': row[0]})
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching courses: {e}")
            flash('Error loading courses. Please try again later.', 'error')
    
    return render_template('admission (1).html', courses=courses)

@app.route('/fees', methods=['GET', 'POST'])
def fees():
    """Fee management"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        form_data = {
            'admission_id': request.form['admission_id'],
            'student_name': request.form['student_name'],
            'course_name': request.form['course_name'],
            'exam_category': request.form['exam_category'],
            'amount': request.form['amount'],
            'payment_method': request.form['payment_method']
        }
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fee (admission_id, student_name, course_name, exam_category, amount, payment_method)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (form_data['admission_id'], form_data['student_name'], form_data['course_name'], 
                  form_data['exam_category'], form_data['amount'], form_data['payment_method']))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Fee record added successfully!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('fees (1).html')

@app.route('/exam', methods=['GET', 'POST'])
def exam():
    """Exam management"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle exam management form submission
        pass
    
    return render_template('exam.html')

@app.route('/result')
def result():
    """Result management"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    results = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, s.student_name, s.course_name 
                FROM result r 
                JOIN student s ON r.student_id = s.student_id
            """)
            raw_results = cursor.fetchall()
            
            # Convert tuples to dictionaries for template compatibility
            for row in raw_results:
                result_dict = {
                    'result_id': row[0],
                    'student_id': row[1],
                    'exam_id': row[2],
                    'course_name': row[3],
                    'subject': row[4],
                    'obtain_marks': row[5],
                    'total_marks': row[6],
                    'grade': row[7],
                    'exam_type': row[8],
                    'cgpa': row[9],
                    'result_status': row[10],
                    'created_at': row[11],
                    'student_name': row[12] if len(row) > 12 else '',
                    'course_name_display': row[13] if len(row) > 13 else row[3]
                }
                results.append(result_dict)
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching results: {e}")
            flash('Error loading results. Please try again later.', 'error')
    
    return render_template('result.html', results=results)

@app.route('/social_activity', methods=['GET', 'POST'])
def social_activity():
    """Social activity management"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        form_data = {
            'student_id': request.form['student_id'],
            'course_name': request.form['course_name'],
            'activity_category': request.form['activity_category'],
            'activity_date': request.form['activity_date'],
            'description': request.form.get('description', '')
        }
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO social_activity (student_id, course_name, activity_category, activity_date, description)
                VALUES (?, ?, ?, ?, ?)
            """, (form_data['student_id'], form_data['course_name'], form_data['activity_category'], 
                  form_data['activity_date'], form_data['description']))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Social activity added successfully!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('social_activity (1).html')

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
