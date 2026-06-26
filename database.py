import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect("homeassist.db")

def is_pg():
    return DATABASE_URL is not None

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    if is_pg():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artisans (
                id SERIAL PRIMARY KEY,
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
    else:
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
    conn = get_conn()
    cursor = conn.cursor()
    if is_pg():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id SERIAL PRIMARY KEY,
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
    else:
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
    conn = get_conn()
    cursor = conn.cursor()
    if is_pg():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                prenom TEXT NOT NULL,
                nom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'user',
                telephone TEXT NOT NULL,
                pays TEXT,
                ville TEXT NOT NULL,
                quartier TEXT,
                password_hash TEXT NOT NULL,
                date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prenom TEXT NOT NULL,
                nom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telephone TEXT NOT NULL,
                pays TEXT,
                ville TEXT NOT NULL,
                quartier TEXT,
                password_hash TEXT NOT NULL,
                date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()
    print("Table users OK !")

def init_ratings():
    conn = get_conn()
    cursor = conn.cursor()
    if is_pg():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id SERIAL PRIMARY KEY,
                artisan_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                note INTEGER NOT NULL CHECK(note >= 1 AND note <= 5),
                avis TEXT,
                date_notation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artisan_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                note INTEGER NOT NULL CHECK(note >= 1 AND note <= 5),
                avis TEXT,
                date_notation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()
    print("Table ratings OK !")

if __name__ == "__main__":
    init_db()
    init_reservations()
    init_users()
    init_ratings()