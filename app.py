from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import json
from werkzeug.utils import secure_filename
from datetime import datetime

# Versão via GitHub - teste de deploy

app = Flask(__name__)

# Libera CORS para as rotas /api/*
CORS(app, resources={r"/api/*": {"origins": "*"}})

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "config" / "users.json"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

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

@app.post("/api/upload")
def upload_file():
    """
    Recebe o arquivo da tela CLT OFF (Facta) e salva no servidor.
    Depois vamos acoplar a automação aqui.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado (campo 'file' não encontrado)."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": "Arquivo sem nome."}), 400

    # Garante nome seguro e prefixo com data/hora
    filename = secure_filename(file.filename)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    final_name = f"{ts}-{filename}"
    dest_path = UPLOAD_DIR / final_name

    try:
        file.save(dest_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Falha ao salvar arquivo: {e}"}), 500

    # Aqui depois você chama a automação de fato (script Selenium, etc.)
    # Exemplo futuro:
    # subprocess.Popen(["python3", "sua_automacao.py", str(dest_path)], ...)

    return jsonify({
        "success": True,
        "message": "Upload realizado com sucesso.",
        "saved_as": final_name
    }), 200

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Porta padrão que estamos usando para a API
    app.run(host="0.0.0.0", port=5050)
