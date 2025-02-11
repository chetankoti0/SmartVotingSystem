from flask import Flask, request, render_template, jsonify, redirect, url_for, session
import sqlite3
import os
import face_recognition
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import logging

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATABASE1 = 'voter_db.sqlite'
DATABASE2 = 'votes_db.sqlite'

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.ERROR)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Use environment variable for admin password
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'SUPER@1')

# Helper function to execute queries
def execute_query(db_name, query, params=()):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(query, params)
        if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            conn.commit()
        results = cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        results = []
    finally:
        conn.close()
    return results

# Initialize databases with proper schema
def initialize_databases():
    execute_query(DATABASE1, """CREATE TABLE IF NOT EXISTS voters (
                                voter_id TEXT PRIMARY KEY,
                                name TEXT,
                                age INTEGER,
                                photo TEXT DEFAULT NULL,
                                failedAttempts INT DEFAULT 0,
                                voted BOOLEAN DEFAULT 0)""")
    execute_query(DATABASE2, """CREATE TABLE IF NOT EXISTS leaders (
                                leader_name TEXT PRIMARY KEY,
                                votes INTEGER DEFAULT 0)""")
    leaders = execute_query(DATABASE2, "SELECT * FROM leaders WHERE leader_name IN ('PK', 'CN')")
    if len(leaders) < 2:
        execute_query(DATABASE2, "INSERT INTO leaders (leader_name, votes) VALUES ('PK', 0), ('CN', 0)")

# Run the database initialization
initialize_databases()

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/vote', methods=['GET', 'POST'])
def cast_vote():
    if request.method == 'GET':
        return render_template('vote.html')
    
    voter_id = request.form.get('voter_id')
    leader_name = request.form.get('leader_name')

    if not voter_id or not leader_name:
        return jsonify({"message": "Voter ID and Leader selection are required"}), 400

    voter = execute_query(DATABASE1, "SELECT * FROM voters WHERE voter_id = ?", (voter_id,))

    if not voter:
        return jsonify({"message": "Voter not found"}), 404

    if voter[0][4] >= 3:  # Assuming column 5 stores 'failed_attempts'
        return jsonify({"message": "Fraud detected! Too many failed attempts."}), 403

    if voter[0][5]:  # Assuming column 4 stores 'voted'
        return jsonify({"message": "You have already voted"}), 403

    execute_query(DATABASE2, "UPDATE leaders SET votes = votes + 1 WHERE leader_name = ?", (leader_name,))
    execute_query(DATABASE1, "UPDATE voters SET voted = 1 WHERE voter_id = ?", (voter_id,))
    return jsonify({"message": "Vote cast successfully!"}), 200



@app.route('/verify', methods=['POST'])
def verify_voter():
    data = request.json
    voter_id = data.get('voter_id')
    photo_data = data.get('photo')

    if not voter_id or not voter_id.isalnum() or not photo_data:
        return jsonify({"error": "Invalid or missing Voter ID and Photo"}), 400

    try:
        uploaded_image = decode_base64_image(photo_data)
        voter = execute_query(DATABASE1, "SELECT * FROM voters WHERE voter_id = ?", (voter_id,))

        if not voter or voter[0][4]:  # Check if voter exists and has not already voted
            return jsonify({"error": "You have already voted or voter not found"}), 403

        stored_image_path = voter[0][3]
        if not stored_image_path or not os.path.exists(stored_image_path):
            return jsonify({"error": "Stored photo not found. Contact admin."}), 400

        stored_image = face_recognition.load_image_file(stored_image_path)
        stored_encoding = face_recognition.face_encodings(stored_image)
        uploaded_encoding = face_recognition.face_encodings(uploaded_image)

        if stored_encoding and uploaded_encoding:
            if face_recognition.compare_faces([stored_encoding[0]], uploaded_encoding[0], tolerance=0.2)[0]:
                leaders = execute_query(DATABASE2, "SELECT * FROM leaders")
                return jsonify({"message": "Verification successful", "leaders": leaders}), 200
            else:
                return jsonify({"error": "Face verification failed. Please try again."}), 403
        else:
            return jsonify({"error": "Face encoding could not be detected. Ensure the image is clear."}), 400
    except Exception as e:
        logging.error(f"Error during verification: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    if not session.get('authenticated'):
        return redirect(url_for('login', next='/admin'))
    
    if request.method == 'POST':
        data = request.json
        voter_id = data.get('voter_id')
        name = data.get('name')
        age = data.get('age')
        photo_data = data.get('photo')

        if not voter_id or not name or not age or not photo_data:
            return "All fields are required.", 400

        existing_voter = execute_query(DATABASE1, "SELECT * FROM voters WHERE voter_id = ?", (voter_id,))
        if existing_voter:
            return "Voter already registered.", 400

        photo_filename = f"{voter_id}.png"
        photo_filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
        with open(photo_filepath, "wb") as photo_file:
            photo_file.write(base64.b64decode(photo_data.split(",")[1]))

        execute_query(DATABASE1, "INSERT INTO voters (voter_id, name, age, photo, failedAttempts, voted) VALUES (?, ?, ?, ?, ?, ?)",
              (voter_id, name, age, photo_filepath, 0, 0))
        return "Registration successful.", 200

    return render_template('new_registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        next_page = request.args.get('next', '/')
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            session.permanent = True
            return redirect(next_page)
        else:
            return "Invalid password. Try again.", 403
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/result', methods=['GET'])
def show_results():
    leaders = execute_query(DATABASE2, "SELECT leader_name, votes FROM leaders")
    return render_template('result.html', leaders=leaders)

def decode_base64_image(base64_str):
    if "," not in base64_str:
        raise ValueError("Invalid base64 format")
    try:
        img_data = base64.b64decode(base64_str.split(",")[1])
        img = Image.open(BytesIO(img_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return np.array(img)
    except Exception as e:
        logging.error(f"Failed to decode image: {e}")
        raise ValueError("Invalid image format")

if __name__ == '__main__':
    app.run(debug=True)
