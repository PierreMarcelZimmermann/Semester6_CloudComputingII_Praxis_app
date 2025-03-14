import mysql.connector
from mysql.connector import Error

# Verbindungsdaten (entsprechen den Azure MySQL-Daten)
db_config = {
    'host': 'digital-bison-xxyz123.mysql.database.azure.com',
    'port': 3306,  # Der Port ist optional, aber wir fügen ihn hier hinzu
    'user': 'sqladmin',
    'password': 'P@ssw0rd1234',
}

# Verbindung testen
try:
    # Verbindung aufbauen
    connection = mysql.connector.connect(**db_config)

    if connection.is_connected():
        print("Erfolgreich mit der Datenbank verbunden!")
        # Hier kannst du weitere SQL-Abfragen durchführen, z.B.:
        # cursor = connection.cursor()
        # cursor.execute("SELECT DATABASE();")
        # print(cursor.fetchone())

except Error as e:
    print(f"Fehler beim Verbinden zur MySQL-Datenbank: {e}")
finally:
    if connection.is_connected():
        connection.close()
        print("Datenbankverbindung geschlossen.")
