import csv
import os


from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api')
def api():
    empresa = request.args.get('empresa')

    if empresa:
        return jsonify({
            "Empresa": empresa,
            "Divida_2024": 1000,
            "EBITDA_2024": 500,
            "Alavancagem": 2.0,
            "Rating": "🟡 MODERADO"
        })

    return jsonify({"status": "ok"})

# necessário pro Vercel
index = app
