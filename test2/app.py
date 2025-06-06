from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from models import db, User, Reservation
from security import hash_password, check_password
import yaml
from datetime import datetime
import os
from functools import wraps
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fonteyn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['ERP_URL'] = "https://erpnext-fonteyn.duckdns.org"
app.config['ERP_API_KEY'] = "aae4c683a84e8f8"
app.config['ERP_API_SECRET'] = "196347af676879c"

db.init_app(app)

# Ensure the instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Create tables and initial admin user
def init_db():
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        # Create all tables
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
            print("Admin user created successfully!")
            print("Admin login credentials:")
            print("Email: admin@fonteyn.com")
            print("Password: admin123")

# Load accommodation types from YAML
with open('accommodations.yaml', 'r') as file:
    ACCOMMODATIONS = yaml.safe_load(file)

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
    return render_template('home.html')

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
    return render_template('register.html')

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
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, reservations=reservations)

@app.route('/accommodation/<type>')
def accommodation_details(type):
    if type not in ACCOMMODATIONS:
        flash('Accommodation type not found', 'error')
        return redirect(url_for('make_reservation'))
    
    accommodation = ACCOMMODATIONS[type]
    return render_template('accommodation_details.html', accommodation=accommodation)

@app.route('/booking/<type>', methods=['GET'])
def booking(type):
    if 'user_id' not in session:
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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
            user_id=session['user_id'],
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
        
        #The next block of code links to the ERPNext API to create a customer and a payment entry
        
        customer_data = {
            "customer_name": User.query.get(session['user_id']).username,
            "customer_type": "Individual",
            "customer_group": "Individual",
            "territory": "All Territories"
        }
        
        payment_data = {
            "payment_type": "Receive",
            "party_type": "Customer",
            "party": User.query.get(session['user_id']).username,
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

if __name__ == '__main__':
    init_db()  # Initialize database and create admin user
    app.run(debug=True) 