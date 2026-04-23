from flask import Flask, request, jsonify
import csv
import os
import unicodedata

app = Flask(__name__)

dados_cache = None

# =========================
# NORMALIZAR TEXTO
# =========================
def limpar_texto(texto):
    return unicodedata.normalize('NFKD', texto)\
        .encode('ascii', 'ignore')\
        .decode('utf-8')\
        .lower().strip()

# =========================
# CARREGAR DADOS
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
                empresa = row[0]

                divida_2024 = float(row[3].replace(',', '') or 0)
                divida_2023 = float(row[2].replace(',', '') or 0)

                ebitda_2024 = float(row[9].replace(',', '') or 0)
                ebitda_2023 = float(row[8].replace(',', '') or 0)

                alavancagem = divida_2024 / ebitda_2024 if ebitda_2024 != 0 else None

                crescimento_divida = (
                    (divida_2024 - divida_2023) / divida_2023
                    if divida_2023 != 0 else 0
                )

                crescimento_ebitda = (
                    (ebitda_2024 - ebitda_2023) / ebitda_2023
                    if ebitda_2023 != 0 else 0
                )

                dados.append({
                    "Empresa": empresa,
                    "Divida_2024": divida_2024,
                    "EBITDA_2024": ebitda_2024,
                    "Alavancagem": round(alavancagem, 2) if alavancagem else None,
                    "Crescimento_Divida": crescimento_divida,
                    "Crescimento_EBITDA": crescimento_ebitda
                })

            except:
                continue

    dados_cache = dados
    return dados_cache


# =========================
# PROBABILIDADE (HEURÍSTICA)
# =========================
def calcular_probabilidade(d):
    if d["Alavancagem"] is None:
        return 1.0

    score = 0

    if d["Alavancagem"] < 2:
        score += 0.05
    elif d["Alavancagem"] < 4.5:
        score += 0.15
    else:
        score += 0.35

    if d["Crescimento_Divida"] > 0.3:
        score += 0.2

    if d["Crescimento_EBITDA"] < 0:
        score += 0.2

    return min(score, 0.95)


# =========================
# API
# =========================
@app.route('/api')
def api():
    tipo = request.args.get('tipo', '')
    empresa_query = request.args.get('empresa', '')

    dados = carregar_dados()

    # 🔥 RANKING
    if tipo == "top-risk":
        filtrado = [d for d in dados if d["Alavancagem"] is not None]
        ordenado = sorted(filtrado, key=lambda x: x["Alavancagem"], reverse=True)
        return jsonify(ordenado[:10])

    # 🔎 BUSCA
    if empresa_query:
        query = limpar_texto(empresa_query)

        resultados = []

        for item in dados:
            nome = limpar_texto(item["Empresa"])

            if query in nome:
                prob = calcular_probabilidade(item)
                item["Prob_Default"] = round(prob, 3)
                resultados.append(item)

        return jsonify(resultados[:10])

    return jsonify({"status": "ok"})


# =========================
# VERCEL HANDLER
# =========================
def handler(environ, start_response):
    return app(environ, start_response)
