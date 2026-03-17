@echo off
echo ============================================
echo  KeplerDB — Subir a GitHub
echo ============================================
echo.
echo 1. Ve a https://github.com/new
echo 2. Nombre del repo: KeplerDB
echo 3. SIN inicializar (no README, no .gitignore)
echo 4. Pulsa "Create repository"
echo 5. Vuelve aqui y ejecuta:
echo.
echo    git remote add origin https://github.com/eduardoddddddd/KeplerDB.git
echo    git branch -M master
echo    git push -u origin master
echo.
echo O ejecuta directamente este script con tu usuario:
echo.
set /p USUARIO="Tu usuario de GitHub: "
cd /d "%~dp0"
git remote add origin https://github.com/%USUARIO%/KeplerDB.git
git branch -M master
git push -u origin master
pause
