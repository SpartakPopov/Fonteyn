from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify
from models import db, User, Reservation, EnergyUsageDaily
from security import hash_password, check_password
from entra_auth import (
    build_auth_url, get_token_from_code, get_user_info, 
    create_or_get_user, entra_id_required, admin_entra_id_required
)
import yaml
from datetime import datetime
import os
from functools import wraps
from energy import energy_monitor
from dotenv import load_dotenv
from urllib.parse import quote_plus
import requests
import time
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import logging

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
# Properly encode the password to handle special characters
password = quote_plus(os.getenv('DB_PASSWORD', ''))
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{password}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['ERP_URL'] = "https://erpnext-fonteyn.duckdns.org"
app.config['ERP_API_KEY'] = os.getenv('ERP_API_KEY')
app.config['ERP_API_SECRET'] = os.getenv('ERP_API_SECRET')

try:
    db.init_app(app)
except Exception as e:
    print(f"Error initializing database: {e}")
    raise

# Ensure the instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables and initial admin user
def init_db():
    """Initialize database with error handling"""
    try:
        with app.app_context():
            db.create_all()
            # Check if admin user exists
            admin = User.query.filter_by(is_admin=True).first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@fonteyn.com',
                    password=hash_password('admin123'),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                logger.info("Admin user created successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        # Don't raise the exception, just log it and continue

# Load accommodation types from YAML
with open('accommodations.yaml', 'r') as file:
    ACCOMMODATIONS = yaml.safe_load(file)

# ERPNext API POST request
def erpnext_post(endpoint, data):
    url = f"{app.config['ERP_URL']}/api/resource/{endpoint}"
    headers = {
        "Authorization": f"token {app.config['ERP_API_KEY']}:{app.config['ERP_API_SECRET']}",
        "Content-Type": "application/json"
    }
    return requests.post(url, json=data, headers=headers)


# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    try:
        return render_template('home.html')
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        return "Service is running but database is unavailable", 200

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, password=hash_password(password))
        db.session.add(user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('auth.html', active_tab='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, is_admin=False).first()
        
        if user and check_password(password, user.password):
            session['user_id'] = user.id
            flash('Login successful')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password')
    return render_template('auth.html', active_tab='login')

@app.route('/dashboard')
def dashboard():
    # Check for either traditional or Entra ID authentication
    if 'user_id' not in session and 'entra_id_user' not in session:
        return redirect(url_for('login'))
    
    # Get user from either session type
    if 'entra_id_user' in session:
        user = User.query.get(session['entra_id_user']['id'])
    else:
        user = User.query.get(session['user_id'])
    
    if not user:
        session.pop('user_id', None)
        session.pop('entra_id_user', None)
        return redirect(url_for('login'))
    
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, reservations=reservations, now=datetime.now())

@app.route('/accommodation/<type>')
def accommodation_details(type):
    if type not in ACCOMMODATIONS:
        flash('Accommodation type not found', 'error')
        return redirect(url_for('make_reservation'))
    
    accommodation = ACCOMMODATIONS[type]
    return render_template('accommodation_details.html', accommodation=accommodation)

@app.route('/booking/<type>', methods=['GET'])
def booking(type):
    # Check for either traditional or Entra ID authentication
    if 'user_id' not in session and 'entra_id_user' not in session:
        return redirect(url_for('login'))
        
    if type not in ACCOMMODATIONS:
        flash('Accommodation type not found', 'error')
        return redirect(url_for('make_reservation'))
    
    accommodation = ACCOMMODATIONS[type]
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('booking.html', 
                         accommodation=accommodation,
                         today=today)

@app.route('/make_reservation', methods=['GET', 'POST'])
def make_reservation():
    # Check for either traditional or Entra ID authentication
    if 'user_id' not in session and 'entra_id_user' not in session:
        return redirect(url_for('login'))
    
    # Get user ID from either session type
    user_id = session.get('entra_id_user', {}).get('id') or session.get('user_id')
    
    if request.method == 'POST':
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
        accommodation_type = request.form['accommodation_type']
        guests = int(request.form['guests'])
        special_requests = request.form.get('special_requests', '')
        has_vehicle = request.form['has_vehicle'] == 'yes'
        license_plate = request.form.get('license_plate') if has_vehicle else None
        
        # Validate guest count against accommodation type
        accommodation = ACCOMMODATIONS.get(accommodation_type)
        if not accommodation:
            flash('Invalid accommodation type', 'error')
            return redirect(url_for('make_reservation'))
            
        if guests > accommodation['max_guests']:
            flash(f'Maximum {accommodation["max_guests"]} guests allowed for this accommodation', 'error')
            return redirect(url_for('booking', type=accommodation_type))
        
        # Validate dates
        if check_in >= check_out:
            flash('Check-out date must be after check-in date', 'error')
            return redirect(url_for('booking', type=accommodation_type))
        
        if check_in < datetime.now().date():
            flash('Check-in date cannot be in the past', 'error')
            return redirect(url_for('booking', type=accommodation_type))
        
        reservation = Reservation(
            user_id=user_id,
            check_in=check_in,
            check_out=check_out,
            accommodation_type=accommodation_type,
            guests=guests,
            special_requests=special_requests,
            status='pending',
            has_vehicle=has_vehicle,
            license_plate=license_plate
        )
        db.session.add(reservation)
        db.session.commit()

        customer_data = {
            "customer_name": User.query.get(user_id).username,
            "customer_type": "Individual",
            "customer_group": "Individual",
            "territory": "All Territories"
        }
        
        payment_data = {
            "payment_type": "Receive",
            "party_type": "Customer",
            "party": User.query.get(user_id).username,
            "paid_amount": accommodation['price'] * (check_out - check_in).days,
            "received_amount": accommodation['price'] * (check_out - check_in).days,
            "posting_date": datetime.now().strftime('%Y-%m-%d'),
            "mode_of_payment": "Credit Card",
            "reference_no": "BOOK" + str(reservation.id),
            "reference_date": datetime.now().strftime('%Y-%m-%d'),
            "target_exchange_rate": 1,
            "paid_to": "Bank Account - FHP",
            "paid_to_account_currency": "EUR"
        }
        
        # Ignore error if customer already exists
        cust_resp = erpnext_post("Customer", customer_data)
        # Step 2: Create Payment Entry
        pay_resp = erpnext_post("Payment Entry", payment_data)
        try:
            pay_json = pay_resp.json()
        except Exception:
            pay_json = pay_resp.text
        if pay_resp.status_code in [200, 201]:
            print({"success": True}, 201)
        else:
            print({"success": False, "error": pay_json}, pay_resp.status_code)


        flash('Reservation created successfully')
        return redirect(url_for('dashboard'))
    
    # For GET requests, show the accommodation options
    return render_template('make_reservation.html', 
                         accommodations=ACCOMMODATIONS)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('entra_id_user', None)  # Clear Entra ID session
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    reservations = Reservation.query.all()
    users = User.query.all()
    return render_template('admin/dashboard.html', reservations=reservations, users=users)

@app.route('/admin/reservations/<int:id>/delete', methods=['POST'])
@admin_required
def delete_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    db.session.delete(reservation)
    db.session.commit()
    flash('Reservation deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reservations/<int:id>/update', methods=['POST'])
@admin_required
def update_reservation_status(id):
    reservation = Reservation.query.get_or_404(id)
    status = request.form.get('status')
    if status in ['pending', 'confirmed', 'cancelled']:
        reservation.status = status
        db.session.commit()
        flash('Reservation status updated successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create_admin', methods=['GET', 'POST'])
@admin_required
def create_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('create_admin'))
        
        # Generate username from email (everything before @)
        username = email.split('@')[0]
        
        user = User(username=username, email=email, password=hash_password(password), is_admin=True)
        db.session.add(user)
        db.session.commit()
        flash('Admin user created successfully')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_admin.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, is_admin=True).first()
        
        if user and check_password(password, user.password):
            session['user_id'] = user.id
            flash('Admin login successful')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials')
    return render_template('admin/login.html')

