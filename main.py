import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core import generator

app = FastAPI(title="Sortemática - Simulador e Gerador de Palpites")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# PÁGINAS HTML
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/lotofacil", response_class=HTMLResponse)
def lotofacil(request: Request):
    return templates.TemplateResponse("lotofacil.html", {"request": request})


@app.get("/megasena", response_class=HTMLResponse)
def megasena(request: Request):
    return templates.TemplateResponse("megasena.html", {"request": request})


@app.get("/quina", response_class=HTMLResponse)
def quina(request: Request):
    return templates.TemplateResponse("quina.html", {"request": request})


@app.get("/diadesorte", response_class=HTMLResponse)
def diadesorte(request: Request):
    return templates.TemplateResponse("diadesorte.html", {"request": request})


@app.get("/maismilionaria", response_class=HTMLResponse)
def maismilionaria(request: Request):
    return templates.TemplateResponse("maismilionaria.html", {"request": request})


# APIs — todas normalizam o nome da loteria e retornam JSON sempre (com campo "erro" se falhar)
def _normalize(name: str) -> str:
    return generator.normalize_loteria(name)


@app.get("/api/analisar/{loteria}")
def api_analisar(loteria: str):
    lot = _normalize(loteria)
    try:
        resultado = generator.gerar_analise(lot)
        if isinstance(resultado, dict) and resultado.get("erro"):
            return JSONResponse(resultado)
        return JSONResponse(resultado)
    except Exception as e:
        return JSONResponse({"erro": f"{e}"})  # sempre retornar 200 com erro no JSON


@app.get("/api/palpite/{loteria}")
def api_palpite(loteria: str, quantidade: int = 5, dezenas_por_jogo: int = None):
    lot = _normalize(loteria)
    try:
        resultado = generator.gerar_palpite_inteligente(lot, quantidade=quantidade, dezenas_por_jogo=dezenas_por_jogo)
        # garantia de formato
        if not isinstance(resultado, dict):
            resultado = {"jogos": resultado}
        return JSONResponse(resultado)
    except Exception as e:
        return JSONResponse({"erro": f"{e}"})


@app.post("/api/simular/{loteria}")
async def api_simular(loteria: str, request: Request):
    lot = _normalize(loteria)
    body = await request.json()
    dezenas = body.get("dezenas", [])
    jogos = body.get("jogos", None)
    try:
        resultado = generator.simular_acertos(lot, dezenas, jogos=jogos)
        return JSONResponse(resultado)
    except Exception as e:
        return JSONResponse({"erro": f"{e}"})


@app.get("/api/ultimos/{loteria}")
def api_ultimos(loteria: str, n: int = 1):
    lot = _normalize(loteria)
    try:
        r = generator.ultimos_resultados(lot, n=n)
        return JSONResponse(r)
    except Exception as e:
        return JSONResponse({"erro": f"{e}"})


if __name__ == "__main__":
    print("Servidor iniciado: http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
