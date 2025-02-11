# Smart Voting System Using Face Recognition and IoT

This project is a **Smart Voting System** that leverages **face recognition** and **IoT** for secure and automated voting. It ensures one person, one vote policy with real-time verification.

## Features
- **New Voter Registration**: Captures voter details including face image.
- **Face Recognition-Based Authentication**: Verifies voter identity before voting.
- **Vote Casting**: Allows registered voters to vote for a candidate.
- **Fraud Detection**: Blocks multiple voting attempts.
- **Admin Dashboard**: Secure login for managing voters.
- **Voting Results**: Displays the live voting count.

## Tech Stack
- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite3
- **Face Recognition**: OpenCV, `face_recognition` library

## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3.x
- Flask
- SQLite3
- `face_recognition`
- `opencv-python`
- `Pillow`
- `numpy`

### Steps to Run
1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/smart-voting-system.git
   cd smart-voting-system

Install dependencies:
pip install -r requirements.txt

Set up the environment:
export ADMIN_PASSWORD="your_secure_password"

Run the application:
python app.py

Open the browser and go to:
http://127.0.0.1:5000/

Project Structure
/smart-voting-system
│-- app.py              # Main application logic
│-- templates/          # HTML templates (Home, Vote, Register, Results)
│-- static/             # CSS, JavaScript, Images
│-- uploads/            # Stores voter images
│-- voter_db.sqlite     # Database for voter details
│-- votes_db.sqlite     # Database for vote counts
│-- README.md           # Project Documentation
│-- requirements.txt    # Python dependencies

API Endpoints
/ → Home page
/vote → Vote for a leader
/verify → Verify voter identity via face recognition
/admin → Admin panel for managing voters
/login → Admin login
/logout → Logout from admin session
/result → Display election results

