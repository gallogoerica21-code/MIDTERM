@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if not errorlevel 1 (
	py -3 main.py %*
) else (
	python main.py %*
)

if errorlevel 1 (
	echo.
	echo The application could not start. Check that Python and requirements.txt dependencies are installed.
	pause
	exit /b 1
)
