@echo off
REM Launches Tab Copier. Right-click this file and "Run as administrator"
REM if Tab presses aren't being detected in the other app (some apps,
REM like ones running elevated, block key hooks from non-elevated processes).
cd /d "%~dp0"
python tab_copier.py
pause
