from flask import Flask, request, jsonify, render_template
from groq import Groq
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__, static_folder='static', static_url_path='/static')

app.secret_key = "homeassist_secret_2026"
historique = []

def chercher_artisans(ville, specialite, quartier=""):
    conn = sqlite3.connect("homeassist.db")
    cursor = conn.cursor()
    if quartier:
        cursor.execute("""
            SELECT nom, prenom, telephone, specialite, quartier
            FROM artisans
            WHERE ville LIKE ? AND specialite LIKE ? AND quartier LIKE ?
            AND disponible = 1 LIMIT 3
        """, (f"%{ville}%", f"%{specialite}%", f"%{quartier}%"))
        artisans = cursor.fetchall()
        if artisans:
            conn.close()
            return artisans
    cursor.execute("""
        SELECT nom, prenom, telephone, specialite, quartier
        FROM artisans
        WHERE ville LIKE ? AND specialite LIKE ?
        AND disponible = 1 LIMIT 3
    """, (f"%{ville}%", f"%{specialite}%"))
    artisans = cursor.fetchall()
    conn.close()
    return artisans

SYSTEM_PROMPT = """Tu es HomeAssist AI, un assistant domestique intelligent
pour les menages en Afrique de l'Ouest. Tu aides les utilisateurs a :
- Diagnostiquer les pannes (ventilateur, frigo, clim, machine a laver, micro-onde, plomberie, gaz...)
- Identifier le type d'artisan necessaire (electricien, plombier, frigoriste, vitrier, jardinier...)
- Estimer le cout approximatif d'une reparation
- Donner des conseils de securite en cas de fuite de gaz ou probleme electrique

REGLES :
Pose UNE SEULE question a la fois pour diagnostiquer le probleme, pas plusieurs.
Ne repete jamais ce que l'utilisateur vient de dire. Va directement a la question suivante.
Quand tu as identifie le probleme et le type d'artisan necessaire, termine toujours ta reponse par :
ARTISAN_NEEDED: [type d'artisan en un mot, ex: Electricien, Plombier, Frigoriste, Macon, Jardinier]"""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    user_city = data.get("city", "")
    user_quartier = data.get("quartier", "")
    if user_city:
        user_message = f"[Utilisateur situe a {user_city}, quartier {user_quartier}] {user_message}"
    historique.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + historique,
        temperature=0.7,
        max_tokens=500
    )
    reply = response.choices[0].message.content
    historique.append({"role": "assistant", "content": reply})
    artisans_info = ""
    if "ARTISAN_NEEDED:" in reply:
        specialite = reply.split("ARTISAN_NEEDED:")[-1].strip().split("\n")[0].strip()
        print(f"Spécialité détectée : {specialite}")
        print(f"Ville détectée : {user_city}")
        reply = reply.replace(f"ARTISAN_NEEDED: {specialite}", "").strip()
        specialite_search = specialite.replace("É", "").replace("é", "").replace("È", "").replace("è", "")
        specialite_search = specialite_search[1:] if specialite_search else specialite
        artisans = chercher_artisans(user_city, specialite_search, user_quartier)
        if artisans:
            artisans_info = "\n\n📋 **Artisans disponibles près de chez vous :**\n"
            for a in artisans:
                artisans_info += f"\n🔧 {a[0]} {a[1]} — {a[3]}\n📞 {a[2]}"
                if a[4]:
                    artisans_info += f" — {a[4]}"
                artisans_info += "\n"
        else:
            artisans_info = "\n\n⚠️ Aucun artisan disponible dans votre ville pour le moment. Nous allons vous en trouver un très bientôt !"
    return jsonify({"response": reply + artisans_info})

@app.route("/inscription")
def inscription():
    return render_template("inscription.html")

