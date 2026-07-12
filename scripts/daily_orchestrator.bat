@echo off
rem ============================================================
rem Daily Orchestrator for stock-analysis-FIL
rem Unified daily pipeline: backup → fetch → update → notify
rem
rem Usage:
rem   daily_orchestrator.bat              (all steps)
rem   daily_orchestrator.bat --step backup
rem   daily_orchestrator.bat --step fetch --step update
rem   daily_orchestrator.bat --step all
rem
rem Called by Windows Task Scheduler or run manually.
rem ============================================================

rem Change to project root (this script lives in scripts\)
cd /d "%~dp0.."

if not exist logs mkdir logs

rem Use venv python if available, otherwise system python
set PY=python
if exist "venv\Scripts\python.exe" set PY=venv\Scripts\python.exe

echo [%date% %time%] daily_orchestrator start >> logs\orchestrator_run.log

rem Forward all command-line arguments (--step ...) to the Python script
"%PY%" scripts\daily_orchestrator.py %*

set EXIT_CODE=%errorlevel%

echo [%date% %time%] daily_orchestrator end (exit %EXIT_CODE%) >> logs\orchestrator_run.log

exit /b %EXIT_CODE%
