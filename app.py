from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message

app = Flask(__name__)

# Flask-Mail setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rishavmitra187@gmail.com'  # Replace with your Gmail address
app.config['MAIL_PASSWORD'] = 'wlkp wceo rhtx txwp'  # Replace with your Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'rishavmitra187@gmail.com'  # Same as the username

mail = Mail(app)

# Configurations for file uploads
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Folder to store uploaded files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max upload size (16MB)
app.secret_key = 'your_secret_key_here'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed file extensions for uploads

# Sample in-memory data to hold grievances (replaceable with a database later)
grievances = []
resolved_grievances = 0
feedbacks = []  # To store feedback temporarily

# Chatbot responses (extendable to integrate with an AI system or predefined rules)
chatbot_responses = {
    "hello": "Hi! How can I help you with your grievance today?",
    "grievance": "You can submit a grievance through the 'Add Grievance' section.",
    "status": "You can check the status of your grievance in the user dashboard once logged in.",
    "feedback": "You can leave feedback via the 'User Feedback' section."
}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_grievance_notification(email, title):
    """Send email notification to the user after submitting a grievance."""
    try:
        msg = Message("Grievance Submitted Successfully", recipients=[email])
        msg.body = f"Dear user,\n\nYour grievance titled '{title}' has been successfully submitted. We will review it and get back to you shortly.\n\nThank you for using our grievance redressal system."
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        flash(f"An error occurred while sending the email: {e}")

def send_resolution_notification(email, title):
    """Send email notification to the user when the grievance is resolved."""
    try:
        msg = Message("Grievance Resolved", recipients=[email])
        msg.body = f"Dear user,\n\nYour grievance titled '{title}' has been resolved. Thank you for your patience.\n\nBest regards,\nGrievance Redressal Team"
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        flash(f"An error occurred while sending the resolution email: {e}")

@app.route('/')
def index():
    # Render the index page and pass the grievances list to display them
    return render_template('index.html', grievances=grievances)

# Handle the chatbot interaction (GET for displaying, POST for processing messages)
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    response = ""
    user_message = ""
    
    if request.method == 'POST':
        user_message = request.form['user_message'].lower()
        response = chatbot_responses.get(user_message, "I'm sorry, I didn't understand that. Can you please rephrase?")
    
    return render_template('chatbot.html', user_message=user_message, response=response)

# Handle the admin login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simple hardcoded login check (replace with database logic as needed)
        if username == "admin" and password == "admin123":
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials, please try again.")
    
    return render_template('login.html')

# Admin dashboard to show total and resolved grievances
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    total_grievances = len(grievances)
    resolved_grievances = sum(1 for grievance in grievances if grievance.get('resolved'))
    
    if request.method == 'POST':
        grievance_id = int(request.form['grievance_id'])
        for grievance in grievances:
            if grievance['id'] == grievance_id:
                grievance['resolved'] = True
                # Send notification to the user when the grievance is resolved
                send_resolution_notification(grievance['email'], grievance['title'])
                break
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin.html', 
                           total_grievances=total_grievances, 
                           resolved_grievances=resolved_grievances, 
                           grievances=grievances, 
                           feedbacks=feedbacks)

# Add grievance page (for users to submit grievances)
@app.route('/add_grievance', methods=['GET', 'POST'])
def add_grievance():
    if request.method == 'POST':
        title = request.form['grievance_title']
        description = request.form['grievance_description']
        email = request.form['email']
        grievance_id = len(grievances) + 1
        attachment = request.files['attachment']  # Get the attached file if any

        # Handle file upload
        filepath = None
        if attachment and allowed_file(attachment.filename):
            filename = secure_filename(attachment.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            attachment.save(filepath)
        elif attachment and not allowed_file(attachment.filename):
            flash("Unsupported file format! Please upload an image file (png, jpg, jpeg, gif).")
            return redirect(request.url)
        
        grievances.append({
            'id': grievance_id,
            'title': title,
            'description': description,
            'email': email,
            'attachment': filepath,
            'resolved': False
        })
        
        # Send email notification
        send_grievance_notification(email, title)

        return redirect(url_for('submission_success'))
    
    return render_template('add_grievance.html')

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Success page after submitting a grievance
@app.route('/submission_success')
def submission_success():
    return render_template('submission_success.html')

# User feedback page
@app.route('/user_feedback', methods=['GET', 'POST'])
def user_feedback():
    if request.method == 'POST':
        feedback = request.form['feedback']
        feedbacks.append(feedback)
        return redirect(url_for('user_feedback_success'))
    return render_template('user_feedback.html')

# Feedback submission success page
@app.route('/user_feedback_success')
def user_feedback_success():
    return render_template('user_feedback_success.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Create upload folder if it doesn't exist
    app.run(debug=True)

