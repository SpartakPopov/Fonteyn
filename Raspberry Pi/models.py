from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import mysql.connector
from dotenv import load_dotenv
import os
load_dotenv()

# Create engine and base
engine = create_engine('sqlite:///license-plate.db', echo=True)
Base = declarative_base()

# Define your model
class Licenses(Base):
    __tablename__ = 'licenses'

    id = Column(Integer, primary_key=True)
    license = Column(String)
    booked = Column(Boolean)
    check_in = Column(Date)
    check_out = Column(Date)

# Create tables
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(bind=engine)

def new_plate(license, check_in=None, check_out=None):
    session = SessionLocal()
    plate = Licenses(
        license=license,
        check_in=check_in,
        check_out=check_out
    )
    session.add(plate)
    session.commit()
    session.close()

# Connect to Azure MySQL Flexible Server
conn = mysql.connector.connect(
    host= os.getenv('DB_HOST'),
    user= os.getenv('DB_USER'),
    password= os.getenv('DB_PASSWORD'),
    database= os.getenv('DB_NAME')
)

cursor = conn.cursor()

# Run your query
cursor.execute("SELECT license_plate, check_in, check_out FROM reservation;")

# Fetch all rows
license_plates = cursor.fetchall()

# Clean up
cursor.close()
conn.close()

for plate in license_plates:
    new_plate(*plate)