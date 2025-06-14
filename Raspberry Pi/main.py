import cv2
import subprocess
import datetime
import os
import threading
import schedule
import subprocess
from models import sync_database
from bookings import check_plate
import time

def check_plates(plate):
    check_plate(license=plate)

def sync_db():
    print("Running data synchronization...")
    success =sync_database()
    if success == False:
        print("Failed to synchronize database!")
def plate_detection_loop():
    while True:
        frame_path = "/tmp/frame.jpg"

        # Start streaming video for debuging using libcamera
        camera_stream_command = "libcamera-vid -t 0 --inline --listen -o tcp://0.0.0.0:8888 > /dev/null 2>&1 &"
        os.system(camera_stream_command)

        print("Starting license plate recognition...")

        while True:
            # Capture frame using libcamera-still
            with open("libcamera_errors.log", "a") as errlog:
                subprocess.run(
                    ["libcamera-still", "-o", frame_path, "--immediate", "--nopreview"],
                    stdout=subprocess.DEVNULL,  # discard standard output
                    stderr=errlog               # save error output to a file
                )

            # Load the captured frame
            frame = cv2.imread(frame_path)

            # Check if the frame was successfully captured
            if frame is None:
                print("Failed to capture frame.")
                continue

            # Preprocess image (convert to grayscale, increase contrast)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
            contrast = cv2.equalizeHist(gray)  # Enhance contrast

            # Save the processed frame
            cv2.imwrite(frame_path, contrast)

            # Run OpenALPR on the processed frame
            try:
                with open("alpr_errors.log", "a") as errlog:
                    result = subprocess.run(
                        ["alpr", "-c", "eu", "-n", "1", frame_path],
                        stdout=subprocess.PIPE,
                        stderr=errlog,
                        text=True
                    )
                output = result.stdout.strip()

        # Check if a plate was detected
                if "plate0:" in output:
                    lines = output.split("\n")
                    for line in lines:
                        if line.strip().startswith("-"):
                            plate_number = line.strip().split()[1]
                            plate_number = plate_number.lower()
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            log_entry = f"{timestamp} - Plate detected: {plate_number}"
                            print("LOG: ", log_entry)
                            data = {
                                "plate": plate_number
                            }
                            if plate_number:
                                check_plates(plate=plate_number)

            except Exception as e:
                print("Error running ALPR:", e)

schedule.every(10).seconds.do(sync_db)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=run_scheduler, daemon=True).start()
    plate_detection_loop()