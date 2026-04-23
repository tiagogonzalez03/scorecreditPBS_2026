from flask import Flask, request, jsonify
import csv
import os

app = Flask(__name__)

# =========================
# FUNÇÃO PARA LER O CSV
# =========================
def carregar_dados():
    base_path = os.path.dirname(__file__)
    file_path = os.path.abspath(
        os.path.join(base_path, '..', 'data', 'SPGlobal_Export_4-14-2026_FinalVersion.csv')
    )

    dados = []

    with open(file_path, newline='', encoding='latin-1') as csvfile:
        reader = csv.reader(csvfile)

        for _ in range(5):
            next(reader, None)

        for row in reader:
            try:
                empresa = row[0].split(' (')[0]
                divida = float(row[3].replace(',', '') or 0)
                ebitda = float(row[9].replace(',', '') or 0)

                alavancagem = round(divida / ebitda, 2) if ebitda != 0 else None

                if ebitda <= 0 or alavancagem is None:
                    rating = '🔴 CRÍTICO'
                elif alavancagem > 4.5:
                    rating = '🔴 ALTO RISCO'
                elif alavancagem < 2.0:
                    rating = '🟢 BAIXO RISCO'
                else:
                    rating = '🟡 MODERADO'

                dados.append({
                    "Empresa": empresa,
                    "Divida_2024": divida,
                    "EBITDA_2024": ebitda,
                    "Alavancagem": alavancagem,
                    "Rating": rating
                })

            except:
                continue

    return dados


# =========================
# ROTA DA API
# =========================
@app.route('/api')
def api():
    empresa_query = request.args.get('empresa', '').lower()

    dados = carregar_dados()

    if empresa_query:
        resultados = [
            item for item in dados
            if empresa_query in item["Empresa"].lower()
        ]

        return jsonify(resultados[:10])  # sugestões

    return jsonify({"status": "ok"})


# necessário para o Vercel
index = app
