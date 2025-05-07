import serial
import csv
import time
import datetime  

COM_PORT = 'COM6'  # Replace with your Arduino's COM port
BAUD_RATE = 115200  # Must match the Arduino's BAUD_RATE

# ---------------------- Added: Prompt to select data type ---------------------- #
# New addition: Prompt user to choose data type for labeling
print("Select the data type to collect:")
print("0 - Relaxation | 1 - Attention | 2 - Blinking")  # Updated: Added blinking option
label = input("Enter the label number (0/1/2): ")        # Added line

# Validate user input
if label not in ['0', '1', '2']:                          # Added validation
    print("Invalid input! Please restart and enter 0, 1, or 2.")
    exit()

# ---------------------- Original Code ---------------------- #
ser = serial.Serial(COM_PORT, BAUD_RATE)

with open('signal.csv', 'a', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)

    # ---------------------- Added: CSV header check ---------------------- #
    if csvfile.tell() == 0:                                # Added: Write header if file is empty
        csvwriter.writerow(['Timestamp', 'Signal', 'Label'])  

    max_duration = 300  # Duration in seconds
    start_time = time.time()

    print("Collecting data... Press Ctrl+C to stop.")

    while time.time() - start_time < max_duration:
        data = ser.readline().decode("latin-1").strip()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

        values = data.split(',')

        # ---------------------- Updated: Data validation and saving ---------------------- #
        if len(values) > 0 and values[0].isdigit():
            signal_value = int(values[0])  # Original: Signal value from Arduino

            # Updated: Save selected label along with signal and timestamp
            csvwriter.writerow([current_time, signal_value, label])  # Updated line
            print(f"Saved: Time={current_time} | Signal={signal_value} | Label={label}")  # Updated line

ser.close()
print("\nData collection complete and saved.")
