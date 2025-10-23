"""
core/generator.py
Versão corrigida e robusta — compatível com main.py e frontend.
"""

import os
import re
import random
import pandas as pd
from collections import Counter
from statistics import mean

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

LOTERIAS = {
    "lotofacil": {"arquivo": "LOTOFACIL.xlsx", "n": 15, "max": 25},
    "megasena": {"arquivo": "MEGA_SENA.xlsx", "n": 6, "max": 60},
    "quina": {"arquivo": "QUINA.xlsx", "n": 5, "max": 80},
    "diadesorte": {"arquivo": "DIA_DE_SORTE.xlsx", "n": 7, "max": 31},
    "maismilionaria": {"arquivo": "MAIS_MILIONARIA.xlsx", "n": 6, "max": 50},
}


# -------------------------
# Normalização pública
# -------------------------
def normalize_loteria(name: str) -> str:
    """
    Normaliza nomes vindos do frontend para chaves internas:
    retorna uma das: lotofacil, megasena, quina, diadesorte, maismilionaria
    Lança ValueError se não reconhecer.
    """
    if not isinstance(name, str):
        raise ValueError("Nome inválido")
    s = name.strip().lower()
    s = s.replace("+", "mais ").replace("-", " ").replace("_", " ")
    # remover acentos básicos
    s = s.replace("á", "a").replace("à","a").replace("â","a").replace("ã","a")
    s = s.replace("é","e").replace("ê","e").replace("í","i").replace("ó","o").replace("ô","o").replace("õ","o").replace("ú","u").replace("ç","c")
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()

    if "lotof" in s:
        return "lotofacil"
    if "mega" in s and "sena" in s:
        return "megasena"
    if "quina" in s:
        return "quina"
    if "dia" in s and "sorte" in s:
        return "diadesorte"
    if "mais" in s and "milion" in s:
        return "maismilionaria"
    # fallback: exact match keys
    compact = s.replace(" ", "")
    for k in LOTERIAS.keys():
        if compact == k:
            return k
    raise ValueError(f"Loteria desconhecida: '{name}'")


# -------------------------
# Carregar excel (bruto)
# -------------------------
def carregar_dados(loteria: str) -> pd.DataFrame:
    if loteria not in LOTERIAS:
        raise ValueError("Loteria inválida: " + str(loteria))
    arquivo = LOTERIAS[loteria]["arquivo"]
    path = os.path.join(DATA_DIR, arquivo)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    try:
        df = pd.read_excel(path, engine="openpyxl", header=0)
    except Exception:
        df = pd.read_excel(path, header=0)
    return df


# -------------------------
# Detectar colunas de dezenas e metadados
# -------------------------
def detectar_colunas_meta(df: pd.DataFrame, loteria: str):
    max_val = LOTERIAS[loteria]["max"]
    cols = list(df.columns)
    dez_cols = []
    col_data = None
    col_concurso = None
    col_ganhadores = None

    for c in cols:
        low = str(c).lower()
        # detect data, concurso, ganhadores por nome de coluna
        if col_data is None and "data" in low:
            col_data = c
        if col_concurso is None and any(k in low for k in ["concurso", "nr", "numero", "nº", "nro"]):
            col_concurso = c
        if col_ganhadores is None and "ganh" in low:
            col_ganhadores = c

        # testar se coluna contém dezenas válidas (pelo menos 2 valores no range)
        try:
            sample = df[c].dropna().astype(str).head(20).tolist()
            found = 0
            for v in sample:
                s = str(v).strip().replace(".0", "")
                if s.lstrip("-").isdigit():
                    iv = int(s)
                    if 1 <= iv <= max_val:
                        found += 1
            if found >= 2:
                dez_cols.append(c)
        except Exception:
            continue

    # fallback: se não detectou dezenas, tentar as primeiras N colunas
    if not dez_cols:
        expected_n = LOTERIAS[loteria]["n"]
        dez_cols = cols[:expected_n] if len(cols) >= expected_n else cols

    return dez_cols, col_concurso, col_data, col_ganhadores


# -------------------------
# Extrair linhas de dezenas válidas do DataFrame
# -------------------------
def linhas_de_dezenas(df: pd.DataFrame, dez_cols, loteria: str):
    max_val = LOTERIAS[loteria]["max"]
    linhas = []
    for _, row in df.iterrows():
        dezenas = []
        for c in dez_cols:
            v = row.get(c, None)
            if pd.isna(v):
                continue
            s = str(v).strip().replace(".0", "")
            if s.lstrip("-").isdigit():
                iv = int(s)
                if 1 <= iv <= max_val:
                    dezenas.append(iv)
        if dezenas:
            linhas.append(sorted(dezenas))
    return linhas


