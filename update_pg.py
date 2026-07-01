import psycopg2

DATABASE_URL = "postgresql://postgres:SLMQOCoQuWyPBEycHeICQtBxutCEcQdx@postgres.railway.internal:5432/railway"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Ajouter colonne role
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';")
    
    # Mettre à jour admin
    cursor.execute("UPDATE users SET role = 'admin' WHERE email = 'brouannya@gmail.com';")
    
    conn.commit()
    conn.close()
    print("✅ Mise à jour PostgreSQL réussie !")
except Exception as e:
    print(f"❌ Erreur : {e}")