@app.route("/inscrire", methods=["POST"])
def inscrire():
    data = request.json
    conn = sqlite3.connect("homeassist.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO artisans (nom, prenom, telephone, email, ville, quartier, specialite, experience)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("nom"), data.get("prenom"), data.get("telephone"),
        data.get("email"), data.get("ville"), data.get("quartier"),
        data.get("specialite"), data.get("experience")
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/reservation")
def reservation():
    return render_template("reservation.html")

@app.route("/reserver", methods=["POST"])
def reserver():
    data = request.json
    conn = sqlite3.connect("homeassist.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reservations (nom_client, telephone_client, ville, quartier,
        type_service, sous_service, date_intervention, heure_debut, duree,
        contrat, logement, salaire)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("nom_client"), data.get("telephone_client"),
        data.get("ville"), data.get("quartier"),
        data.get("type_service"), data.get("sous_service"),
        data.get("date_intervention"), data.get("heure_debut"),
        data.get("duree"), data.get("contrat", "Ponctuel"),
        data.get("logement", "Non"), data.get("salaire", "")
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/artisans")
def artisans():
    return render_template("artisans.html")

@app.route("/chercher_artisans", methods=["POST"])
def chercher_artisans_page():
    data = request.json
    ville = data.get("ville", "")
    quartier = data.get("quartier", "")
    specialite = data.get("specialite", "")
    conn = sqlite3.connect("homeassist.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM artisans WHERE disponible = 1"
    params = []
    if ville:
        query += " AND ville LIKE ?"
        params.append(f"%{ville}%")
    if specialite:
        query += " AND specialite LIKE ?"
        params.append(f"%{specialite}%")
    if quartier:
        query += " AND quartier LIKE ?"
        params.append(f"%{quartier}%")
    query += " ORDER BY id DESC LIMIT 10"
    cursor.execute(query, params)
    artisans = [dict(a) for a in cursor.fetchall()]
    conn.close()
    return jsonify({"artisans": artisans})

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/admin/data")
def admin_data():
    conn = sqlite3.connect("homeassist.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservations ORDER BY id DESC")
    reservations = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM artisans ORDER BY id DESC")
    artisans = [dict(a) for a in cursor.fetchall()]
    conn.close()
    return jsonify({"reservations": reservations, "artisans": artisans})

@app.route("/admin/statut_reservation", methods=["POST"])
def statut_reservation():
    data = request.json
    conn = sqlite3.connect("homeassist.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE reservations SET statut = ? WHERE id = ?", (data.get("statut"), data.get("id")))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/admin/toggle_artisan", methods=["POST"])
def toggle_artisan():
    data = request.json
    conn = sqlite3.connect("homeassist.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE artisans SET disponible = ? WHERE id = ?", (data.get("disponible"), data.get("id")))
    conn.commit()
    conn.close()
    return jsonify({"success": True})
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

@app.route("/auth")
def auth():
    return render_template("auth.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    conn = sqlite3.connect("homeassist.db")
    cursor = conn.cursor()
    try:
        password_hash = generate_password_hash(data.get("password"))
        cursor.execute("""
            INSERT INTO users (prenom, nom, email, telephone, ville, quartier, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("prenom"), data.get("nom"), data.get("email"),
            data.get("telephone"), data.get("ville"), data.get("quartier"),
            password_hash
        ))
        conn.commit()
        session['user'] = {
            'email': data.get("email"),
            'prenom': data.get("prenom"),
            'ville': data.get("ville"),
            'quartier': data.get("quartier")
        }
        return jsonify({"success": True})
    except Exception as e:
        if "UNIQUE" in str(e):
            return jsonify({"success": False, "error": "Cet email est déjà utilisé"})
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    conn = sqlite3.connect("homeassist.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? OR telephone = ?", (email, email))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user["password_hash"], password):
        session['user'] = {
            'email': user["email"],
            'prenom': user["prenom"],
            'ville': user["ville"],
            'quartier': user["quartier"]
        }
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Email ou mot de passe incorrect"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/auth")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)