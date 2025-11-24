from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import json
import subprocess
from werkzeug.utils import secure_filename
from datetime import datetime

# Versão via GitHub - atualizado

app = Flask(__name__)

# Libera CORS para todas rotas /api/*
CORS(app, resources={r"/api/*": {"origins": "*"}})

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "config" / "users.json"

# Diretório geral de uploads
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# CARREGAR USUÁRIOS
# ============================================================

def load_users():
    """Carrega usuários do arquivo JSON."""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {USERS_FILE}")
        return []
    except Exception as e:
        print(f"[ERRO] Falha ao carregar users.json: {e}")
        return []


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"success": False, "error": "missing_fields"}), 400

    users = load_users()

    for user in users:
        if (
            user.get("username") == username
            and user.get("password") == password
            and user.get("active", True)
        ):
            return jsonify({
                "success": True,
                "username": username,
                "role": user.get("role", "user")
            }), 200

    return jsonify({"success": False, "error": "invalid_credentials"}), 401


# ============================================================
# NOVA ROTA CORRETA PARA O FRONT:
# /api/facta/upload
# ============================================================

@app.post("/api/facta/upload")
def facta_upload():
    """
    Rota usada pelo dashboard.js para enviar arquivo da automação da FACTA.
    (Por enquanto só salva o arquivo; depois ligamos na automação.)
    """

    if "file" not in request.files:
        return jsonify({"ok": False, "error": "Nenhum arquivo enviado."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"ok": False, "error": "Arquivo sem nome."}), 400

    # Diretório específico da FACTA
    facta_dir = UPLOAD_DIR / "facta"
    facta_dir.mkdir(parents=True, exist_ok=True)

    # Nome seguro
    base_name = secure_filename(file.filename)

    # Timestamp no nome para evitar conflitos
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    final_name = f"{ts}-{base_name}"
    save_path = facta_dir / final_name

    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Falha ao salvar arquivo: {e}"}), 500

    # ⚠️ A automação FACTA ainda não está plugada aqui.
    # Vamos ligar depois com um worker próprio.

    return jsonify({
        "ok": True,
        "message": "Arquivo recebido com sucesso. (Automação será ligada depois.)",
        "saved_as": final_name
    }), 200

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
