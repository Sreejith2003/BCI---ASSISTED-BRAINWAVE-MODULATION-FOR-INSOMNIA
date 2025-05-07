# Copyright (c) 2024 Umang Bansal
# 
# This software is the property of Umang Bansal. All rights reserved.
# Unauthorized copying of this file, via any medium, is strictly prohibited.
# Licensed under the MIT License. See the LICENSE file for details.

import serial
import numpy as np
from scipy import signal
import pandas as pd
import time
import pickle
import pyautogui
from collections import deque 

# -------------------- Suppress sklearn warnings -------------------- #
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

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

# -------------------- PSD Feature Calculation -------------------- #
def calculate_psd_features(segment, sampling_rate):
    f, psd_values = signal.welch(segment, fs=sampling_rate, nperseg=len(segment))
    bands = {'alpha': (8, 13), 'beta': (14, 30), 'theta': (4, 7), 'delta': (0.5, 3)}
    features = {f'E_{band}': np.sum(psd_values[(f >= low) & (f <= high)]) for band, (low, high) in bands.items()}
    features['alpha_beta_ratio'] = features['E_alpha'] / features['E_beta'] if features['E_beta'] > 0 else 0
    return features

# ---------------- Additional Feature Calculation ---------------- #
def calculate_additional_features(segment, sampling_rate):
    f, psd = signal.welch(segment, fs=sampling_rate, nperseg=len(segment))
    peak_frequency = f[np.argmax(psd)]
    spectral_centroid = np.sum(f * psd) / np.sum(psd)
    spectral_slope = np.polyfit(np.log(f[1:]), np.log(psd[1:]), 1)[0]
    return {
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

# ------------------- Main Prediction Loop ------------------- #
def main():
    ser = serial.Serial('COM6', 115200, timeout=1)  # Update COM port if needed
    clf, scaler = load_model_and_scaler()
    b_notch, a_notch, b_bandpass, a_bandpass = setup_filters(512)
    buffer = deque(maxlen=512)  

    print("Model loaded. Starting prediction...")

    while True:
        try:
            raw_data = ser.readline().decode('latin-1').strip()
            if raw_data:
                eeg_value = float(raw_data)
                buffer.append(eeg_value)

                if len(buffer) == 512:
                    # ----------------- Process and Extract Features ----------------- #
                    buffer_array = np.array(buffer)
                    processed_data = process_eeg_data(buffer_array, b_notch, a_notch, b_bandpass, a_bandpass)
                    
                    psd_features = calculate_psd_features(processed_data, 512)
                    additional_features = calculate_additional_features(processed_data, 512)
                    features = {**psd_features, **additional_features}

                    df = pd.DataFrame([features])
                    X_scaled = scaler.transform(df)
                    prediction = clf.predict(X_scaled)[0]

                    print(f"Predicted Class: {prediction}")  # ✅ Shows predicted class

                    buffer.clear()

                    # ------------------- Key Press Actions ------------------- #
                    if prediction == 0:  # Relaxation → Space key
                        pyautogui.keyDown('space')
                        time.sleep(1)
                        pyautogui.keyUp('space')

                    elif prediction == 1:  # Attention → W key
                        pyautogui.keyDown('w')
                        time.sleep(1)
                        pyautogui.keyUp('w') 

                    elif prediction == 2:  # 🚀 NEW: Blink detected → Right Arrow key
                        pyautogui.keyDown('right')
                        time.sleep(1)
                        pyautogui.keyUp('right')

        except Exception as e:
            print(f'Error: {e}')
            continue

# ---------------------------- Run Script ---------------------------- #
if __name__ == '__main__':
    main()
