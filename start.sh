#!/usr/bin/env bash
# Inicia o servidor FastAPI com Uvicorn (produção)
exec uvicorn main:app --host 0.0.0.0 --port 10000

