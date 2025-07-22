from flask import Flask, request, jsonify, render_template, send_file, request
import sqlite3
import os
from datetime import datetime
import pickle
import pandas as pd

app = Flask(__name__)

# === Încărcare model AI ===
with open("model_tmax.pkl", "rb") as f:
    ai_model = pickle.load(f)

# === Constante pentru clasificare atmosferică ===
THRESHOLD_RAIN_ANALOG = 80
THRESHOLD_LIGHT_LEVEL = 20


# === Clasificare atmosferică ===
def classify_weather_type(light_level, rain_analog, rain_status, hour):
    if 22 <= hour or hour < 6:
        return "Noapte"
    if rain_analog < THRESHOLD_RAIN_ANALOG or rain_status.lower() == "plouă":
        return "Zi ploioasă"
    elif light_level <= THRESHOLD_LIGHT_LEVEL:
        return "Zi înnorată"
    else:
        return "Zi însorită"


# === Inițializare DB ===
def init_db():
    connection = sqlite3.connect("weather_station.db")
    cursor = connection.cursor()

    # Verifică dacă tabelul există deja
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='sensor_data'
    """)
    table_exists = cursor.fetchone()

    if not table_exists:
        cursor.execute("""
            CREATE TABLE sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                humidity REAL,
                temperature REAL,
                uvValue INTEGER,
                rainStatus TEXT,
                rainAnalogValue INTEGER,
                lightLevel REAL,
                pressure REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                timestamp_iso TEXT,
                hour INTEGER,
                day_of_week TEXT,
                predicted_temp REAL,
                weather_class TEXT,
                weather_type TEXT
            )
        """)
        connection.commit()

    connection.close()


# === Salvare în DB + AI + clasificare ===
def save_to_database(humidity, temperature, uvValue, rainStatus, rainAnalogValue, lightLevel, pressure):
    now = datetime.now()
    timestamp_iso = now.isoformat()
    hour = now.hour
    day_of_week = now.strftime("%A")  # ex: Monday
    day_num = now.weekday()  # Monday = 0

    # === AI: Predicție temperatură maximă ===
    try:
        predicted_temp = ai_model.predict([[pressure, 0.0, day_num]])[0]
    except Exception as e:
        print("Eroare la predicția AI:", e)
        predicted_temp = None

    # === Clasificare termică ===
    if predicted_temp is not None:
        if predicted_temp > 25:
            weather_class = "Zi călduroasă"
        elif predicted_temp > 10:
            weather_class = "Zi moderată"
        else:
            weather_class = "Zi rece"
    else:
        weather_class = None

    # === Clasificare atmosferică ===
    weather_type = classify_weather_type(light_level=lightLevel, rain_analog=rainAnalogValue, rain_status=rainStatus,
                                         hour=hour)

    # === Salvare în baza de date ===
    connection = sqlite3.connect("weather_station.db")
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO sensor_data (
            humidity, temperature, uvValue, rainStatus, rainAnalogValue,
            lightLevel, pressure, timestamp_iso, hour, day_of_week,
            predicted_temp, weather_class, weather_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        humidity, temperature, uvValue, rainStatus, rainAnalogValue,
        lightLevel, pressure, timestamp_iso, hour, day_of_week,
        predicted_temp, weather_class, weather_type
    ))
    connection.commit()
    connection.close()


# === Endpoint de recepție ESP32 ===
@app.route("/data", methods=["POST"])
def receive_data():
    data = request.json
    humidity = data.get("humidity")
    temperature = data.get("temperature")
    uvValue = data.get("uvValue")
    rainStatus = data.get("rainStatus")
    rainAnalogValue = data.get("rainAnalog")
    lightLevel = data.get("lightLevel")
    pressure = data.get("pressure")

    # Validare minimă
    if None in [humidity, temperature, uvValue, rainStatus, rainAnalogValue, lightLevel, pressure]:
        return jsonify({"error": "Missing one or more values"}), 400

    save_to_database(humidity, temperature, uvValue, rainStatus, rainAnalogValue, lightLevel, pressure)
    return jsonify({"message": "Data received and saved successfully!"})


# === Endpoint pentru ultimul set de date ===
@app.route("/get_latest_data", methods=["GET"])
def get_latest_data():
    connection = sqlite3.connect("weather_station.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    connection.close()

    if row:
        data = {
            "id": row[0],
            "humidity": row[1],
            "temperature": row[2],
            "uvValue": row[3],
            "rainStatus": row[4],
            "rainAnalogValue": row[5],
            "lightLevel": row[6],
            "pressure": row[7],
            "timestamp": row[8],
            "timestamp_iso": row[9],
            "hour": row[10],
            "day_of_week": row[11],
            "predicted_temp": row[12],
            "weather_class": row[13]
        }
        return jsonify(data)
    else:
        return jsonify({"message": "No data found!"})


# === Pagina principală ===
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ai_insights", methods=["GET"])
def ai_insights():
    connection = sqlite3.connect("weather_station.db")
    cursor = connection.cursor()
    cursor.execute("SELECT predicted_temp, weather_class, weather_type FROM sensor_data ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    connection.close()

    if row:
        return jsonify({
            "predicted_temp": round(row[0], 2) if row[0] is not None else None,
            "weather_class": row[1],
            "weather_type": row[2]
        })
    else:
        return jsonify({"message": "No AI data found."})


@app.route("/export_csv", methods=["POST"])
def export_csv():
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    if not start_date or not end_date:
        return "Datele de început și sfârșit sunt obligatorii", 400

    start = f"{start_date}T00:00:00"
    end = f"{end_date}T23:59:59"

    try:
        connection = sqlite3.connect("weather_station.db")
        query = f"""
            SELECT timestamp_iso, temperature, humidity, pressure, lightLevel
            FROM sensor_data
            WHERE timestamp_iso BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, connection, params=(start, end))
        connection.close()

        if df.empty:
            return "Nu s-au găsit date în intervalul selectat.", 404

        export_path = "export_date_meteo.csv"
        df.to_csv(export_path, index=False)

        return send_file(export_path, as_attachment=True)

    except Exception as e:
        return f"Eroare la exportul datelor: {str(e)}", 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
