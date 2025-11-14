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
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"ok": False, "error": "Usuário e senha são obrigatórios."}), 400

    users = load_users()
    if not users:
        return jsonify({"ok": False, "error": "Nenhum usuário configurado."}), 500

    # Procura usuário pelo username
    user = next((u for u in users if u.get("username") == username), None)

    # Usuário não existe ou está inativo
    if not user or not user.get("active", True):
        return jsonify({"ok": False, "error": "Usuário ou senha inválidos."}), 401

    # Compara senha simples (texto puro)
    if user.get("password") != password:
        return jsonify({"ok": False, "error": "Usuário ou senha inválidos."}), 401

    # Login OK
    return jsonify({
        "ok": True,
        "username": user.get("username"),
        "role": user.get("role", "user")
    }), 200


if __name__ == "__main__":
    # Escuta em todas as interfaces, porta 5050
    app.run(host="0.0.0.0", port=5050)
