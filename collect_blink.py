import serial
import csv
import time
import datetime  

COM_PORT = 'COM6'      
BAUD_RATE = 115200     
BLINK_LABEL = 2        


ser = serial.Serial(COM_PORT, BAUD_RATE)

with open('signal.csv', 'a', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)

    # Write header if the file is empty
    if csvfile.tell() == 0:
        csvwriter.writerow(['Timestamp', 'Signal', 'Label'])  

    max_duration = 300  # Duration in seconds
    start_time = time.time()

    print("Collecting blinking data... Press Ctrl+C to stop.")

    while time.time() - start_time < max_duration:
        data = ser.readline().decode("latin-1").strip()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

        values = data.split(',')

        if len(values) > 0 and values[0].isdigit():
            signal_value = int(values[0])  

            # Save only blinking data with label=2
            csvwriter.writerow([current_time, signal_value, BLINK_LABEL])  
            print(f"Saved: Time={current_time} | Signal={signal_value} | Label={BLINK_LABEL}")  

ser.close()
print("\nBlinking data collection complete and saved.")
