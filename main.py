from flask import Flask, request , render_template , flash , redirect, url_for
from flask_mail import Mail, Message
from datetime import datetime
from face_utils import detect_from_webcam , mark_attendance
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash , check_password_hash
import os

app = Flask(__name__)

load_dotenv()  # load variables from .env

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Configure the SQLite database
app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)


# Define the Student model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    course = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(150))  # for storing captured image path

#Define the Admin model
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

#MIGRATE SHOULD COME AFTER THE MODEL
migrate = Migrate(app,db)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/attendance')
def attendance():
    current_date = datetime.now().strftime("%d-%m-%Y")
    current_time = datetime.now().strftime("%H:%M %p")
    return render_template('attendance.html' , date = current_date , time = current_time)


# Route: Handle form submission
@app.route('/enroll' , methods=['GET', 'POST'])
def enroll():
    if request.method == 'POST':
        full_name = request.form['fullName']
        dob = request.form['dob']
        gender = request.form['gender']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        course = request.form['course']

        # Create and save to DB
        new_student = Student(
            full_name=full_name,
            dob=dob,
            gender=gender,
            email=email,
            phone=phone,
            address=address,
            course=course
        )

        try:
            db.session.add(new_student)
            db.session.commit()
            student_id = new_student.id  # generated ID

            # Send confirmation email
            msg = Message("Enrollment Confirmation",
                          recipients=[email])
            msg.body = f'''Hello {full_name},

Your enrollment was successful!

Here are your details:
- Full Name: {full_name}
- Date of Birth: {dob}
- Gender: {gender}
- Email: {email}
- Phone: {phone}
- Address: {address}
- Course: {course}

Thank you for registering with us.

Best regards,
Attendance System Admin
'''
            mail.send(msg)
            
            # Redirect to capture face page with student_id
            return render_template('capture.html', student_id=student_id , student_name = full_name)
        except Exception as e:
            return f"An error occurred: {e}"
        
    return render_template('enroll.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if admin already exists
        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            flash( "Admin already exists. Please login.")
            return render_template('login.html') 
        
        # Create new admin
        hashed_password = generate_password_hash(password)
        new_admin = Admin(email = email , password_hash = hashed_password)
        try:
            db.session.add(new_admin)
            db.session.commit()
            return render_template('login.html', message="Admin created successfully. Please login.")
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template('signup.html')


@app.route('/login' , methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if admin exists
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password_hash, password):
                return redirect(url_for('data'))  # redirect to data route
        else:
            print("No admin found with that email")
        
        flash("Invalid credentials. Please try again.")
        return render_template('login.html')
    return render_template('login.html')


@app.route('/capture/<int:student_id>/<student_name>' , methods=['POST'])
def capture(student_id , student_name):
    result = detect_from_webcam(student_id , student_name)
    return result


@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/mark_attendance' , methods = ['GET'])
def mark_attendance_route():
    result  = mark_attendance()
    return render_template('attendance_result.html', result=result)


@app.route('/data')
def data():
    return render_template('data.html' , students = Student.query.all())

##  Delete all data from the admin table
# with app.app_context() :
#     db.session.query(Admin).delete()
#     db.session.commit()

# # Delete all data from the student table
# with app.app_context():
#     db.session.query(Student).delete()
#     db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)