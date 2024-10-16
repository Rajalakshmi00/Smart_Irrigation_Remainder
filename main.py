from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import requests
from twilio.rest import Client
from flask_cors import CORS
import os

app = Flask("Smart Irrigation Reminder System")
CORS(app, supports_credentials=True)
# Secret key for session management (required by Flask to manage sessions)
app.config['SECRET_KEY'] = '80d8c33887dcae114f255dbc33291d206a062bdab5781b08'

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Twilio configuration
TWILIO_ACCOUNT_SID = 'AC840cebb71958e4411da1837e7e8fb9da'
TWILIO_AUTH_TOKEN = '61892ee535efc09150771944fd800a0c'
TWILIO_PHONE_NUMBER = '+16062684835'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
global_phone_number = None
# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    location = db.Column(db.String(100), nullable=False)

# Initialize the database
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Smart Irrigation Reminder System"
@app.before_request
def make_session_permanent():
    session.permanent = True
# User registration route
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    phone_number = data['phone_number']
    location = data['location']

    if not phone_number or not location:
        return jsonify({"message": "Phone number and location are required!"}), 400
    
    # Check if user already exists
    user = User.query.filter_by(phone_number=phone_number).first()
    if user:
        return jsonify({"message": "User already registered!"}), 400

    new_user = User(phone_number=phone_number, location=location)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 200

# User login route
@app.route('/login', methods=['POST'])
def login():
    global global_phone_number
    data = request.json
    phone_number = data.get('phone_number')  # Using get to avoid KeyError
    user = User.query.filter_by(phone_number=phone_number).first()
    
    if user:
        # Store phone number in session on successful login
        global_phone_number = phone_number
        return jsonify({
            "success": True,
            "message": "Login successful!",
            "user": {"phone_number": user.phone_number, "location": user.location}
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": "User not found. Please register first."
        }), 404

# Fetch weather data
def get_weather_data(location):
    api_key = "c6a03522ccfc48e9b7e9596e61f32450"
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        return None
    data = response.json()
    
    # Extract first forecast data
    if 'list' in data and len(data['list']) > 0:
        return data['list'][0]
    else:
        return None

def check_irrigation_remainder(soil_moisture, upcoming_rainfall):
    moisture_threshold = 30
    if soil_moisture < moisture_threshold and upcoming_rainfall == 0:
        return "Time to irrigate your crops!"
    return "No irrigation needed right now"

#user logout route
@app.route('/logout', methods=['POST'])
def logout():
    if 'phone_number' not in session:
        return jsonify({"message": "You are not logged in."}), 403
    
    phone_number = session['phone_number']
    user = User.query.filter_by(phone_number=phone_number).first()

    if not user:
        return jsonify({"message": "User not found."}), 404
    
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "Logout successful, and user data deleted"}), 200

# Set reminder and send SMS
@app.route('/set_reminder', methods=['POST'])
def set_reminder():
    global global_phone_number  # Declare the variable as global to access it

    if global_phone_number is None:
        return jsonify({"message": "You need to log in first."}), 403

    # Retrieve user info from the database using the global phone number
    user = User.query.filter_by(phone_number=global_phone_number).first()
    
    if not user:
        return jsonify({"message": "User not found."}), 404

    # Get the soil moisture from the user input
    data = request.json
    soil_moisture = data.get('soil_moisture')

    if soil_moisture is None:
        return jsonify({"message": "Soil moisture data is required."}), 400

    try:
        # Use user's location for weather data
        location = user.location
        print(f"Fetching weather data for location: {location}")

        # Fetch weather data using the user's location
        weather_data = get_weather_data(location)
        if not weather_data:
            return jsonify({"message": "Failed to fetch weather data."}), 400

        # Extract upcoming rainfall data
        upcoming_rainfall = weather_data.get('rain', {}).get('3h', 0)

        # Check if irrigation is needed based on soil moisture and rainfall forecast
        reminder_message = check_irrigation_remainder(soil_moisture, upcoming_rainfall)

        # Send SMS reminder to the user's phone number
        client.messages.create(
            body=reminder_message,
            from_=TWILIO_PHONE_NUMBER,
            to=global_phone_number
        )

        return jsonify({"message": "SMS reminder sent!", "reminder": reminder_message}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "An error occurred while setting the reminder."}), 500




if __name__ == '__main__':
    app.run(debug=True)
