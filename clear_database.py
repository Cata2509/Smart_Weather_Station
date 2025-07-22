import sqlite3

connection = sqlite3.connect("weather_station.db")
cursor = connection.cursor()

cursor.execute("DELETE FROM sensor_data")
connection.commit()
connection.close()

print("Toate înregistrările au fost șterse.")
