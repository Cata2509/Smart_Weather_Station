import sqlite3

connection = sqlite3.connect("weather_station.db")
cursor = connection.cursor()

# Adăugăm noua coloană dacă nu există deja
try:
    cursor.execute("ALTER TABLE sensor_data ADD COLUMN weather_type TEXT")
    print("Coloana 'weather_type' a fost adăugată.")
except sqlite3.OperationalError:
    print("Coloana 'weather_type' există deja.")

connection.commit()
connection.close()
