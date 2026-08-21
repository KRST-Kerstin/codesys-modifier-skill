@echo off
setlocal enabledelayedexpansion

set TEMPLATE=%1
set WORKSPACE_NAME=%2
set GATEWAY_IP=%3

if "%TEMPLATE%"=="" (
    echo Usage: run.bat ^<template^> ^<workspace_name^> [gateway_ip]
    echo   gateway_ip is optional - omit to build only, without downloading to a PLC.
    echo.
    python scripts\setup_workspace.py --list
    exit /b 1
)

:: Setup workspace and capture output variables
for /f "tokens=1,2 delims==" %%A in ('python scripts\setup_workspace.py %TEMPLATE% %WORKSPACE_NAME%') do (
    set %%A=%%B
)

if not defined PROJECT_PATH (
    echo ERROR: setup_workspace.py failed.
    exit /b 1
)

echo Workspace : %WORKSPACE_NAME%
echo Project   : %PROJECT_PATH%
echo Profile   : %CODESYS_PROFILE%
if not "%GATEWAY_IP%"=="" echo Gateway   : %GATEWAY_IP%
echo.

:: Step 1 - Export project to XML
set XML_PATH=%WORKSPACE%\export.xml
start "" /b /wait "%CODESYS_EXE%" --noUI --profile="%CODESYS_PROFILE%" ^
    --runscript="%~dp0scripts\export.py" ^
    --scriptargs="%PROJECT_PATH%|%XML_PATH%"
if errorlevel 1 goto :error

:: Step 2 - Modify XML (CPython)
python "%~dp0scripts\modify.py" "%XML_PATH%" "%XML_PATH%"
if errorlevel 1 goto :error

:: Step 3 - Import + build + (optional) download
set IMPORT_ARGS=%PROJECT_PATH%^|%XML_PATH%
if not "%GATEWAY_IP%"=="" set IMPORT_ARGS=%IMPORT_ARGS%^|%GATEWAY_IP%

start "" /b /wait "%CODESYS_EXE%" --noUI --profile="%CODESYS_PROFILE%" ^
    --runscript="%~dp0scripts\import_deploy.py" ^
    --scriptargs="%IMPORT_ARGS%"
if errorlevel 1 goto :error

echo Done.
exit /b 0

:error
echo FAILED.
exit /b 1
