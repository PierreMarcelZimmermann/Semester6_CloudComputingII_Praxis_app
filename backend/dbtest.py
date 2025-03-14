import json
from urllib.parse import quote_plus
from sqlalchemy import create_engine

# Lade die JSON-Konfigurationsdatei
with open('db_config.json', 'r') as file:
    config = json.load(file)

# Extrahiere den Servernamen und die Datenbankinformationen
hostname = config['server']
database_name = config['database_name']
username = config['username']

# URL-kodiertes Passwort (falls Sonderzeichen wie "@" enthalten sind)
password_encoded = quote_plus(config['password'])

# Baue den Connection String
connection_string = f"mysql+mysqlconnector://{username}:{password_encoded}@{hostname}/{database_name}"

# Erstelle den SQLAlchemy-Engine
engine = create_engine(connection_string)

# Teste die Verbindung
try:
    with engine.connect() as connection:
        print("Verbindung erfolgreich!")
except Exception as e:
    print(f"Fehler bei der Verbindung: {e}")
