@echo off
setlocal
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0tr1604_sim_v6.py"
) else (
  python "%~dp0tr1604_sim_v6.py"
)
if errorlevel 1 pause
