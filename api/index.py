from flask import Flask, request, jsonify
import csv
import os
import numpy as np

from sklearn.linear_model import LogisticRegression

app = Flask(__name__)

dados_cache = None
modelo = None

# =========================
# CARREGAR E PREPARAR DADOS
# =========================
def carregar_dados():
    global dados_cache

    if dados_cache is not None:
        return dados_cache

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

                divida_2024 = float(row[3].replace(',', '') or 0)
                divida_2023 = float(row[2].replace(',', '') or 0)

                ebitda_2024 = float(row[9].replace(',', '') or 0)
                ebitda_2023 = float(row[8].replace(',', '') or 0)

                alavancagem = divida_2024 / ebitda_2024 if ebitda_2024 != 0 else None

                # crescimento
                crescimento_divida = (divida_2024 - divida_2023) / divida_2023 if divida_2023 != 0 else 0
                crescimento_ebitda = (ebitda_2024 - ebitda_2023) / ebitda_2023 if ebitda_2023 != 0 else 0

                # proxy de default
                default = 1 if (alavancagem and alavancagem > 5 and crescimento_divida > 0) else 0

                dados.append({
                    "Empresa": empresa,
                    "Divida_2024": divida_2024,
                    "EBITDA_2024": ebitda_2024,
                    "Alavancagem": round(alavancagem, 2) if alavancagem else None,
                    "Crescimento_Divida": crescimento_divida,
                    "Crescimento_EBITDA": crescimento_ebitda,
                    "Default": default
                })

            except:
                continue

    dados_cache = dados
    return dados_cache


# =========================
# TREINAR MODELO
# =========================
def treinar_modelo():
    global modelo

    if modelo is not None:
        return modelo

    dados = carregar_dados()

    X = []
    y = []

    for d in dados:
        if d["Alavancagem"] is not None:
            X.append([
                d["Alavancagem"],
                d["Crescimento_Divida"],
                d["Crescimento_EBITDA"]
            ])
            y.append(d["Default"])

    modelo = LogisticRegression()
    modelo.fit(X, y)

    return modelo


# =========================
# API
# =========================
@app.route('/api')
def api():
    tipo = request.args.get('tipo', '')
    empresa_query = request.args.get('empresa', '').lower()

    dados = carregar_dados()

    # ranking
    if tipo == "top-risk":
        filtrado = [d for d in dados if d["Alavancagem"] is not None]
        ordenado = sorted(filtrado, key=lambda x: x["Alavancagem"], reverse=True)
        return jsonify(ordenado[:10])

    # busca + previsão
    if empresa_query:
        resultados = [
            item for item in dados
            if empresa_query in item["Empresa"].lower()
        ]

        if not resultados:
            return jsonify([])

        item = resultados[0]

        modelo = treinar_modelo()

        if item["Alavancagem"] is not None:
            prob = modelo.predict_proba([[
                item["Alavancagem"],
                item["Crescimento_Divida"],
                item["Crescimento_EBITDA"]
            ]])[0][1]
        else:
            prob = 1.0

        item["Prob_Default"] = round(float(prob), 3)

        return jsonify([item])

    return jsonify({"status": "ok"})


index = app
