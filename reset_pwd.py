import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("homeassist.db")
new_hash = generate_password_hash("homeassist2026")
conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hash, "brouannya@gmail.com"))
conn.commit()
conn.close()
print("Mot de passe réinitialisé !")
