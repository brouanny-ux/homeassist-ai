import sqlite3

def init_db():
    conn = sqlite3.connect("homeassist.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artisans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            telephone TEXT NOT NULL,
            email TEXT,
            ville TEXT NOT NULL,
            quartier TEXT,
            specialite TEXT NOT NULL,
            experience TEXT,
            disponible INTEGER DEFAULT 1,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("Table artisans OK !")

def init_reservations():
    conn = sqlite3.connect("homeassist.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_client TEXT NOT NULL,
            telephone_client TEXT NOT NULL,
            ville TEXT NOT NULL,
            quartier TEXT,
            type_service TEXT NOT NULL,
            sous_service TEXT,
            date_intervention TEXT NOT NULL,
            heure_debut TEXT NOT NULL,
            duree TEXT NOT NULL,
            contrat TEXT DEFAULT 'Ponctuel',
            logement TEXT DEFAULT 'Non',
            salaire TEXT,
            statut TEXT DEFAULT 'en_attente',
            date_reservation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("Table réservations OK !")
def init_users():
    conn = sqlite3.connect("homeassist.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prenom TEXT NOT NULL,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telephone TEXT NOT NULL,
            ville TEXT NOT NULL,
            quartier TEXT,
            password_hash TEXT NOT NULL,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
 """)
    conn.commit()
    conn.close()
    print("Table users OK !")

if __name__ == "__main__":
    init_db()
    init_reservations()
    init_users()