---
name: codesys-modifier
description: >
  Automate CODESYS 3.5 SP17+ project modification via CLI on Windows.
  Use this skill whenever the user wants to: export a CODESYS .project to XML,
  modify ST code / VAR blocks / FBD / task config in that XML, import it back,
  build, or download to a PLC — all from the terminal without the GUI.
  Trigger on any mention of CODESYS scripting, --noUI, runscript, PLCopen XML
  modification, automated PLC deployment, or headless CODESYS workflows.
allowed-tools: |
  bash: python, cmd, powershell
---

# CODESYS Project Modifier Skill

Automates the full cycle: **export → XML edit → import → build → download** using
`CODESYS.exe --noUI --runscript=<script.py>`.

Scripts run inside CODESYS's embedded IronPython 2.7 interpreter. Standard Python
stdlib is available; third-party CPython packages are NOT (no pip, no .venv).

---

## Architecture

```
Terminal (cmd/PowerShell)
  └─ CODESYS.exe --noUI --profile="..." --runscript="script.py" [--scriptargs "..."]
       └─ IronPython (hosted inside CODESYS)
            └─ scriptengine API  ← implicit: from scriptengine import *
                 ├─ projects      (open/save/close)
                 ├─ online        (connect/login/download/run)
                 └─ system        (write_message, delay, exit)
```

XML editing happens **outside** CODESYS using a regular Python script (CPython 3.x
or any tool). The IronPython script only handles open/export/import/build/deploy.

Recommended two-script pattern:
1. `export.py`  — IronPython: open .project, export XML, close
2. `modify.py`  — CPython: parse & edit XML (ElementTree / lxml)
3. `import_deploy.py` — IronPython: open .project, import XML, build, download

---

## CLI Invocation

```bat
"C:\Program Files\CODESYS 3.5.17.x\CODESYS\Common\CODESYS.exe" ^
  --noUI ^
  --profile="CODESYS V3.5 SP17 Patch x" ^
  --runscript="C:\scripts\export.py" ^
  --scriptargs="C:\projects\MyProject.project|C:\tmp\export.xml"
```

**Gotchas:**
- `--profile` string must match exactly what appears in CODESYS's profile list (case-sensitive, with patch suffix). Wrong string = GUI opens instead of --noUI.
- Use `start /b /wait` in batch files to block until CODESYS exits.
- `--scriptargs` passes a single string. Use `|` as separator between paths — space will break paths containing spaces:
  ```python
  args = [a.strip() for a in system.get_scriptargs().split("|")]
  project_path, xml_path = args[0], args[1]
  ```
- Use `%~dp0` in batch files for paths relative to the batch file location, not CWD.
- stdout from `system.write_message(Severity.Information, "...")` goes to terminal in --noUI mode.

---

## Export Script (IronPython)

**File:** `scripts/export.py`

Accepts args: `<project_path> <xml_output_path>`

**Note:** `declarations_as_plaintext=True` is critical — without it, VAR block text
is stored in a structured XML form that is harder to round-trip safely.

---

## XML Modification Script (CPython)

**File:** `scripts/modify.py`

Accepts args: `<xml_input_path> <xml_output_path>`

Template script — implement modifications in the `main()` function.
Helper functions `find_pou()`, `set_st_body()`, `set_declaration()` are provided.
See `references/xml-schema.md` for full node paths for VAR, FBD, task config.

---

## Import + Build + Download Script (IronPython)

**File:** `scripts/import_deploy.py`

Accepts args: `<project_path> <modified_xml_path> [<gateway_ip>]`

`gateway_ip` is optional — omit to build only without downloading.

**Download options** (edit in script if needed):
- `OnlineChangeOption.Try` — online change if delta compatible, else full download
- `OnlineChangeOption.Full` — always full download
- `OnlineChangeOption.None_` — compile only, no download

---

## Agent Workflow

When the user asks to modify a CODESYS project, follow these steps:

1. **Determine template** — ask which product/template to use, or check `templates.json`
2. **Create workspace** — run `setup_workspace.py <template> <workspace_name>`
3. **Generate modify.py** — write the XML modification code into `scripts/modify.py` based on what the user wants changed (ST body, VAR declaration, task config, etc.). Use helper functions already in the file and `references/xml-schema.md` for node paths.
4. **Run `run.bat`** from the skill root directory (CWD matters — paths in the batch are relative)
5. **Report results** — show build output and confirm download if gateway was specified

If the user only wants to build without downloading, omit the gateway IP argument to `import_deploy.py`.

**Note on paths with spaces:** `--scriptargs` uses `|` as separator between arguments (not space). This is already handled in `export.py`, `import_deploy.py`, and `run.bat`.

---

## Batch Orchestration (run.bat)

