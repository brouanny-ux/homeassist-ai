import sqlite3

conn = sqlite3.connect("homeassist.db")
conn.execute("UPDATE users SET role = 'admin' WHERE email = 'brouannya@gmail.com'")
conn.commit()
conn.close()
print("Admin créé !")