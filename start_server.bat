@echo off
"C:\Users\spide\.local\bin\uv.exe" run uvicorn server:app --host 0.0.0.0 --port 8083
pause