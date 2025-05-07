import serial
import numpy as np
from scipy import signal
import pandas as pd
import pickle
import pyautogui
from collections import deque
import time

# ------------------------- Filter Setup ------------------------- #
def setup_filters(sampling_rate):
    b_notch, a_notch = signal.iirnotch(50.0 / (0.5 * sampling_rate), 30.0)
    b_bandpass, a_bandpass = signal.butter(4, [0.5 / (0.5 * sampling_rate), 30.0 / (0.5 * sampling_rate)], 'band')
    return b_notch, a_notch, b_bandpass, a_bandpass

# --------------------- EEG Data Processing --------------------- #
def process_eeg_data(data, b_notch, a_notch, b_bandpass, a_bandpass):
    data = signal.filtfilt(b_notch, a_notch, data)
    data = signal.filtfilt(b_bandpass, a_bandpass, data)
    return data

# ---------------- PSD & Additional Feature Calculation ---------------- #
def extract_features(segment, sampling_rate):
    f, psd_values = signal.welch(segment, fs=sampling_rate, nperseg=len(segment))

    # PSD features
    E_alpha = np.sum(psd_values[(f >= 8) & (f <= 13)])
    E_beta = np.sum(psd_values[(f >= 14) & (f <= 30)])
    E_theta = np.sum(psd_values[(f >= 4) & (f <= 7)])
    E_delta = np.sum(psd_values[(f >= 0.5) & (f <= 3)])
    alpha_beta_ratio = E_alpha / E_beta if E_beta > 0 else 0

    # Additional features
    peak_frequency = f[np.argmax(psd_values)]
    spectral_centroid = np.sum(f * psd_values) / np.sum(psd_values) if np.sum(psd_values) > 0 else 0
    spectral_slope = np.polyfit(np.log(f[1:]), np.log(psd_values[1:]), 1)[0] if np.all(psd_values[1:] > 0) else 0

    return {
        'E_alpha': E_alpha,
        'E_beta': E_beta,
        'E_theta': E_theta,
        'E_delta': E_delta,
        'alpha_beta_ratio': alpha_beta_ratio,
        'peak_frequency': peak_frequency,
        'spectral_centroid': spectral_centroid,
        'spectral_slope': spectral_slope
    }

# ------------------- Load Model and Scaler ------------------- #
def load_model_and_scaler():
    with open('updated_model.pkl', 'rb') as f:
        clf = pickle.load(f)
    with open('updated_scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    return clf, scaler

# ------------------- Blink Prediction Loop with 2-Second Gap ------------------- #
def main():
    ser = serial.Serial('COM6', 115200, timeout=1)  # Update COM port if needed
    clf, scaler = load_model_and_scaler()
    b_notch, a_notch, b_bandpass, a_bandpass = setup_filters(512)
    buffer = deque(maxlen=512)

    last_blink_time = 0  # Track last blink detection time
    blink_gap = 5       # Minimum gap between blinks (seconds)

    print("👁️ Predicting blinks with a 2-second gap... (Press Ctrl+C to stop)")

    while True:
        try:
            raw_data = ser.readline().decode('latin-1').strip()
            if raw_data:
                buffer.append(float(raw_data))

                if len(buffer) == 512:
                    processed_data = process_eeg_data(np.array(buffer), b_notch, a_notch, b_bandpass, a_bandpass)
                    features = extract_features(processed_data, 512)

                    # Maintain correct feature order
                    feature_order = ['E_alpha', 'E_beta', 'E_theta', 'E_delta', 'alpha_beta_ratio', 
                                     'peak_frequency', 'spectral_centroid', 'spectral_slope']
                    df = pd.DataFrame([[features[col] for col in feature_order]], columns=feature_order)

                    X_scaled = scaler.transform(df)
                    prediction = clf.predict(X_scaled)[0]

                    current_time = time.time()
                    if prediction == 2:  # Blink detected
                        if current_time - last_blink_time >= blink_gap:
                            print("👁️ Blink detected!")
                            pyautogui.press('right')  # Simulate right arrow key press
                            last_blink_time = current_time
                        else:
                            print("⏳ Blink ignored (waiting for gap)")

                    buffer.clear()

        except Exception as e:
            print(f'⚠️ Error: {e}')
            continue

# ---------------------------- Run Script ---------------------------- #
if __name__ == '__main__':
    main()
