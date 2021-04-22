@echo off     
cd /d %~dp0
..\..\Tools\py39\python.exe exporter.py -a %*
pause