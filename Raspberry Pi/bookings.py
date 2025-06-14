from models import SessionLocal, Licenses
import datetime

def check_plate(license):
    session = SessionLocal()
    plate = session.query(Licenses).filter_by(license=license).first()
    if plate is None:
        print(f"License plate {license} not found in database.")
        session.close()
        return
    
    today = datetime.date.today()
    check_in = plate.check_in
    if check_in is None:
        print("No check-in date recorded for this license plate.")
    else:
        if hasattr(check_in, "date"):
            check_in = check_in.date()
        if today == check_in:
            print(f"License plate: {license} checked in! ")
        elif today > check_in:
            print(f"License plate: {license} checked in! ")
        else:
            print(f"License plate: {license} isn't supposed to check-in!!! ")
    session.close()
