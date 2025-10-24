# main.py — versão otimizada da Sortemática (carregamento rápido dos resultados)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
from core.generator import gerar_palpite_inteligente, gerar_analise

app = FastAPI()

# --- Pastas padrão ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Caminho dos arquivos Excel ---
DATA_PATH = "data"

# --- Cache global ---
cache_resultados = {}
cache_analises = {}

# --- Funções auxiliares ---

def carregar_resultados_excel():
    """Carrega todos os arquivos Excel uma única vez e guarda em cache."""
    resultados = {}
    for nome in ["LOTOFACIL", "MEGA_SENA", "QUINA", "MAIS_MILIONARIA", "DIA_DE_SORTE"]:
        caminho = os.path.join(DATA_PATH, f"{nome}.xlsx")
        if not os.path.exists(caminho):
            continue
        try:
            df = pd.read_excel(caminho)
            df = df.dropna(how="all")
            df.columns = [str(c).strip().lower() for c in df.columns]

            # Identifica colunas relevantes
            col_concurso = next((c for c in df.columns if "concurso" in c), None)
            col_data = next((c for c in df.columns if "data" in c), None)
            col_ganhador = next((c for c in df.columns if "ganh" in c), None)

            # Obtém dezenas (todas as colunas numéricas entre 1 e 80)
            dezenas = [c for c in df.columns if c.isdigit() or c.strip().isdigit()]
            if not dezenas:
                dezenas = [c for c in df.columns if "dezena" in c or "bola" in c]

            # Pega o último sorteio
            ultimo = df.iloc[-1]
            numeros = [
                str(int(ultimo[d])) for d in dezenas
                if str(ultimo[d]).strip().isdigit()
            ]
            numeros_fmt = ",".join([f"{int(n):02d}" for n in numeros])

            concurso = str(ultimo[col_concurso]) if col_concurso else "?"
            ganhadores = str(ultimo[col_ganhador]) if col_ganhador else "Sem info"
            data = str(ultimo[col_data]) if col_data else "Sem data"

            resultados[nome] = {
                "concurso": concurso,
                "numeros": numeros_fmt,
                "ganhadores": ganhadores,
                "data": data
            }
        except Exception as e:
            print(f"[Erro ao ler {nome}]: {e}")
    return resultados


def carregar_analises_iniciais():
    """Gera e guarda as análises iniciais em cache para cada jogo."""
    analises = {}
    for nome in ["lotofacil", "megasena", "quina", "maismilionaria", "diadesorte"]:
        try:
            analises[nome] = gerar_analise(nome)
        except Exception as e:
            analises[nome] = f"Erro ao gerar análise: {e}"
    return analises


# --- Inicialização com cache ---
print("🔄 Carregando resultados iniciais...")
cache_resultados = carregar_resultados_excel()
print("✅ Resultados carregados com sucesso!")

print("🔄 Gerando análises iniciais...")
cache_analises = carregar_analises_iniciais()
print("✅ Análises geradas com sucesso!")


# --- Rotas ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "resultados": cache_resultados,
        },
    )


@app.get("/lotofacil", response_class=HTMLResponse)
async def lotofacil(request: Request):
    return templates.TemplateResponse(
        "lotofacil.html",
        {
            "request": request,
            "analise": cache_analises.get("lotofacil", ""),
        },
    )


@app.get("/megasena", response_class=HTMLResponse)
async def megasena(request: Request):
    return templates.TemplateResponse(
        "megasena.html",
        {
            "request": request,
            "analise": cache_analises.get("megasena", ""),
        },
    )


@app.get("/quina", response_class=HTMLResponse)
async def quina(request: Request):
    return templates.TemplateResponse(
        "quina.html",
        {
            "request": request,
            "analise": cache_analises.get("quina", ""),
        },
    )


@app.get("/maismilionaria", response_class=HTMLResponse)
async def maismilionaria(request: Request):
    return templates.TemplateResponse(
        "maismilionaria.html",
        {
            "request": request,
            "analise": cache_analises.get("maismilionaria", ""),
        },
    )


@app.get("/diadesorte", response_class=HTMLResponse)
async def diadesorte(request: Request):
    return templates.TemplateResponse(
        "diadesorte.html",
        {
            "request": request,
            "analise": cache_analises.get("diadesorte", ""),
        },
    )


@app.get("/gerar/{jogo}")
async def gerar_palpite(jogo: str):
    try:
        palpites = gerar_palpite_inteligente(jogo)
        return {"palpites": palpites}
    except Exception as e:
        return {"erro": str(e)}


# --- Rodando localmente ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
