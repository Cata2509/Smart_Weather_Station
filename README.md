# Smart Weather Station Using Linear Regression

**SmartEnvMonitor** is a smart weather station developed for a master's dissertation project titled *"Contributions to Environmental Parameter Monitoring"*. The system uses an ESP32 microcontroller and multiple sensors to collect weather data, which is then stored, visualized, and analyzed through a Python-based web platform. The platform includes AI-based temperature prediction and weather classification features.

## Project Highlights

- Real-time monitoring of environmental parameters
- Data collection using an ESP32 and sensors (temperature, humidity, pressure, light, UV, rain)
- Local server built with Python (Flask)
- Data saved in SQLite database
- Web dashboard with live charts (Chart.js)
- AI model for weather forecasting (linear regression)
- Easy to expand and customize

## Hardware Components

- ESP32 (ESP-WROOM-32)
- DHT22 – Temperature & Humidity sensor
- BMP280 – Atmospheric pressure sensor
- BH1750 – Light intensity sensor
- YL-83 – Rain sensor
- UV Sensor – Basic UV detection
- TFT LCD 1.8" (SPI) – On-device real-time display
- Breadboard, power supply, jumper wires

## Software Stack

| Component      | Technology             |
|----------------|------------------------|
| Microcontroller Code | Arduino (C++)     |
| Web Server     | Python Flask           |
| Database       | SQLite                 |
| Frontend       | HTML, CSS, JavaScript, Chart.js |
| AI Model       | Python (scikit-learn)  |

## Features

- Live data visualization via web interface
- Real-time graphs for each environmental parameter
- CSV export for raw sensor data
- SQLite database integration
- AI-based temperature forecasting
- Weather classification (e.g., hot, rainy, sunny)
- Local-only server, but can be extended to remote access

## AI Model

- **Goal:** Predict future temperature based on historical data
- **Model:** Linear Regression (scikit-learn)
- **Training Data:** Sensor data (CSV) + historical data (Meteostat)
- **Metrics:** MAE ≈ 1.91°C, R² ≈ 0.405
- **Retraining:** Can be automated using Task Scheduler

## How to Run

1. **Flash ESP32:**
   - Upload `Disertatie.ino` to your ESP32 using Arduino IDE

2. **Set up Python server:**
   ```bash
   cd web_server
   pip install -r requirements.txt
   python app.py
