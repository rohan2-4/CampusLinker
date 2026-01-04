from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import secrets
import sqlite3
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database configuration - Using SQLite
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'campus_linker.db')

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    """Get database connection"""
    try:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_course_fee_table():
    """Ensure the course_fee table exists and seed minimal defaults if empty."""
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS course_fee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                fee_category TEXT NOT NULL,
                amount REAL NOT NULL
            )
            """
        )

        # Seed defaults per course and ensure missing combinations are filled
        try:
            cursor.execute("SELECT course_name FROM course")
            courses = [row[0] for row in cursor.fetchall()]
        except Exception:
            courses = []

        default_amounts = {
            'Admission Fee': 5000.0,
            'Tuition Fee': 20000.0,
            'Exam Fee': 1500.0,
            'Library Fee': 500.0,
            'Hostel Fee': 15000.0,
            'Other Fee': 0.0,
        }

        # Always make sure GENERIC fallback exists
        targets = list({c for c in courses if c}) if courses else []
        targets.append('GENERIC')

        for course_name in targets:
            for category, amt in default_amounts.items():
                cursor.execute(
                    """
                    SELECT 1 FROM course_fee
                    WHERE UPPER(course_name) = UPPER(?) AND UPPER(fee_category) = UPPER(?)
                    LIMIT 1
                    """,
                    (course_name, category),
                )
                if cursor.fetchone():
                    continue
                cursor.execute(
                    "INSERT INTO course_fee (course_name, fee_category, amount) VALUES (?, ?, ?)",
                    (course_name, category, amt),
                )

        conn.commit()
    except Exception as e:
        print(f"Error ensuring course_fee table: {e}")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

def get_or_create_student_details(registration_id: int):
    """Fetch student details for a user, create record from latest admission if missing."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.student_id, s.course_name
            FROM student s
            JOIN admission a ON s.admission_id = a.admission_id
            WHERE a.registration_id = ?
            ORDER BY s.student_id DESC
            LIMIT 1
            """,
            (registration_id,),
        )
        row = cursor.fetchone()
        if row:
            return {'student_id': row[0], 'course_name': row[1]}

        cursor.execute(
            """
            SELECT admission_id, student_name, course_name
            FROM admission
            WHERE registration_id = ?
            ORDER BY admission_id DESC
            LIMIT 1
            """,
            (registration_id,),
        )
        admission_row = cursor.fetchone()
        if not admission_row:
            return None

        cursor.execute(
            """
            INSERT INTO student (admission_id, student_name, course_name)
            VALUES (?, ?, ?)
            """,
            (admission_row[0], admission_row[1], admission_row[2]),
        )
        conn.commit()
        return {
            'student_id': cursor.lastrowid,
            'course_name': admission_row[2],
        }
    except Exception as e:
        print(f"Error fetching/creating student details: {e}")
        return None
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

def get_fee_amount_for_course(course_name: str, fee_category: str):
    """Lookup the fee amount for a given course and category. Falls back to GENERIC if present."""
    course_name = (course_name or '').strip()
    fee_category = (fee_category or '').strip()
    if not course_name or not fee_category:
        return None
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        # Exact course match
        cursor.execute(
            """
            SELECT amount FROM course_fee
            WHERE UPPER(course_name) = UPPER(?) AND UPPER(fee_category) = UPPER(?)
            LIMIT 1
            """,
            (course_name, fee_category),
        )
        row = cursor.fetchone()
        if row:
            return float(row[0])
        # Fallback to GENERIC
        cursor.execute(
            """
            SELECT amount FROM course_fee
            WHERE UPPER(course_name) = 'GENERIC' AND UPPER(fee_category) = UPPER(?)
            LIMIT 1
            """,
            (fee_category,),
        )
        row = cursor.fetchone()
        if row:
            return float(row[0])
        return None
    except Exception as e:
        print(f"Error fetching fee amount: {e}")
        return None
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

def get_user_role(user_id):
    """Get user role from database"""
    conn = get_db_connection()
    if not conn:
        return 'student'
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM registration WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 'student'
    except Exception as e:
        print(f"Error getting user role: {e}")
        return 'student'
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        
        user_role = get_user_role(session['user_id'])
        if user_role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """Decorator to require student role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        
        user_role = get_user_role(session['user_id'])
        if user_role != 'student':
            flash('This page is for students only.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM registration WHERE username = ?", (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user[2], password):
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['role'] = user[5]  # Store role in session
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
            flash('Database connection failed.', 'error')
    
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form['email']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM registration WHERE email_id = ?", (email,))
                user = cursor.fetchone()
                
                if user:
                    # In a real application, you would send an email with a reset link
                    # For now, we'll just show a success message
                    flash('If an account with that email exists, a password reset link has been sent.', 'info')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('login'))
                else:
                    flash('No account found with that email address.', 'error')
                
                cursor.close()
                conn.close()
            except Exception as e:
                flash('Database error. Please try again later.', 'error')
                print(f"Database error: {e}")
        else:
            flash('Database connection failed.', 'error')
    
    return render_template('forgot_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email_id = request.form['email_id']
        mobile_no = request.form['mobile_no']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM registration WHERE username = ? OR email_id = ?", 
                             (username, email_id))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    flash('Username or email already exists!', 'error')
                else:
                    hashed_password = generate_password_hash(password)
                    cursor.execute("""
                        INSERT INTO registration (username, password, email_id, mobile_no, role)
                        VALUES (?, ?, ?, ?, 'student')
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
            flash('Database connection failed.', 'error')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('home'))

@app.route('/admission', methods=['GET', 'POST'])
@student_required
def admission():
    """Admission management"""
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
            
            # Insert admission record
            cursor.execute("""
                INSERT INTO admission (
                    registration_id, student_name, course_name, email_id, date_of_birth,
                    father_name, mother_name, mobile_no, aadhar_no, address, state, district,
                    pincode, gender, previous_year_cgpa, obtain_marks, total_marks, percentage,
                    passing_year, photo_path, id_proof_path, sign_path, previous_year_marklist_path, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Submitted')
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
            
            # Get the last inserted admission_id
            admission_id = cursor.lastrowid
            
            # Create student record automatically
            cursor.execute("""
                INSERT INTO student (admission_id, student_name, course_name)
                VALUES (?, ?, ?)
            """, (admission_id, form_data['student_name'], form_data['course_name']))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Admission application submitted successfully! Student record created. Please complete fee payment.', 'success')
            return redirect(url_for('fees'))
    
    # Get courses for dropdown
    conn = get_db_connection()
    courses = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT course_name FROM course")
            raw_courses = cursor.fetchall()
            
            for row in raw_courses:
                courses.append({'course_name': row[0]})
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching courses: {e}")
            flash('Error loading courses. Please try again later.', 'error')
    
    return render_template('admission (1).html', courses=courses)

@app.route('/fees', methods=['GET', 'POST'])
@student_required
def fees():
    """Fee management"""
    # Get user's admission details automatically
    conn = get_db_connection()
    admission_details = None
    fee_details = None
    fee_paid = False
    total_fee = 0.0
    
    if conn:
        try:
            cursor = conn.cursor()
            # Get the latest admission for this user
            cursor.execute("""
                SELECT a.admission_id, a.student_name, a.course_name 
                FROM admission a 
                WHERE a.registration_id = ? 
                ORDER BY a.admission_id DESC LIMIT 1
            """, (session['user_id'],))
            
            admission_row = cursor.fetchone()
            if admission_row:
                admission_details = {
                    'admission_id': admission_row[0],
                    'student_name': admission_row[1],
                    'course_name': admission_row[2]
                }
                
                # Calculate total fee for all categories
                fee_categories = ['Admission Fee', 'Tuition Fee', 'Exam Fee', 'Library Fee', 'Hostel Fee', 'Other Fee']
                for category in fee_categories:
                    amount = get_fee_amount_for_course(admission_details['course_name'], category)
                    if amount:
                        total_fee += float(amount)
                
                # Check if fee has been paid for this admission
                cursor.execute("""
                    SELECT * FROM fee 
                    WHERE admission_id = ? AND payment_status = 'Completed'
                """, (admission_details['admission_id'],))
                
                fee_row = cursor.fetchone()
                if fee_row:
                    fee_paid = True
                    fee_details = {
                        'fee_id': fee_row[0],
                        'amount': float(fee_row[5]) if fee_row[5] else 0.0,
                        'payment_method': fee_row[6],
                        'payment_date': fee_row[8],
                        'total_fee': float(fee_row[4]) if fee_row[4] else 0.0
                    }
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching admission details: {e}")
    
    # Handle POST request - process payment
    if request.method == 'POST':
        if fee_paid:
            flash('Fee already paid for this admission!', 'error')
            return redirect(url_for('fees'))
        
        form_data = {
            'admission_id': int(request.form['admission_id']),
            'student_name': request.form['student_name'],
            'course_name': request.form['course_name'],
            'total_fee': float(total_fee),
            'payment_method': request.form['payment_method']
        }
        
        if form_data['total_fee'] <= 0:
            flash('Unable to calculate total fee amount for this course.', 'error')
            return redirect(url_for('fees'))

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Insert fee record with completed status
                cursor.execute("""
                    INSERT INTO fee (admission_id, student_name, course_name, total_fee, amount, payment_method, payment_status, payment_date)
                    VALUES (?, ?, ?, ?, ?, ?, 'Completed', datetime('now'))
                """, (
                    form_data['admission_id'], 
                    form_data['student_name'], 
                    form_data['course_name'], 
                    form_data['total_fee'], 
                    form_data['total_fee'], 
                    form_data['payment_method']
                ))
                
                # Update admission status to 'Completed'
                cursor.execute("""
                    UPDATE admission SET status = 'Completed' 
                    WHERE admission_id = ?
                """, (form_data['admission_id'],))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                flash('Fee payment completed successfully! Admission process finished.', 'success')
                return redirect(url_for('fees'))
            except Exception as e:
                print(f"Error processing fee payment: {e}")
                flash(f'Error processing payment: {str(e)}', 'error')
                return redirect(url_for('fees'))
    
    return render_template('fees (1).html', 
                         admission_details=admission_details, 
                         fee_details=fee_details,
                         fee_paid=fee_paid,
                         total_fee=float(total_fee))

@app.route('/api/fee_amount')
def api_fee_amount():
    """Return JSON with fee amount for a given course and category."""
    if 'user_id' not in session:
        return jsonify({ 'error': 'Unauthorized' }), 401
    course_name = request.args.get('course_name', '')
    fee_category = request.args.get('fee_category', '')
    amount = get_fee_amount_for_course(course_name, fee_category)
    if amount is None:
        return jsonify({ 'found': False }), 200
    return jsonify({ 'found': True, 'amount': amount }), 200

@app.route('/download_fee_receipt/<int:admission_id>')
def download_fee_receipt(admission_id):
    """Download fee receipt as PDF"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Create receipts directory if it doesn't exist
    receipts_dir = 'receipts'
    os.makedirs(receipts_dir, exist_ok=True)
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Get fee details
            cursor.execute("""
                SELECT f.fee_id, f.admission_id, f.student_name, f.course_name, 
                       f.total_fee, f.amount, f.payment_method, f.payment_status, f.payment_date
                FROM fee f 
                WHERE f.admission_id = ? AND f.payment_status = 'Completed'
                LIMIT 1
            """, (admission_id,))
            
            fee_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if fee_data:
                # Safely convert fee amounts to float
                total_fee_amount = float(fee_data[4]) if fee_data[4] else 0.0
                amount_paid = float(fee_data[5]) if fee_data[5] else 0.0
                
                # Create PDF file path
                pdf_file_path = f"{receipts_dir}/receipt_{admission_id}.pdf"
                
                # Create PDF document
                doc = SimpleDocTemplate(pdf_file_path, pagesize=letter,
                                      rightMargin=0.5*inch, leftMargin=0.5*inch,
                                      topMargin=0.5*inch, bottomMargin=0.5*inch)
                
                # Container for PDF elements
                story = []
                
                # Define styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor=colors.HexColor('#1a237e'),
                    spaceAfter=6,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold'
                )
                
                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontSize=11,
                    textColor=colors.HexColor('#1a237e'),
                    spaceAfter=10,
                    spaceBefore=10,
                    alignment=TA_LEFT,
                    fontName='Helvetica-Bold',
                    borderPadding=5
                )
                
                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.black,
                    alignment=TA_LEFT
                )
                
                # Header
                story.append(Paragraph("CAMPUS LINKER", title_style))
                story.append(Paragraph("Skylink Institute of ACS", styles['Normal']))
                story.append(Spacer(1, 0.15*inch))
                
                # Receipt Title
                story.append(Paragraph("FEE RECEIPT", ParagraphStyle(
                    'ReceiptTitle',
                    parent=styles['Heading2'],
                    fontSize=16,
                    textColor=colors.HexColor('#1a237e'),
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold'
                )))
                story.append(Spacer(1, 0.1*inch))
                
                # Receipt Info Table
                receipt_info_data = [
                    ['Receipt No:', str(fee_data[0]), 'Date:', fee_data[8] if fee_data[8] else 'N/A'],
                    ['Admission ID:', str(fee_data[1]), '', '']
                ]
                
                receipt_info_table = Table(receipt_info_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.5*inch])
                receipt_info_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
                ]))
                story.append(receipt_info_table)
                story.append(Spacer(1, 0.15*inch))
                
                # Student Details Section
                story.append(Paragraph("STUDENT DETAILS", heading_style))
                student_data = [
                    ['Student Name:', fee_data[2]],
                    ['Course Name:', fee_data[3]]
                ]
                
                student_table = Table(student_data, colWidths=[2*inch, 4*inch])
                student_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ]))
                story.append(student_table)
                story.append(Spacer(1, 0.15*inch))
                
                # Payment Details Section
                story.append(Paragraph("PAYMENT DETAILS", heading_style))
                payment_data = [
                    ['Total Fee Amount:', f"Rs. {total_fee_amount:,.2f}"],
                    ['Amount Paid:', f"Rs. {amount_paid:,.2f}"],
                    ['Payment Method:', fee_data[6]],
                    ['Payment Status:', fee_data[7]]
                ]
                
                payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
                payment_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ]))
                story.append(payment_table)
                story.append(Spacer(1, 0.15*inch))
                
                # Fee Breakdown Section
                story.append(Paragraph("FEE BREAKDOWN", heading_style))
                breakdown_data = [
                    ['Fee Category', 'Amount'],
                    ['Admission Fee', 'Rs. 5,000.00'],
                    ['Tuition Fee', 'Rs. 20,000.00'],
                    ['Exam Fee', 'Rs. 1,500.00'],
                    ['Library Fee', 'Rs. 500.00'],
                    ['Hostel Fee', 'Rs. 15,000.00'],
                    ['Other Fee', 'Rs. 0.00'],
                    ['TOTAL', f'Rs. {total_fee_amount:,.2f}']
                ]
                
                breakdown_table = Table(breakdown_data, colWidths=[3*inch, 3*inch])
                breakdown_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff3cd')),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
                ]))
                story.append(breakdown_table)
                story.append(Spacer(1, 0.2*inch))
                
                # Terms & Conditions
                story.append(Paragraph("TERMS & CONDITIONS", heading_style))
                terms_text = """
                <b>1.</b> This receipt is valid only with the official seal of the institute.<br/>
                <b>2.</b> Please keep this receipt for future reference.<br/>
                <b>3.</b> In case of any discrepancy, please contact the finance office immediately.<br/>
                <b>4.</b> The fee is non-refundable once paid.
                """
                story.append(Paragraph(terms_text, normal_style))
                story.append(Spacer(1, 0.15*inch))
                
                # Contact Information
                story.append(Paragraph("CONTACT INFORMATION", heading_style))
                contact_text = """
                <b>Institution:</b> Skylink Institute of ACS<br/>
                <b>Phone:</b> +91-7385326615<br/>
                <b>Email:</b> info@skylink.edu<br/>
                <b>Address:</b> Skylink Institute, College Campus
                """
                story.append(Paragraph(contact_text, normal_style))
                story.append(Spacer(1, 0.2*inch))
                
                # Footer
                footer_text = "Thank you for your payment!"
                story.append(Paragraph(footer_text, ParagraphStyle(
                    'FooterStyle',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.HexColor('#1a237e'),
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold'
                )))
                
                story.append(Spacer(1, 0.1*inch))
                generated_date = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                story.append(Paragraph(generated_date, ParagraphStyle(
                    'DateStyle',
                    parent=styles['Normal'],
                    fontSize=8,
                    textColor=colors.grey,
                    alignment=TA_CENTER
                )))
                
                # Build PDF
                doc.build(story)
                
                return send_file(pdf_file_path, as_attachment=True, download_name=f"receipt_{admission_id}.pdf")
            else:
                flash('Fee payment record not found for this admission!', 'error')
                return redirect(url_for('fees'))
                
        except Exception as e:
            print(f"Error generating receipt: {e}")
            flash(f'Error generating receipt: {str(e)}', 'error')
            return redirect(url_for('fees'))
    
    flash('Database connection failed.', 'error')
    return redirect(url_for('fees'))

@app.route('/exam', methods=['GET', 'POST'])
@student_required
def exam():
    """Student exam form submission"""
    # Prefill student details for the logged-in user
    student_details = get_or_create_student_details(session['user_id'])
    exams_grouped = {}
    available_exams = []

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            exam_query = """
                SELECT exam_id, exam_name, subject, exam_type, exam_date, exam_time,
                       duration, max_marks, course_name
                FROM exam
            """
            params = ()
            if student_details:
                exam_query += " WHERE course_name = ? ORDER BY exam_name ASC, exam_date ASC"
                params = (student_details['course_name'],)
            else:
                exam_query += " ORDER BY exam_name ASC, exam_date ASC"

            cursor.execute(exam_query, params)
            rows = cursor.fetchall()
            
            # Group exams by exam_name
            for exam_row in rows:
                exam_dict = {
                    'exam_id': exam_row[0],
                    'exam_name': exam_row[1],
                    'subject': exam_row[2],
                    'exam_type': exam_row[3],
                    'exam_date': exam_row[4],
                    'exam_time': exam_row[5],
                    'duration': exam_row[6],
                    'max_marks': exam_row[7],
                    'course_name': exam_row[8],
                }
                available_exams.append(exam_dict)
                
                exam_name = exam_row[1]
                if exam_name not in exams_grouped:
                    exams_grouped[exam_name] = {
                        'exam_name': exam_name,
                        'exam_type': exam_row[3],
                        'subjects': []
                    }
                
                exams_grouped[exam_name]['subjects'].append(exam_dict)
        except Exception as e:
            print(f"Error preparing exam page: {e}")
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    if request.method == 'POST':
        selected_exam_id = request.form.get('exam_id')
        student_id = request.form.get('student_id')

        if not selected_exam_id or not student_id:
            flash('Please select an exam before submitting the form.', 'error')
            return redirect(url_for('exam'))

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed.', 'error')
            return redirect(url_for('exam'))

        try:
            cursor = conn.cursor()

            # Ensure the student belongs to the logged-in user
            cursor.execute(
                """
                SELECT s.student_id, s.course_name
                FROM student s
                JOIN admission a ON s.admission_id = a.admission_id
                WHERE s.student_id = ? AND a.registration_id = ?
                """,
                (student_id, session['user_id']),
            )
            verified_student = cursor.fetchone()
            if not verified_student:
                flash('Invalid student information.', 'error')
                return redirect(url_for('exam'))

            cursor.execute(
                """
                SELECT exam_id, exam_name, subject, exam_type, exam_date, max_marks, course_name
                FROM exam
                WHERE exam_id = ?
                """,
                (selected_exam_id,),
            )
            exam_row = cursor.fetchone()
            if not exam_row:
                flash('Selected exam not found.', 'error')
                return redirect(url_for('exam'))

            cursor.execute(
                """
                SELECT 1 FROM result
                WHERE student_id = ? AND exam_id = ?
                """,
                (student_id, selected_exam_id),
            )
            if cursor.fetchone():
                flash('You have already submitted the exam form for this exam.', 'info')
                return redirect(url_for('result'))

            cursor.execute(
                """
                INSERT INTO result (
                    student_id, exam_id, course_name, subject, obtain_marks, total_marks,
                    grade, exam_type, cgpa, result_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    selected_exam_id,
                    exam_row[6],
                    exam_row[2],
                    0,
                    exam_row[5] or 0,
                    '',
                    exam_row[3],
                    None,
                    'Pending',
                ),
            )
            conn.commit()
            flash('Exam form submitted successfully. Status: Pending.', 'success')
        except Exception as e:
            print(f"Error submitting exam form: {e}")
            flash('Error submitting exam form. Please try again.', 'error')
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

        return redirect(url_for('result'))

    return render_template(
        'exam.html',
        student_details=student_details,
        available_exams=available_exams,
    )

@app.route('/admin/exams', methods=['GET', 'POST'])
@admin_required
def admin_exams():
    """Admin exam management - create and manage exams"""
    if request.method == 'POST':
        # Get base exam info
        exam_name = request.form.get('exam_name')
        exam_type = request.form.get('exam_type')
        course_name = request.form.get('course_name')
        instructions = request.form.get('instructions', '')
        
        # Get subject data (can be multiple subjects)
        subjects = request.form.getlist('subject[]')
        exam_dates = request.form.getlist('exam_date[]')
        exam_times = request.form.getlist('exam_time[]')
        durations = request.form.getlist('duration[]')
        max_marks_list = request.form.getlist('max_marks[]')
        
        if not exam_name or not exam_type or not course_name or not subjects:
            flash('Please fill in all required fields and add at least one subject.', 'error')
            return redirect(url_for('admin_exams'))
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                exam_count = 0
                
                # Insert exam for each subject
                for i, subject in enumerate(subjects):
                    if not subject:  # Skip empty subject rows
                        continue
                    
                    exam_date = exam_dates[i] if i < len(exam_dates) else ''
                    exam_time = exam_times[i] if i < len(exam_times) else ''
                    duration = durations[i] if i < len(durations) else 0
                    max_marks = max_marks_list[i] if i < len(max_marks_list) else 0
                    
                    if not exam_date or not exam_time or not duration or not max_marks:
                        continue
                    
                    cursor.execute("""
                        INSERT INTO exam (exam_name, subject, exam_type, course_name, exam_date, 
                                        exam_time, duration, max_marks, instructions, exam_fee)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (
                        exam_name, subject, exam_type, course_name, exam_date, exam_time,
                        duration, max_marks, instructions
                    ))
                    exam_count += 1
                
                if exam_count > 0:
                    conn.commit()
                    flash(f'Exam "{exam_name}" with {exam_count} subject(s) created successfully!', 'success')
                else:
                    flash('No valid subjects added. Please check your data.', 'error')
            except Exception as e:
                flash(f'Error creating exam: {e}', 'error')
                print(f"Error creating exam: {e}")
            finally:
                cursor.close()
                conn.close()
        
        return redirect(url_for('admin_exams'))
    
    # Get all exams grouped by exam_name for display
    conn = get_db_connection()
    exams_grouped = {}
    courses = []
    if conn:
        try:
            cursor = conn.cursor()
            # Get all exams
            cursor.execute("""
                SELECT exam_id, exam_name, subject, exam_type, exam_date, exam_time, 
                       duration, max_marks, course_name, instructions
                FROM exam 
                ORDER BY exam_name DESC, exam_date DESC
            """)
            
            for row in cursor.fetchall():
                exam_dict = dict(row)
                exam_name = exam_dict['exam_name']
                
                if exam_name not in exams_grouped:
                    exams_grouped[exam_name] = {
                        'exam_name': exam_name,
                        'exam_type': exam_dict['exam_type'],
                        'course_name': exam_dict['course_name'],
                        'instructions': exam_dict['instructions'],
                        'subjects': []
                    }
                
                exams_grouped[exam_name]['subjects'].append({
                    'exam_id': exam_dict['exam_id'],
                    'subject': exam_dict['subject'],
                    'exam_date': exam_dict['exam_date'],
                    'exam_time': exam_dict['exam_time'],
                    'duration': exam_dict['duration'],
                    'max_marks': exam_dict['max_marks']
                })
            
            # Get courses for dropdown
            cursor.execute("SELECT course_name FROM course")
            courses = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching exams: {e}")
        finally:
            cursor.close()
            conn.close()
    
    exams = list(exams_grouped.values())
    return render_template('admin_exams.html', exams=exams, courses=courses)

@app.route('/result')
@student_required
def result():
    """Student view - only see their own results"""
    conn = get_db_connection()
    results = []
    if conn:
        try:
            cursor = conn.cursor()
            # Only show results for the current student
            cursor.execute("""
                SELECT r.*, s.student_name, e.exam_name
                FROM result r 
                JOIN student s ON r.student_id = s.student_id
                JOIN admission a ON s.admission_id = a.admission_id
                LEFT JOIN exam e ON r.exam_id = e.exam_id
                WHERE a.registration_id = ?
                ORDER BY r.created_at DESC
            """, (session['user_id'],))
            
            results = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching student results: {e}")
            flash('Error loading results. Please try again later.', 'error')
    
    return render_template('result.html', results=results, user_role='student')

@app.route('/admin/results', methods=['GET', 'POST'])
@admin_required
def admin_results():
    """Admin result management - view and manage all results"""
    if request.method == 'POST':
        # Update result
        result_id = request.form.get('result_id')
        obtain_marks = request.form.get('obtain_marks')
        result_status = request.form.get('result_status')
        grade = request.form.get('grade')
        cgpa = request.form.get('cgpa')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE result 
                    SET obtain_marks = ?, result_status = ?, grade = ?, cgpa = ?
                    WHERE result_id = ?
                """, (obtain_marks, result_status, grade, cgpa, result_id))
                conn.commit()
                flash('Result updated successfully!', 'success')
            except Exception as e:
                flash(f'Error updating result: {e}', 'error')
            finally:
                cursor.close()
                conn.close()
    
    # Get all results
    conn = get_db_connection()
    results = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, s.student_name, s.course_name, e.exam_name
                FROM result r 
                JOIN student s ON r.student_id = s.student_id
                LEFT JOIN exam e ON r.exam_id = e.exam_id
                ORDER BY r.created_at DESC
            """)
            results = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching results: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('admin_results.html', results=results)

@app.route('/api/result/<int:result_id>')
@admin_required
def api_get_result(result_id):
    """API to get result data for editing"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT result_id, obtain_marks, result_status, grade, cgpa
            FROM result WHERE result_id = ?
        """, (result_id,))
        result = cursor.fetchone()
        
        if result:
            return jsonify(dict(result))
        else:
            return jsonify({'error': 'Result not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/analysis')
def analysis():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    line_labels = []
    line_values = []
    hist_labels = [
        '0-50%', '50-60%', '60-70%', '70-80%', '80-90%', '90-100%'
    ]
    hist_values = [0, 0, 0, 0, 0, 0]
    pie_labels = ['Pass', 'Fail']
    pie_values = [0, 0]

    if conn:
        try:
            cursor = conn.cursor()
            # Fetch result rows to build datasets in Python for flexibility
            cursor.execute(
                """
                SELECT obtain_marks, total_marks, result_status,
                       COALESCE(created_at, datetime('now')) as created_at
                FROM result
                """
            )
            rows = cursor.fetchall()

            # Build line chart: results count per day (last 365 days)
            from datetime import datetime as dt, timedelta
            today = dt.utcnow().date()
            last_days = [today - timedelta(days=i) for i in range(364, -1, -1)]
            per_day_counts = {d.strftime('%Y-%m-%d'): 0 for d in last_days}
            for r in rows:
                created_at = r[3]
                try:
                    date_key = dt.fromisoformat(str(created_at)).date().strftime('%Y-%m-%d')
                except Exception:
                    # Fallback: try parsing common SQLite format 'YYYY-MM-DD HH:MM:SS'
                    try:
                        date_key = dt.strptime(str(created_at), '%Y-%m-%d %H:%M:%S').date().strftime('%Y-%m-%d')
                    except Exception:
                        date_key = today.strftime('%Y-%m-%d')
                if date_key in per_day_counts:
                    per_day_counts[date_key] += 1

            line_labels = list(per_day_counts.keys())
            line_values = list(per_day_counts.values())

            # Histogram: percentage buckets
            for r in rows:
                obtain = r[0]
                total = r[1]
                try:
                    obtain_f = float(obtain) if obtain is not None else None
                    total_f = float(total) if total is not None else None
                except Exception:
                    obtain_f = None
                    total_f = None
                if obtain_f is None or total_f in (None, 0):
                    continue
                percent = (obtain_f / total_f) * 100.0
                if percent < 50:
                    hist_values[0] += 1
                elif percent < 60:
                    hist_values[1] += 1
                elif percent < 70:
                    hist_values[2] += 1
                elif percent < 80:
                    hist_values[3] += 1
                elif percent < 90:
                    hist_values[4] += 1
                else:
                    hist_values[5] += 1

            # Pie: pass vs fail using result_status
            for r in rows:
                status = (r[2] or '').strip().lower()
                if status == 'pass':
                    pie_values[0] += 1
                elif status == 'fail':
                    pie_values[1] += 1

            cursor.close()
            conn.close()
        except Exception as e:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
            print(f"Error building analysis data: {e}")

    return render_template(
        'analysis.html',
        line_labels=line_labels,
        line_values=line_values,
        hist_labels=hist_labels,
        hist_values=hist_values,
        pie_labels=pie_labels,
        pie_values=pie_values,
    )

@app.route('/social_activity', methods=['GET', 'POST'])
def social_activity():
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


def ensure_sample_exams():
    """Ensure sample exams exist for all courses"""
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        
        # Check if M.Sc exams exist
        cursor.execute("SELECT COUNT(*) FROM exam WHERE course_name = 'M.Sc'")
        if cursor.fetchone()[0] == 0:
            # Insert M.Sc sample exams
            sample_exams = [
                ('Midterm Exam 2025', 'Physics', 'Midterm', 'M.Sc', '2025-03-17', '09:00', 180, 100, 'Bring calculator and ID card'),
                ('Midterm Exam 2025', 'Chemistry', 'Midterm', 'M.Sc', '2025-03-18', '10:00', 180, 100, 'No electronic devices allowed'),
                ('Final Exam 2025', 'Advanced Mathematics', 'Final', 'M.Sc', '2025-05-21', '14:00', 180, 100, 'Open book exam'),
                ('Final Exam 2025', 'Quantum Mechanics', 'Final', 'M.Sc', '2025-05-22', '14:00', 180, 100, 'Bring scientific calculator'),
            ]
            
            cursor.executemany('''
                INSERT INTO exam (exam_name, subject, exam_type, course_name, exam_date, exam_time, duration, max_marks, instructions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_exams)
            conn.commit()
            print("✅ Added sample exams for M.Sc course")
    except Exception as e:
        print(f"Error ensuring sample exams: {e}")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Create receipts directory if it doesn't exist
    os.makedirs('receipts', exist_ok=True)
    # Ensure course_fee table exists and has defaults
    ensure_course_fee_table()
    # Ensure sample exams exist
    ensure_sample_exams()
    app.run(debug=True)