import sqlite3
conn = sqlite3.connect("weather_station.db")
for row in conn.execute("SELECT * FROM sensor_data ORDER BY id"):
    print(row)
conn.close()
