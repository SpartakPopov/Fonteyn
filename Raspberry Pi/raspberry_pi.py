import cv2
import subprocess
import datetime
import os

# Path to save the log file
LOG_FILE = "plate_log.txt"

# Create a temporary file to store each captured frame
frame_path = "/tmp/frame.jpg"

# Start streaming video for debuging using libcamera
camera_stream_command = "libcamera-vid -t 0 --inline --listen -o tcp://0.0.0.0:8888 > /dev/null 2>&1 &"
os.system(camera_stream_command)

print("Starting license plate recognition...")

while True:
    # Capture frame using libcamera-still
    os.system(f"libcamera-still -o {frame_path} --immediate --nopreview")

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
        result = subprocess.run(
            ["alpr", "-c", "eu","-n", "1", frame_path],
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()

# Check if a plate was detected
        if "plate0:" in output:
            lines = output.split("\n")
            for line in lines:
                if line.strip().startswith("-"):
                    plate_number = line.strip().split()[1]
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"{timestamp} - Plate detected: {plate_number}"
                    print("LOG: ", log_entry)

                    # Append to log file
                    with open(LOG_FILE, "a") as log_file:
                        log_file.write(log_entry + "\n")

    except Exception as e:
        print("Error running ALPR:", e)