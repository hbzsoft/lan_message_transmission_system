@echo off
setlocal EnableExtensions
chcp 65001 >nul
title LMTS 1.6 Firewall Setup
cd /d "%~dp0"

net session >nul 2>&1
if errorlevel 1 (
    echo Requesting administrator permission...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo Adding LAN-only UDP firewall rules...
for %%R in ("LMTS Discovery UDP" "LMTS Display UDP" "LMTS Reply UDP") do (
    netsh advfirewall firewall delete rule name=%%R >nul 2>nul
)
netsh advfirewall firewall add rule name="LMTS Discovery UDP" dir=in action=allow protocol=UDP localport=54321 remoteip=localsubnet profile=any enable=yes >nul
if errorlevel 1 goto :failed
netsh advfirewall firewall add rule name="LMTS Display UDP" dir=in action=allow protocol=UDP localport=12345 remoteip=localsubnet profile=any enable=yes >nul
if errorlevel 1 goto :failed
netsh advfirewall firewall add rule name="LMTS Reply UDP" dir=in action=allow protocol=UDP localport=14514 remoteip=localsubnet profile=any enable=yes >nul
if errorlevel 1 goto :failed

echo.
echo Firewall setup completed. Run this BAT once on BOTH computers.
pause
exit /b 0

:failed
echo [ERROR] Firewall setup failed. Confirm the administrator prompt.
pause
exit /b 1
