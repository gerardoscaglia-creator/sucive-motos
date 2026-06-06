@echo off
cd /d "%~dp0"
start "" http://localhost:3140/index.html
python serve.py