@app.route('/admin/create-reservation', methods=['GET', 'POST'])
@admin_required
def admin_create_reservation():
    if request.method == 'POST':
        # Create a new user for the guest if they don't exist
        guest_email = request.form['guest_email']
        user = User.query.filter_by(email=guest_email).first()
        
        if not user:
            user = User(
                username=request.form['guest_name'].lower().replace(' ', '_'),
                email=guest_email,
                password=hash_password('guest123'),  # Temporary password
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()
        
        # Create the reservation
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
        accommodation_type = request.form['accommodation_type']
        guests = int(request.form['guests'])
        status = request.form['status']
        has_vehicle = request.form['has_vehicle'] == 'yes'
        license_plate = request.form.get('license_plate') if has_vehicle else None
        
        reservation = Reservation(
            user_id=user.id,
            check_in=check_in,
            check_out=check_out,
            accommodation_type=accommodation_type,
            guests=guests,
            status=status,
            has_vehicle=has_vehicle,
            license_plate=license_plate
        )
        db.session.add(reservation)
        db.session.commit()
        flash('Reservation created successfully')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/create_reservation.html', accommodations=ACCOMMODATIONS)

@app.route('/energy-consumption')
def energy_consumption():
    # Check for either traditional or Entra ID authentication
    if 'user_id' not in session and 'entra_id_user' not in session:
        return redirect(url_for('login'))
    return render_template('energy_consumption.html')

@app.route('/api/energy/current')
def get_current_energy():
    # Check for either traditional or Entra ID authentication
    if 'user_id' not in session and 'entra_id_user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    current_usage = energy_monitor.update_readings()
    daily_average = energy_monitor.calculate_daily_average()
    
    return jsonify({
        'current_usage': current_usage,
        'daily_average': daily_average
    })

@app.route('/api/energy/history')
def get_energy_history():
    # Check for either traditional or Entra ID authentication
    if 'user_id' not in session and 'entra_id_user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get the last 30 days of energy usage data
    history = EnergyUsageDaily.query.order_by(EnergyUsageDaily.date.desc()).limit(30).all()
    
    # Format the data for the frontend
    data = [{
        'date': record.date.strftime('%Y-%m-%d'),
        'average_usage_kwh': record.average_usage_kwh
    } for record in reversed(history)]  # Reverse to get chronological order
    
    return jsonify(data)

# Entra ID Authentication Routes
@app.route('/admin/entra-id/login')
def entra_id_login():
    """Redirect to Microsoft Entra ID for admin authentication"""
    auth_url = build_auth_url()
    return redirect(auth_url)

@app.route('/admin/msauth')
def entra_id_callback():
    """Handle the callback from Microsoft Entra ID - Admin only"""
    error = request.args.get('error')
    if error:
        flash(f'Authentication error: {error}')
        return redirect(url_for('admin_login'))
    
    auth_code = request.args.get('code')
    if not auth_code:
        flash('No authorization code received')
        return redirect(url_for('admin_login'))
    
    # Get token from authorization code
    token_result = get_token_from_code(auth_code)
    if 'error' in token_result:
        flash(f'Token error: {token_result.get("error_description", "Unknown error")}')
        return redirect(url_for('admin_login'))
    
    # Get user information
    user_info = get_user_info(token_result['access_token'])
    if not user_info:
        flash('Failed to get user information')
        return redirect(url_for('admin_login'))
    
    # Create or get user from database
    user = create_or_get_user(user_info)
    if not user:
        flash('Failed to create or retrieve user')
        return redirect(url_for('admin_login'))
    
    # Check if user has admin privileges
    if not user.is_admin:
        flash('Access denied. Entra ID authentication is for administrators only.')
        return redirect(url_for('admin_login'))
    
    # Store user info in session
    session['entra_id_user'] = {
        'email': user.email,
        'name': user.username,
        'id': user.id
    }
    
    # Also set user_id for compatibility with existing code
    session['user_id'] = user.id
    
    flash('Entra ID admin login successful')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/entra-id/logout')
def entra_id_logout():
    """Logout from Entra ID - Admin only"""
    session.pop('entra_id_user', None)
    session.pop('user_id', None)
    flash('Admin logged out successfully')
    return redirect(url_for('admin_login'))

# Add a health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint that returns 200 if the app is running"""
    try:
        # Try to make a simple database query
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'database': 'disconnected',
            'error': str(e)
        }), 200  # Still return 200 to indicate the app is running

# Add error handlers
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return "Internal server error", 500

@app.errorhandler(503)
def service_unavailable(error):
    logger.error(f"Service unavailable: {str(error)}")
    return "Service temporarily unavailable", 503

# Modify the main execution
if __name__ == '__main__':
    try:
        # Try to initialize the database, but don't stop if it fails
        init_db()
        
        # Start the Flask application
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        # Remove the raise statement to allow the app to start even if init_db fails
        app.run(host='0.0.0.0', port=5000)  # Start the app anyway 