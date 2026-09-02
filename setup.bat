@echo off
echo ========================================
echo  ANEXO RISK - Setup rapido
echo ========================================

cd /d %~dp0

echo.
echo [1/4] Creando entorno virtual...
cd backend
python -m venv venv

echo.
echo [2/4] Activando entorno e instalando dependencias...
call venv\Scripts\activate
pip install -r requirements.txt -q

echo.
echo [3/4] Iniciando base de datos...
python -c "from db.database import init_db; init_db()"
python seed_es.py

echo.
echo ========================================
echo  Tudo pronto! Agora abre 2 terminales:
echo.
echo  Terminal 1 (Backend):
echo    cd backend
echo    venv\Scripts\activate
echo    python -m uvicorn main:app --port 8000
echo.
echo  Terminal 2 (Frontend):
echo    cd frontend
echo    python -m http.server 3000
echo.
echo  Luego abre: http://localhost:3000
echo ========================================
pause
