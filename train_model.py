import pandas as pd
import os
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import pickle

# === Config ===
csv_folder = "D:\\Disertatie\\date_antrenament"  # unde sunt fișierele CSV
csv_files = [
    "2022_Apri-August.csv",
    "2023_April-August.csv",
    "2024_April-August.csv",
    "2025_April-Present.csv"
]

# === Pregătire date ===
dfs = []
for file in csv_files:
    path = os.path.join(csv_folder, file)
    df = pd.read_csv(path)
    if 'time' in df.columns:
        df.rename(columns={"time": "date"}, inplace=True)
    dfs.append(df)

data = pd.concat(dfs)
data['date'] = pd.to_datetime(data['date'])

# Eliminăm rânduri incomplete
data = data.dropna(subset=['tmax', 'pres', 'prcp'])

# Adăugăm coloane pentru ziua săptămânii
data['day_of_week'] = data['date'].dt.dayofweek  # Monday=0, Sunday=6

features = ['pres', 'prcp', 'day_of_week', 'tmax']
data = data.dropna(subset=features)

X = data[['pres', 'prcp', 'day_of_week']]
y = data['tmax']

# === Antrenare model ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

# Evaluare simplă
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"Modelul a fost antrenat. MAE: {mae:.2f}°C")

# === Salvăm modelul ===
with open("model_tmax.pkl", "wb") as f:
    pickle.dump(model, f)
print("Modelul a fost salvat în model_tmax.pkl.")
