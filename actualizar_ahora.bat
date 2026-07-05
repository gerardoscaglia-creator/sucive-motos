@echo off
REM Actualiza los datos de SUCIVE ahora mismo (sin esperar al dia 5).
REM Baja el ultimo PDF, valida, reconstruye el dataset y lo sube a la web.
cd /d "%~dp0"
echo == Bajando y parseando SUCIVE ==
python capture.py || goto :err
echo == Reconstruyendo dataset ==
python build_dataset.py || goto :err
echo == Subiendo a GitHub (la web se actualiza sola) ==
git add data/ pdfs/ dataset.json
git diff --staged --quiet && (echo Sin cambios: SUCIVE todavia no publico un mes nuevo. & goto :fin)
for /f "tokens=1-2 delims=/ " %%a in ("%date%") do set HOY=%%c
git commit -m "Datos SUCIVE (carga manual)"
git push || goto :err
echo LISTO. En 1-2 minutos la pagina online queda al dia.
goto :fin
:err
echo.
echo ERROR: algo fallo. Si SUCIVE cambio el formato, el script aborta solo para no pisar datos buenos.
:fin
echo.
pause
