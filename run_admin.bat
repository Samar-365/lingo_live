@echo off
:: Run as Administrator
powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && python main.py && pause' -Verb RunAs"
