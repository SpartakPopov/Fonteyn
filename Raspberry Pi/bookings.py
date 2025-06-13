from models import SessionLocal, Licenses
import json
import datetime
# Open and load the JSON file
with open('data.json', 'r') as f:
    data = json.load(f)

# Extract variables
time = datetime.date()
plate = data['plate']

def check_plate(license, time):
    session = SessionLocal()
    plate = session.query(Licenses).filter_by(license=True).first()
    session.close()
    if plate == True:
        return("License found!")

    else:
        return("License not found!")