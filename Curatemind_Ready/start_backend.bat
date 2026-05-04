@echo off
cd /d "C:\Users\gs430\Desktop\major"
call .venv\Scripts\activate
python -m uvicorn html.main:app --reload
pause