from flask import Flask, request, jsonify , render_template
from flask_mail import Mail, Message
from datetime import datetime
from face_recognition import detect_from_webcam
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
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


#MIGRATE SHOULD COME AFTER THE MODEL
migrate = Migrate(app,db)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/attendance')
def attendance():
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M %p")
    return render_template('attendance.html' , date = current_date , time = current_time)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/data')
def data():
    return render_template('data.html')

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
            return render_template('capture.html', student_id=student_id)
        except Exception as e:
            return f"An error occurred: {e}"
        
    return render_template('enroll.html')

@app.route('/capture/<int:student_id>' , methods=['POST'])
def capture(student_id):
    result = detect_from_webcam(student_id)
    return result

@app.route('/students')
def students():
    all_students = Student.query.all()
    return render_template('data.html', students = all_students)

@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)