@echo off
title Zero Trust Continuous Biometric Authentication Agent
color 0b

echo =====================================================================
echo    ZERO TRUST OS CONTINUOUS BIOMETRIC AUTHENTICATION AGENT
echo =====================================================================
echo  Monitoring: ALL Windows Applications in background
echo  Backend:    https://continuous-biometric-authenticationnn-production-4039.up.railway.app/api
echo =====================================================================
echo.

set /p USERNAME="Enter your username [default: santhu_01]: " || set USERNAME=santhu_01
if "%USERNAME%"=="" set USERNAME=santhu_01

set /p PASSWORD="Enter your password: "

echo.
echo Starting background continuous monitoring...
echo Press Ctrl+C at any time to stop the agent.
echo.

.\.venv\Scripts\python.exe desktop_agent\agent.py --username %USERNAME% --password %PASSWORD%

pause
