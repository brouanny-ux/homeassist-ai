from flask import Flask, request, jsonify, render_template, session, redirect
from groq import Groq
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_conn, is_pg
import os
def migrate_db():
    try:
        conn = get_conn()
        cursor = conn.cursor()
        if is_pg():
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';")
            cursor.execute("UPDATE users SET role = 'admin' WHERE email = 'brouannya@gmail.com';")
        conn.commit()
        conn.close()
        print("Migration OK !")
    except Exception as e:
        print(f"Migration: {e}")

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "homeassist_secret_2026"

historique = []

def chercher_artisans(ville, specialite, quartier=""):
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    if quartier:
        cursor.execute(f"""
            SELECT nom, prenom, telephone, specialite, quartier
            FROM artisans
            WHERE ville LIKE {ph} AND specialite LIKE {ph} AND quartier LIKE {ph}
            AND disponible = 1 LIMIT 3
        """, (f"%{ville}%", f"%{specialite}%", f"%{quartier}%"))
        artisans = cursor.fetchall()
        if artisans:
            conn.close()
            return artisans
    cursor.execute(f"""
        SELECT nom, prenom, telephone, specialite, quartier
        FROM artisans
        WHERE ville LIKE {ph} AND specialite LIKE {ph}
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
    if not session.get('user'):
        return redirect("/auth")
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
            artisans_info = "\n\n⚠️ Aucun artisan disponible dans votre ville pour le moment."
    return jsonify({"response": reply + artisans_info})

@app.route("/inscription")
def inscription():
    return render_template("inscription.html")

@app.route("/inscrire", methods=["POST"])
def inscrire():
    data = request.json
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"""
        INSERT INTO artisans (nom, prenom, telephone, email, ville, quartier, specialite, experience)
        VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})
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
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"""
        INSERT INTO reservations (nom_client, telephone_client, ville, quartier,
        type_service, sous_service, date_intervention, heure_debut, duree,
        contrat, logement, salaire)
        VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})
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
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    query = "SELECT * FROM artisans WHERE disponible = 1"
    params = []
    if ville:
        query += f" AND ville LIKE {ph}"
        params.append(f"%{ville}%")
    if specialite:
        query += f" AND specialite LIKE {ph}"
        params.append(f"%{specialite}%")
    if quartier:
        query += f" AND quartier LIKE {ph}"
        params.append(f"%{quartier}%")
    query += " ORDER BY id DESC LIMIT 10"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    if is_pg():
        cols = [desc[0] for desc in cursor.description]
        artisans_list = [dict(zip(cols, row)) for row in rows]
    else:
        cols = [desc[0] for desc in cursor.description]
        artisans_list = [dict(zip(cols, row)) for row in rows]
    conn.close()
    return jsonify({"artisans": artisans_list})

@app.route("/admin-homeassist-2026")
def admin():
    user = session.get('user')
    if not user:
        return redirect("/auth")
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"SELECT role FROM users WHERE email = {ph}", (user.get('email'),))
    row = cursor.fetchone()
    conn.close()
    if not row or row[0] != 'admin':
        return redirect("/")
    return render_template("admin.html")

@app.route("/admin/data")
def admin_data():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservations ORDER BY id DESC")
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    reservations = [dict(zip(cols, row)) for row in rows]
    cursor.execute("SELECT * FROM artisans ORDER BY id DESC")
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    artisans_list = [dict(zip(cols, row)) for row in rows]
    conn.close()
    return jsonify({"reservations": reservations, "artisans": artisans_list})

@app.route("/admin/statut_reservation", methods=["POST"])
def statut_reservation():
    data = request.json
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"UPDATE reservations SET statut = {ph} WHERE id = {ph}", (data.get("statut"), data.get("id")))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/admin/toggle_artisan", methods=["POST"])
def toggle_artisan():
    data = request.json
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"UPDATE artisans SET disponible = {ph} WHERE id = {ph}", (data.get("disponible"), data.get("id")))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/auth")
def auth():
    return render_template("auth.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    try:
        password_hash = generate_password_hash(data.get("password"))
        cursor.execute(f"""
            INSERT INTO users (prenom, nom, email, telephone, pays, ville, quartier, password_hash, role)
            VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})
        """, (
            data.get("prenom"), data.get("nom"), data.get("email"),
            data.get("telephone"), data.get("pays"), data.get("ville"),
            data.get("quartier"), password_hash, data.get("role", "user")
        ))
        conn.commit()
        role = data.get("role", "user")
        session['user'] = {
            'email': data.get("email"),
            'prenom': data.get("prenom"),
            'nom': data.get("nom"),
            'ville': data.get("ville"),
            'quartier': data.get("quartier"),
            'role': role
        }
        return jsonify({"success": True, "role": role, "redirect": "/dashboard/artisan" if role == "artisan" else "/dashboard/user"})
    except Exception as e:
        if "UNIQUE" in str(e) or "unique" in str(e):
            return jsonify({"success": False, "error": "Cet email est déjà utilisé"})
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"""
        SELECT id, prenom, nom, email, telephone, ville, quartier, password_hash, role
        FROM users WHERE email = {ph} OR telephone = {ph}
    """, (email, email))
    cols = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    conn.close()
    if row:
        user = dict(zip(cols, row))
        if check_password_hash(user["password_hash"], password):
            role = user.get("role", "user")
            session['user'] = {
                'email': user["email"],
                'prenom': user["prenom"],
                'nom': user["nom"],
                'ville': user["ville"],
                'quartier': user["quartier"],
                'role': role
            }
            return jsonify({"success": True, "role": role, "redirect": "/dashboard/artisan" if role == "artisan" else "/dashboard/user"})
    return jsonify({"success": False, "error": "Email ou mot de passe incorrect"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/auth")

@app.route("/me")
def me():
    user = session.get('user')
    if user:
        return jsonify({"user": user})
    return jsonify({"user": None})

@app.route("/noter_artisan", methods=["POST"])
def noter_artisan():
    data = request.json
    user = session.get('user')
    if not user:
        return jsonify({"success": False, "error": "Connectez-vous pour noter"})
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    try:
        cursor.execute(f"""
            INSERT INTO ratings (artisan_id, user_email, note, avis)
            VALUES ({ph}, {ph}, {ph}, {ph})
        """, (
            data.get("artisan_id"),
            user.get("email"),
            data.get("note"),
            data.get("avis", "")
        ))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()

@app.route("/note_artisan/<int:artisan_id>")
def note_artisan(artisan_id):
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"""
        SELECT COUNT(note) as total, AVG(note) as moyenne
        FROM ratings WHERE artisan_id = {ph}
    """, (artisan_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] > 0:
        return jsonify({"total": row[0], "moyenne": round(float(row[1]), 1)})
    return jsonify({"total": 0, "moyenne": 0})

@app.route("/dashboard/user")
def dashboard_user():
    if not session.get('user'):
        return redirect("/auth")
    return render_template("dashboard_user.html")

@app.route("/dashboard/artisan")
def dashboard_artisan():
    if not session.get('user'):
        return redirect("/auth")
    return render_template("dashboard_artisan.html")

@app.route("/mes_reservations")
def mes_reservations():
    user = session.get('user')
    if not user:
        return jsonify({"reservations": []})
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"""
        SELECT * FROM reservations
        WHERE nom_client LIKE {ph} OR telephone_client LIKE {ph}
        ORDER BY id DESC LIMIT 10
    """, (f"%{user.get('prenom')}%", f"%{user.get('email')}%"))
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"reservations": [dict(zip(cols, row)) for row in rows]})

@app.route("/mon_profil_artisan")
def mon_profil_artisan():
    user = session.get('user')
    if not user:
        return jsonify({"artisan": None})
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"""
        SELECT * FROM artisans
        WHERE email = {ph} OR nom LIKE {ph}
        LIMIT 1
    """, (user.get('email'), f"%{user.get('nom')}%"))
    cols = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({"artisan": dict(zip(cols, row))})
    return jsonify({"artisan": None})

@app.route("/avis_artisan/<int:artisan_id>")
def avis_artisan(artisan_id):
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"""
        SELECT note, avis, date_notation
        FROM ratings WHERE artisan_id = {ph}
        ORDER BY date_notation DESC LIMIT 10
    """, (artisan_id,))
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"avis": [dict(zip(cols, row)) for row in rows]})
@app.route("/set-admin-secret-2026")
def set_admin():
    conn = get_conn()
    cursor = conn.cursor()
    ph = "%s" if is_pg() else "?"
    cursor.execute(f"UPDATE users SET role = 'admin' WHERE email = {ph}", ('brouannya@gmail.com',))
    conn.commit()
    conn.close()
    return "Admin configuré !"
@app.route("/admin/users")
def admin_users():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, prenom, nom, email, telephone, ville, role, date_inscription FROM users ORDER BY id DESC")
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"users": [dict(zip(cols, row)) for row in rows]})

@app.route("/admin/avis")
def admin_avis():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ratings ORDER BY date_notation DESC")
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"avis": [dict(zip(cols, row)) for row in rows]})

if __name__ == "__main__":
    from database import init_db, init_reservations, init_users, init_ratings
    init_db()
    init_reservations()
    init_users()
    init_ratings()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
    
    from database import init_db, init_reservations, init_users, init_ratings
    init_db()
    init_reservations()
    init_users()
    init_ratings()
    migrate_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)