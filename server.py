import os
import sqlite3
import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# chemins absolus (important pour Render)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_FOLDER = os.path.join(BASE_DIR, "template")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "news.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# initialisation base de données
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image_path TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()


# page principale
@app.route("/")
def serve_liste():
    return send_from_directory(TEMPLATE_FOLDER, "liste.html")


# page lire
@app.route("/lire")
def serve_lire():
    return send_from_directory(TEMPLATE_FOLDER, "lire.html")


# servir les images uploadées
@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# API : liste des news
@app.route("/api/news", methods=["GET"])
def get_news():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, description, image_path, date
        FROM news
        ORDER BY date DESC
    """)

    rows = cursor.fetchall()

    news = []
    for r in rows:
        news.append({
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "image_path": r[3],
            "date": r[4]
        })

    conn.close()
    return jsonify(news)


# API : détail d'une news
@app.route("/api/news/<int:news_id>", methods=["GET"])
def get_news_detail(news_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, description, image_path, date
        FROM news
        WHERE id = ?
    """, (news_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "image_path": row[3],
            "date": row[4]
        })

    return jsonify({"error": "Not found"}), 404


# API : publier une news
@app.route("/api/publish", methods=["POST"])
def publish_news():

    if "title" not in request.form or "description" not in request.form:
        return jsonify({"error": "Missing fields"}), 400

    if "image" not in request.files:
        return jsonify({"error": "Image missing"}), 400

    title = request.form["title"]
    description = request.form["description"]
    image_file = request.files["image"]

    if image_file.filename == "":
        return jsonify({"error": "No image selected"}), 400

    filename = secure_filename(image_file.filename)

    if not filename:
        ext = os.path.splitext(image_file.filename)[1]
        filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ext

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    image_file.save(filepath)

    date_now = datetime.datetime.now().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO news (title, description, image_path, date)
        VALUES (?, ?, ?, ?)
    """, (title, description, filename, date_now))

    conn.commit()

    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "success": True,
        "id": new_id
    })


# démarrage local (pas utilisé par gunicorn)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
