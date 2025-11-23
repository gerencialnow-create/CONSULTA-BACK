from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import json

app = Flask(__name__)

# Libera CORS para as rotas /api/*
CORS(app, resources={r"/api/*": {"origins": "*"}})

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "config" / "users.json"


def load_users():
    """Carrega a lista de usuários do arquivo JSON."""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo de usuários não encontrado em: {USERS_FILE}")
        return []
    except Exception as e:
        print(f"[ERRO] Falha ao ler users.json: {e}")
        return []


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

    # Usuário ou senha inválidos
    return jsonify({"success": False, "error": "invalid_credentials"}), 401


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Porta padrão que estamos usando para a API
    app.run(host="0.0.0.0", port=5050)
