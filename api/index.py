from flask import Flask, jsonify

app = Flask(__name__)

# =========================
# DEBUG - LISTAR ARQUIVOS
# =========================
@app.route('/api')
def api():
    import os

    files = []

    for root, dirs, filenames in os.walk('.'):
        for f in filenames:
            files.append(os.path.join(root, f))

    return jsonify({
        "files": files
    })


# =========================
# VERCEL HANDLER
# =========================
def handler(environ, start_response):
    return app(environ, start_response)
