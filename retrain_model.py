import pandas as pd
import sqlite3
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import pickle
import os

# === Config ===
csv_folder = "D:\\Disertatie\\date_antrenament"
csv_files = [
    "2022_Apri-August.csv",
    "2023_April-August.csv",
    "2024_April-August.csv",
    "2025_April-Present.csv"
]

# === 1. Citim datele din CSV
csv_data = []
for file in csv_files:
    path = os.path.join(csv_folder, file)
    df = pd.read_csv(path)
    if 'time' in df.columns:
        df.rename(columns={'time': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek  # Monday = 0
    df = df[['date', 'tmax', 'pres', 'prcp', 'day_of_week']]
    csv_data.append(df)

df_csv = pd.concat(csv_data)

# === 2. Citim datele din baza SQLite
conn = sqlite3.connect("weather_station.db")
query = "SELECT timestamp_iso, temperature, pressure, day_of_week FROM sensor_data"
df_sql = pd.read_sql_query(query, conn)
conn.close()

# Conversii și adăugări
df_sql['date'] = pd.to_datetime(df_sql['timestamp_iso'])
df_sql['tmax'] = df_sql['temperature']  # presupunem că e maximă
df_sql['pres'] = df_sql['pressure']
df_sql['prcp'] = 0.0  # nu avem precipitații reale
df_sql['day_of_week'] = pd.to_datetime(df_sql['date']).dt.dayofweek
df_sql = df_sql[['date', 'tmax', 'pres', 'prcp', 'day_of_week']]

# === 3. Combinăm datele
df_all = pd.concat([df_csv, df_sql])

# === 4. Curățăm datele lipsă
df_all = df_all.dropna(subset=['tmax', 'pres', 'prcp', 'day_of_week'])

# === Filtrare orară: 08:00–21:00
df_all = df_all[df_all['date'].dt.hour >= 8]
df_all = df_all[df_all['date'].dt.hour < 21]

# === 5. Pregătim datele pentru antrenare
X = df_all[['pres', 'prcp', 'day_of_week']]
y = df_all['tmax']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

# === 6. Evaluare și salvare model
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)

print(f"Modelul reantrenat. MAE: {mae:.2f}°C")

with open("model_tmax.pkl", "wb") as f:
    pickle.dump(model, f)

print("Modelul nou a fost salvat în model_tmax.pkl.")
