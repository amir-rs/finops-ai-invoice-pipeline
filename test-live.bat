@echo off
title Run n8n Automated Pipeline Tests
echo ========================================================
echo       Running FinOps Invoice Processing Test Suite
echo ========================================================
echo.
python scripts/run_scenarios.py
echo.
pause
