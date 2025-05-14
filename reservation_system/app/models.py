from .security import hash_password, check_password 

users = []
reservations = []
bookings = []

class User:
    def __init__(self, User_id, Name, Password, Email, Birth_Date):
        self.id = User_id
        self.name = Name
        self.password = hash_password(Password) 
        self.email = Email
        self.birth_date = Birth_Date
        self.rental_history = [] 
    
    def to_dict(self):
        return{
            "id": self.id,
            "Name": self.name,
            "Password": self.password,
            "Email": self.email,
            "Date of Birth": self.birth_date
        }
    def update_profile(self, new_name=None, new_email=None, new_password=None):
        if new_name:
            self.name = new_name
        if new_email:
            self.email = new_email
        if new_password:
            self.password = hash_password(new_password)
    def verify_password(self, password):
        return check_password(password, self.password)

    def add_rental(self, Reservation_id, start_date, end_date):
        rental_record = {
            "reservation_id": Reservation_id,
            "start_date": start_date,
            "end_date": end_date,
            "status": "active"
        }
        self.rental_history.append(rental_record)
        
class Reservations:
    def __init__(self, Reservation_id, Year, Availability, Price_per_day):
        self.reservation_id = Reservation_id
        self.year = Year
        self.availability = Availability
        self.price_per_day = Price_per_day
    def to_dict(self):
        return {
            "reservation_id": self.reservation_id,
            "year": self.year,
            "availabile": self.availability, 
            "Price per day": self.price_per_day
        }
        
class Booking:
    def __init__(self, Booking_id, User_id, Reservation_id, Start_date, End_date, Status="active"):
        self.booking_id = Booking_id
        self.user_id = User_id
        self.reservation_id = Reservation_id
        self.start_date = Start_date
        self.end_date = End_date
        self.status = Status
    def to_dict(self):
        return{
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "reservation_id": self.reservation_id,
            "Start Date": self.start_date,
            "End Date": self.end_date,
            "Status": self.status
            
        }
        
