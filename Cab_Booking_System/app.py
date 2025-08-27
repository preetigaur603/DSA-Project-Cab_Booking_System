from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import random # For simulated fare

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cab.db')
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), default='user') # 'user' or 'driver'
    rides = db.relationship('Ride', backref='user', lazy=True)
    payments = db.relationship('PaymentMethod', backref='user', lazy=True)
    saved_places = db.relationship('SavedPlace', backref='user', lazy=True)

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), default='driver')
    trips = db.relationship('Ride', backref='driver', lazy=True)
    earnings = db.relationship('Earning', backref='driver', lazy=True)
    current_location = db.Column(db.String(255))

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'))
    pickup_location = db.Column(db.String(255), nullable=False)
    dropoff_location = db.Column(db.String(255), nullable=False)
    pickup_time = db.Column(db.DateTime)
    fare = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')

class PaymentMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_type = db.Column(db.String(50))
    card_number = db.Column(db.String(20))
    expiry_date = db.Column(db.String(10))

class SavedPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)

class Earning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

    # Add some dummy drivers with locations if they don't exist
    if not Driver.query.first():
        driver_a_pass = generate_password_hash('drivera_pass')
        driver_a = Driver(name='Amit', email='amit@example.com', phone='9876543210',
                          license_number='DL12345', vehicle_type='Sedan', password=driver_a_pass,
                          current_location='Ghanta Ghar, Meerut')
        db.session.add(driver_a)

        driver_b_pass = generate_password_hash('driverb_pass')
        driver_b = Driver(name='Birjesh', email='birjesh@example.com', phone='9876543211',
                          license_number='DL12346', vehicle_type='SUV', password=driver_b_pass,
                          current_location='Pallavpuram, Meerut')
        db.session.add(driver_b)

        driver_c_pass = generate_password_hash('driverc_pass')
        driver_c = Driver(name='Deepak', email='deepak@example.com', phone='9876543212',
                          license_number='DL12347', vehicle_type='Hatchback', password=driver_c_pass,
                          current_location='Roorkee Road, Meerut')
        db.session.add(driver_c)

        driver_d_pass = generate_password_hash('driverc_pass')
        driver_d = Driver(name='Rahul', email='rahul@example.com', phone='9879834212',
                          license_number='DL12348', vehicle_type='SUV', password=driver_d_pass,
                          current_location='ISBT Dehradun')
        db.session.add(driver_d)

        driver_e_pass = generate_password_hash('driverc_pass')
        driver_e = Driver(name='Rohan', email='rohan@example.com', phone='9812078212',
                          license_number='DL12349', vehicle_type='Hatchback', password=driver_e_pass,
                          current_location='Haridwar Junction')
        db.session.add(driver_e)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')

        if role == 'user':
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['role'] = user.role
                return redirect(url_for('user_dashboard'))
            else:
                return render_template('login.html', error='Invalid user credentials')
        elif role == 'driver':
            driver = Driver.query.filter_by(email=email).first()
            if driver and check_password_hash(driver.password, password):
                session['driver_id'] = driver.id
                session['role'] = driver.role
                return redirect(url_for('driver_dashboard'))
            else:
                return render_template('login.html', error='Invalid driver credentials')
        else:
            return render_template('login.html', error='Please select a role')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        vehicle_type = request.form.get('vehicle_type')
        license_number = request.form.get('license_number')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        hashed_password = generate_password_hash(password)

        if role == 'user':
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return render_template('register.html', error='Email already exists')
            new_user = User(name=name, email=email, password=hashed_password, phone=phone, role='user')
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        elif role == 'driver':
            existing_driver = Driver.query.filter_by(email=email).first()
            if existing_driver:
                return render_template('register.html', error='Email already exists')
            existing_license = Driver.query.filter_by(license_number=license_number).first()
            if existing_license:
                return render_template('register.html', error='License number already exists')
            new_driver = Driver(name=name, email=email, password=hashed_password, phone=phone,
                                 vehicle_type=vehicle_type, license_number=license_number, role='driver')
            db.session.add(new_driver)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error='Please select a role')
    return render_template('register.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' in session and session['role'] == 'user':
        user = User.query.get(session['user_id'])
        rides = Ride.query.filter_by(user_id=session['user_id']).order_by(Ride.pickup_time.desc()).limit(5).all()
        saved_places = SavedPlace.query.filter_by(user_id=session['user_id']).all()
        payments = PaymentMethod.query.filter_by(user_id=session['user_id']).all()
        return render_template('user_dashboard.html', user=user, rides=rides, saved_places=saved_places, payments=payments)
    return redirect(url_for('login'))

@app.route('/driver_dashboard')
def driver_dashboard():
    if 'driver_id' in session and session['role'] == 'driver':
        driver = Driver.query.get(session['driver_id'])
        trips = Ride.query.filter_by(driver_id=session['driver_id']).order_by(Ride.pickup_time.desc()).limit(5).all()
        available_rides = Ride.query.filter_by(driver_id=None, status='pending').limit(5).all()
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        earnings_today = db.session.query(db.func.sum(Earning.amount)).filter(
            Earning.driver_id == session['driver_id'],
            db.func.date(Earning.date) == today
        ).scalar() or 0.0

        earnings_week = db.session.query(db.func.sum(Earning.amount)).filter(
            Earning.driver_id == session['driver_id'],
            Earning.date >= start_of_week,
            Earning.date <= end_of_week
        ).scalar() or 0.0

        return render_template('driver_dashboard.html', driver=driver, trips=trips, available_rides=available_rides, earnings_today=earnings_today, earnings_week=earnings_week)
    return redirect(url_for('login'))

@app.route('/api/drivers/available', methods=['POST'])
def get_available_drivers():
    # This endpoint is kept for demonstration purposes as originally provided.
    # In a real app, this would fetch drivers based on proximity to pickup_location.
    # For now, it just returns all existing drivers.
    all_drivers = Driver.query.all()
    drivers_data = [{"id": driver.id, "name": driver.name, "location": driver.current_location} for driver in all_drivers]
    return jsonify({"drivers": drivers_data})

@app.route('/api/book_ride', methods=['POST'])
def book_ride():
    if 'user_id' not in session:
        return jsonify({"message": "User not logged in"}), 401

    data = request.get_json()
    pickup_location = data.get('pickup_location')
    dropoff_location = data.get('dropoff_location')
    driver_id = data.get('driver_id')

    if not all([pickup_location, dropoff_location, driver_id]):
        return jsonify({"message": "Missing ride details"}), 400

    user = User.query.get(session['user_id'])
    driver = Driver.query.get(driver_id)

    if not user:
        return jsonify({"message": "User not found"}), 404
    if not driver:
        return jsonify({"message": "Driver not found"}), 404

    # Simulate fare calculation (e.g., based on distance or a random value)
    # For a real application, you'd calculate this based on the actual route distance
    # For now, let's just generate a random fare between 5 and 50
    fare = round(random.uniform(80, 150), 2)

    new_ride = Ride(
        user_id=user.id,
        driver_id=driver.id,
        pickup_location=pickup_location,
        dropoff_location=dropoff_location,
        pickup_time=datetime.utcnow(),
        fare=fare,
        status='booked'
    )
    db.session.add(new_ride)

    # Add an earning record for the driver
    new_earning = Earning(
        driver_id=driver.id,
        amount=fare * 0.8 # Driver gets 80% of the fare, for example
    )
    db.session.add(new_earning)

    db.session.commit()

    return jsonify({
        "message": "Ride booked successfully!",
        "ride_id": new_ride.id,
        "driver_name": driver.name,
        "fare": new_ride.fare
    }), 200

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('driver_id', None)
    session.pop('role', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)