import os
import random
from datetime import datetime
from dotenv import load_dotenv
from models import EnergyUsageDaily, db
from flask import current_app

load_dotenv()

class EnergyMonitor:
    def __init__(self):
        self.current_usage = 0.0
        self.readings = []
        self.last_average_time = datetime.now()
        
    def get_simulated_usage(self):
        # Simulate real-time energy consumption with realistic fluctuations
        fluctuation = random.uniform(-0.5, 0.5)
        self.current_usage = max(0, self.current_usage + fluctuation)
        return round(self.current_usage, 2)
    
    def calculate_daily_average(self):
        if not self.readings:
            return 0.0
        return round(sum(self.readings) / len(self.readings), 2)
    
    def update_readings(self):
        current_usage = self.get_simulated_usage()
        self.readings.append(current_usage)
        
        # Check if 5 minutes have passed
        now = datetime.now()
        if (now - self.last_average_time).total_seconds() >= 300:  # 300 seconds = 5 minutes
            average = self.calculate_daily_average()
            self.save_daily_average(average)
            self.readings = []  # Reset readings
            self.last_average_time = now
            
        return current_usage
    
    def save_daily_average(self, average):
        try:
            with current_app.app_context():
                today = datetime.now().date()
                
                # Check if record exists for today
                existing_record = EnergyUsageDaily.query.filter_by(date=today).first()
                
                if existing_record:
                    # Update existing record
                    existing_record.average_usage_kwh = average
                else:
                    # Create new record
                    new_record = EnergyUsageDaily(
                        date=today,
                        average_usage_kwh=average
                    )
                    db.session.add(new_record)
                
                db.session.commit()
                
        except Exception as e:
            print(f"Error saving energy usage: {str(e)}")
            db.session.rollback()

# Create a global instance
energy_monitor = EnergyMonitor() 