Use `run.bat` from the Template System section below. Run it from the skill root directory so relative script paths resolve correctly.

**Quick reference — args passed to scripts use `|` separator:**
```bat
--scriptargs="%PROJECT_PATH%|%XML_PATH%"
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| GUI opens despite --noUI | Wrong `--profile` string | Copy exact string from CODESYS Help > About |
| `ModuleNotFoundError: scriptengine.dotNETs` | Running in CPython, not IronPython | Only run scriptengine scripts via `CODESYS.exe --runscript` |
| Import places objects in wrong location | Wrong selection context during import | Call `import_xml` on `proj` not on `app` for top-level objects |
| Task config missing after round-trip | Task config lives in `<addData>`, not standard PLCopen | See `references/xml-schema.md` — task config section |
| `has_compile_error` always False | Check `app.messages` for warnings treated as errors | Iterate `app.messages` and log them |
| Online change rejected | Delta too large or memory layout changed | Use `OnlineChangeOption.Full` |

---

## Template System

Users register named product templates in `templates.json`. Each template is a
base `.project` file. When starting work, `setup_workspace.py` copies the chosen
template into a new workspace directory — the original is never touched.

### 1. Register templates — edit `templates.json`

```json
{
  "templates": {
    "pdm360": {
      "description": "IFM PDM360 panel project base",
      "project": "C:\\templates\\pdm360_base.project",
      "codesys_profile": "CODESYS V3.5 SP17 Patch 20"
    },
    "my_other_product": {
      "description": "...",
      "project": "C:\\templates\\other_base.project",
      "codesys_profile": "CODESYS V3.5 SP17 Patch 20"
    }
  },
  "defaults": {
    "workspace_root": "C:\\codesys-workspaces",
    "codesys_exe": "C:\\Program Files\\CODESYS 3.5.17.20\\CODESYS\\Common\\CODESYS.exe"
  }
}
```

Fields per template:
- `project` — absolute path to the base `.project` file (never modified)
- `codesys_profile` — exact profile string for `--profile` (copy from CODESYS Help > About)
- `description` — human label shown by `--list`

### 2. List available templates

```bat
python scripts\setup_workspace.py --list
```

Output:
```
Available templates:
  pdm360               — IFM PDM360 panel project base
                         project: C:\templates\pdm360_base.project
  my_other_product     — ...
```

### 3. Create a workspace from a template

```bat
python scripts\setup_workspace.py pdm360 MyProject_v2
```

This:
1. Reads `templates.json` to find the `pdm360` entry
2. Creates `C:\codesys-workspaces\MyProject_v2\`
3. Copies `pdm360_base.project` → `MyProject_v2.project` inside that folder
4. Prints `KEY=VALUE` pairs to stdout for the batch script to consume

### 4. Full orchestration batch with template support

```bat
@echo off
setlocal enabledelayedexpansion

set TEMPLATE=%1
set WORKSPACE_NAME=%2

if "%TEMPLATE%"=="" (
    echo Usage: run.bat ^<template^> ^<workspace_name^>
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
echo.

:: Step 1 - Export project to XML
set XML_PATH=%WORKSPACE%\export.xml
start /b /wait "%CODESYS_EXE%" --noUI --profile="%CODESYS_PROFILE%" ^
    --runscript="%~dp0scripts\export.py" ^
    --scriptargs="%PROJECT_PATH%|%XML_PATH%"
if errorlevel 1 goto :error

:: Step 2 - Modify XML (CPython)
python "%~dp0scripts\modify.py" "%XML_PATH%" "%XML_PATH%"
if errorlevel 1 goto :error

:: Step 3 - Import + build + download
start /b /wait "%CODESYS_EXE%" --noUI --profile="%CODESYS_PROFILE%" ^
    --runscript="%~dp0scripts\import_deploy.py" ^
    --scriptargs="%PROJECT_PATH%|%XML_PATH%"
if errorlevel 1 goto :error

echo Done.
exit /b 0

:error
echo FAILED.
exit /b 1
```

**Usage:**
```bat
run.bat pdm360 MyProject_v2
run.bat cr0403 AnotherProject
```

### Adding a new template

1. Create and save a base `.project` in CODESYS with all device/library config done
2. Copy it to your templates folder (e.g. `C:\templates\`)
3. Add an entry to `templates.json`
4. Verify with `python scripts\setup_workspace.py --list`

The skill agent can help generate `templates.json` entries and update the registry
when the user describes a new product target.

---

## References

- `references/xml-schema.md` — PLCopen XML node map for ST, VAR, FBD, task config
- CODESYS scripting snippets: https://forge.codesys.com/tol/scripting/snippets/
- ScriptProject API: https://product-help.schneider-electric.com/Machine%20Expert/V1.1/en/ScriptEngine/topics/scriptproject.htm
