from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from security import hash_password, check_password 

db = SQLAlchemy()

users = []
units = []
bookings = []

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    accommodation_type = db.Column(db.String(50), nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    special_requests = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    has_vehicle = db.Column(db.Boolean, default=False)
    license_plate = db.Column(db.String(20), nullable=True)

class EnergyUsageDaily(db.Model):
    date = db.Column(db.Date, primary_key=True, nullable=False)
    average_usage_kwh = db.Column(db.Float, nullable=False)

class unit:
    def __init__(self, Unit_id, Year, Availability, Price_per_day):
        self.unit_id = Unit_id
        self.year = Year
        self.availability = Availability
        self.price_per_day = Price_per_day
    def to_dict(self):
        return {
            "unit_id": self.unit_id,
            "year": self.year,
            "availabile": self.availability, 
            "Price per day": self.price_per_day
        }
        
class Booking:
    def __init__(self, Booking_id, User_id, Unit_id, Start_date, End_date, Status="active"):
        self.booking_id = Booking_id
        self.user_id = User_id
        self.unit_id = Unit_id
        self.start_date = Start_date
        self.end_date = End_date
        self.status = Status
    def to_dict(self):
        return{
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "unit_id": self.unit_id,
            "Start Date": self.start_date,
            "End Date": self.end_date,
            "Status": self.status
            
        }
        
