from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
import json
import subprocess
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

BASE_DIR = Path(__file__).resolve().parent

USERS_FILE = BASE_DIR / "config" / "users.json"
UPLOAD_DIR = BASE_DIR / "uploads"
LOG_DIR = BASE_DIR / "logs"
AUTOMATION_DIR = BASE_DIR / "automation"
AUTOMATION_SCRIPT = AUTOMATION_DIR / "facta_clt_off.py"
STATUS_FILE = BASE_DIR / "status_facta.json"

# garante pastas
UPLOAD_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
AUTOMATION_DIR.mkdir(exist_ok=True)


# =============== FUNÇÕES AUXILIARES ===============

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERRO] users.json não encontrado em {USERS_FILE}")
        return []
    except Exception as e:
        print(f"[ERRO] Falha ao ler users.json: {e}")
        return []


def save_status(data: dict):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Não consegui salvar status_facta.json: {e}")


def load_status():
    try:
        if not STATUS_FILE.exists():
            return None
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Não consegui ler status_facta.json: {e}")
        return None


# =============== LOGIN ===============

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    users = load_users()
    for u in users:
        if u.get("username") == username and u.get("password") == password and u.get("active", True):
            return jsonify({
                "ok": True,
                "role": u.get("role", "user"),
                "username": username
            }), 200

    return jsonify({"ok": False, "error": "Usuário ou senha inválidos."}), 401


# =============== UPLOAD + DISPARO DA AUTOMAÇÃO ===============

def _handle_upload_facta():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado (campo file)."}), 400

    file = request.files["file"]

    if not file or file.filename == "":
        return jsonify({"success": False, "error": "Arquivo inválido."}), 400

    # nome seguro + timestamp
    safe_name = secure_filename(file.filename)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    final_name = f"facta_{ts}_{safe_name}"

    dest_path = UPLOAD_DIR / final_name

    try:
        file.save(dest_path)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Falha ao salvar arquivo: {e}",
        }), 500

    # define log da automação
    log_file = LOG_DIR / f"facta_{ts}.log"

    # registra status INICIAL
    status_data = {
        "status": "PROCESSANDO",
        "file": final_name,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "finished_at": None,
        "log_file": str(log_file.name),
        # por enquanto, o arquivo processado é o próprio arquivo na pasta uploads
        "output_file": final_name,
    }
    save_status(status_data)

    # monta comando da automação
    cmd = [
        "python3",
        str(AUTOMATION_SCRIPT),
        "--input",
        str(dest_path),
        "--log-dir",
        str(LOG_DIR),
    ]

    try:
        # aqui está SÍNCRONO: a rota só devolve depois da automação terminar
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )

        status_data["finished_at"] = datetime.now().isoformat(timespec="seconds")

        if result.returncode == 0:
            status_data["status"] = "CONCLUIDO"
            msg = "Arquivo enviado com sucesso! A higienização foi iniciada e finalizou sem erro."
            ok = True
        else:
            status_data["status"] = "ERRO"
            msg = f"Automação retornou código {result.returncode}."
            ok = False
            print("[ERRO] STDOUT:", result.stdout)
            print("[ERRO] STDERR:", result.stderr)

        save_status(status_data)

        return jsonify({
            "success": ok,
            "message": msg,
            "saved_as": final_name,
            "status": status_data["status"],
        }), 200 if ok else 500

    except Exception as e:
        status_data["finished_at"] = datetime.now().isoformat(timespec="seconds")
        status_data["status"] = "ERRO"
        save_status(status_data)

        print(f"[ERRO] Falha ao executar automação: {e}")
        return jsonify({
            "success": False,
            "error": f"Falha ao executar automação: {e}",
        }), 500


@app.post("/api/facta/upload")
def upload_facta():
    return _handle_upload_facta()


# =============== STATUS DA ÚLTIMA EXECUÇÃO ===============

@app.get("/api/facta/status")
def facta_status():
    data = load_status()
    if not data:
        return jsonify({"has_job": False}), 200

    return jsonify({
        "has_job": True,
        **data,
    }), 200


# =============== DOWNLOAD DO ARQUIVO PROCESSADO ===============

@app.get("/api/facta/download")
def facta_download():
    data = load_status()
    if not data or not data.get("output_file"):
        return jsonify({"error": "Nenhum arquivo processado disponível."}), 404

    filename = data["output_file"]
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        return jsonify({"error": "Arquivo processado não foi encontrado no servidor."}), 404

    return send_from_directory(
        UPLOAD_DIR,
        filename,
        as_attachment=True,
    )


# =============== ROTA DE TESTE ===============

@app.get("/api/ping")
def ping():
    return jsonify({"message": "pong"})


if __name__ == "__main__":
    # somente para desenvolvimento (em produção usamos systemd + gunicorn/uwsgi)
    app.run(host="0.0.0.0", port=5050)
