import os
import sqlite3
from flask import Flask, request, session, redirect, url_for, render_template_string

app = Flask(__name__)
app.secret_key = os.urandom(16)

FLAG = os.environ.get("CHALLENGE_FLAG", "UNIALONE{sql_1nj3ct10n_un10n_pwn}")
DB = "/tmp/novacorp.db"


def init_db():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
    cur.executemany(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        [
            ("admin", "S3cr3t_N0v4_2024!", "admin"),
            ("jdupont", "azerty", "employee"),
            ("mbenali", "password1", "employee"),
        ],
    )
    cur.execute("CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT)")
    cur.executemany(
        "INSERT INTO employees (name, department) VALUES (?, ?)",
        [
            ("Jean Dupont", "Finance"),
            ("Mohamed Benali", "IT"),
            ("Sarah Khelifi", "RH"),
        ],
    )
    cur.execute("CREATE TABLE secret_notes (id INTEGER PRIMARY KEY, title TEXT, flag TEXT)")
    cur.execute("INSERT INTO secret_notes (title, flag) VALUES (?, ?)", ("internal_memo", FLAG))
    con.commit()
    con.close()


PAGE = """
<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>NovaCorp - Portail Employe</title>
<style>
 body{font-family:system-ui,sans-serif;background:#0d1117;color:#e6edf3;max-width:760px;margin:40px auto;padding:0 20px}
 h1{color:#58a6ff} a{color:#3fb950} input{padding:8px;margin:4px 0;width:260px;background:#161b22;border:1px solid #30363d;color:#e6edf3;border-radius:6px}
 .btn{background:#238636;border:0;color:#fff;padding:9px 18px;border-radius:6px;cursor:pointer;width:auto}
 .card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;margin:16px 0}
 .err{color:#f85149} .flag{color:#3fb950;font-weight:700;font-family:monospace}
 table{width:100%;border-collapse:collapse} td,th{border-bottom:1px solid #21262d;padding:8px;text-align:left}
</style></head><body>
<h1>NovaCorp &mdash; Portail Employe</h1>
{{ body|safe }}
</body></html>
"""

LOGIN = """
<div class="card">
<form method="post">
<div><input name="username" placeholder="Nom d'utilisateur"></div>
<div><input name="password" type="password" placeholder="Mot de passe"></div>
<div><button class="btn" type="submit">Se connecter</button></div>
</form>
{% if error %}<p class="err">{{ error }}</p>{% endif %}
</div>
<p style="color:#8b949e">Compte de demonstration fourni par la DSI. Acces restreint.</p>
"""

DASH = """
<div class="card">
<p>Connecte en tant que <b>{{ username }}</b> (role : {{ role }})</p>
{% if flag %}<p>Note interne confidentielle : <span class="flag">{{ flag }}</span></p>
{% else %}<p style="color:#8b949e">Tu n'as pas les droits pour voir les notes internes.</p>{% endif %}
</div>
<div class="card">
<h3>Annuaire des employes</h3>
<form method="get" action="/search">
<input name="q" placeholder="Rechercher un employe"><button class="btn" type="submit">Chercher</button>
</form>
</div>
<p><a href="/logout">Deconnexion</a></p>
"""

SEARCH = """
<div class="card">
<form method="get" action="/search">
<input name="q" value="{{ q }}" placeholder="Rechercher un employe"><button class="btn" type="submit">Chercher</button>
</form>
</div>
<div class="card">
{% if error %}<p class="err">{{ error }}</p>{% endif %}
<table><tr><th>Nom</th><th>Departement</th></tr>
{% for r in rows %}<tr><td>{{ r[0] }}</td><td>{{ r[1] }}</td></tr>{% endfor %}
</table>
</div>
<p><a href="/dashboard">Retour</a></p>
"""


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        # VULNERABLE : requete construite par concatenation (volontaire)
        query = "SELECT id, username, role FROM users WHERE username='%s' AND password='%s'" % (u, p)
        con = sqlite3.connect(DB)
        cur = con.cursor()
        row = None
        try:
            cur.execute(query)
            row = cur.fetchone()
        except Exception as e:
            error = "SQL error: %s" % e
        con.close()
        if row:
            session["username"] = row[1]
            session["role"] = row[2]
            return redirect(url_for("dashboard"))
        elif not error:
            error = "Identifiants invalides."
    return render_template_string(PAGE, body=render_template_string(LOGIN, error=error))


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    flag = None
    if session.get("role") == "admin":
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("SELECT flag FROM secret_notes LIMIT 1")
        flag = cur.fetchone()[0]
        con.close()
    return render_template_string(
        PAGE, body=render_template_string(DASH, username=session["username"], role=session.get("role"), flag=flag)
    )


@app.route("/search")
def search():
    if "username" not in session:
        return redirect(url_for("login"))
    q = request.args.get("q", "")
    rows = []
    error = None
    # VULNERABLE : injectable en UNION (2 colonnes) (volontaire)
    query = "SELECT name, department FROM employees WHERE name LIKE '%%%s%%'" % q
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:
        error = "SQL error: %s" % e
    con.close()
    return render_template_string(PAGE, body=render_template_string(SEARCH, rows=rows, q=q, error=error))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