# -------------------------
# Últimos resultados formatados
# -------------------------
def ultimos_resultados(loteria: str, n: int = 2):
    df = carregar_dados(loteria)
    dez_cols, col_concurso, col_data, col_ganhadores = detectar_colunas_meta(df, loteria)

    ult = []
    tail = df.tail(n)
    for _, row in tail.iterrows():
        # concurso
        concurso = ""
        if col_concurso and not pd.isna(row.get(col_concurso, None)):
            try:
                concurso = int(row[col_concurso])
            except Exception:
                concurso = str(row[col_concurso])
        # data
        data_s = ""
        if col_data and not pd.isna(row.get(col_data, None)):
            try:
                data_s = pd.to_datetime(row[col_data]).strftime("%d/%m/%Y")
            except Exception:
                data_s = str(row[col_data])
        # numeros: coletar somente números válidos dentro do intervalo
        numeros = []
        for c in dez_cols:
            v = row.get(c, None)
            if pd.isna(v):
                continue
            s = str(v).strip().replace(".0", "")
            if s.lstrip("-").isdigit():
                iv = int(s)
                if 1 <= iv <= LOTERIAS[loteria]["max"]:
                    numeros.append(iv)
        numeros = sorted(numeros)
        # ganhadores
        ganhadores = "Sem ganhador"
        if col_ganhadores and not pd.isna(row.get(col_ganhadores, None)):
            val = row[col_ganhadores]
            s = str(val).strip()
            if s != "":
                ganhadores = s if not s.isdigit() else str(int(s))
        if numeros:
            ult.append({
                "concurso": concurso,
                "numeros": numeros,
                "ganhadores": ganhadores,
                "data": data_s
            })
    return {"ultimos": ult}


# -------------------------
# Gerar análise matemática
# -------------------------
def gerar_analise(loteria: str):
    df = carregar_dados(loteria)
    dez_cols, _, _, _ = detectar_colunas_meta(df, loteria)
    linhas = linhas_de_dezenas(df, dez_cols, loteria)
    if not linhas:
        return {"erro": "Sem dados válidos para análise."}

    # Frequências e TOP10
    todas = [n for l in linhas for n in l]
    freq = Counter(todas)
    top10 = [n for n, _ in freq.most_common(10)]

    # números mais atrasados: usamos posição de última aparição nas linhas
    total = len(linhas)
    last_seen = {}
    for idx, linha in enumerate(linhas):
        for n in linha:
            last_seen[n] = idx
    # gerar atraso para todos números do universo (se nunca visto, atraso = total)
    atrasos = []
    for num in range(1, LOTERIAS[loteria]["max"] + 1):
        if num in last_seen:
            atraso = (total - 1) - last_seen[num]
        else:
            atraso = total
        atrasos.append((num, atraso))
    atrasos_sorted = sorted(atrasos, key=lambda x: (-x[1], x[0]))
    numeros_mais_atrasados = [n for n, _ in atrasos_sorted[:10]]

    resultado = {
        "total_concursos": total,
        "top10": top10,
        "numeros_mais_atrasados": numeros_mais_atrasados
    }

    # média pares/ímpares apenas para lotofacil
    if loteria == "lotofacil":
        pares = [sum(1 for n in l if n % 2 == 0) for l in linhas]
        impares = [sum(1 for n in l if n % 2 == 1) for l in linhas]
        resultado["media_pares"] = round(mean(pares), 2) if pares else 0
        resultado["media_impares"] = round(mean(impares), 2) if impares else 0

    return resultado


# -------------------------
# Gerar palpites (mantido simples / não mexer)
# -------------------------
def gerar_palpite_inteligente(loteria: str, quantidade: int = 5, dezenas_por_jogo: int = None):
    if loteria not in LOTERIAS:
        raise ValueError("Loteria inválida")
    cfg = LOTERIAS[loteria]
    n = cfg["n"] if dezenas_por_jogo is None else int(dezenas_por_jogo)
    universo = list(range(1, cfg["max"] + 1))
    jogos = [sorted(random.sample(universo, n)) for _ in range(int(quantidade))]
    return {"jogos": jogos}


# -------------------------
# Simulador de acertos
# -------------------------
def simular_acertos(loteria: str, dezenas_sorteadas, jogos=None):
    if not isinstance(dezenas_sorteadas, (list, tuple)):
        return {"erro": "Dezenas sorteadas inválidas."}
    if jogos is None or not isinstance(jogos, (list, tuple)):
        return {"erro": "Forneça a lista de jogos a serem simulados (parâmetro 'jogos')."}
    resultados = []
    for i, jogo in enumerate(jogos, start=1):
        try:
            acertos = len(set(jogo) & set(dezenas_sorteadas))
        except Exception:
            acertos = 0
        resultados.append({"jogo": i, "acertos": int(acertos)})
    return {"resultados": resultados}
