# claude-skill-codesys-modifier

A [Claude Skill](https://support.claude.ai/hc/en-us/articles/skills) that automates CODESYS 3.5 SP17+ project modification from the terminal — no GUI required.

Gives Claude the ability to export a `.project` to PLCopen XML, modify ST code / VAR blocks / FBD / task config, import it back, build, and download to a PLC using `CODESYS.exe --noUI`.

## What it does

```
run.bat <template> <workspace_name>
  └─ setup_workspace.py    copies template .project to new workspace
  └─ export.py             CODESYS.exe --noUI → PLCopen XML
  └─ modify.py             CPython edits XML (ST, VAR, FBD, task config)
  └─ import_deploy.py      CODESYS.exe --noUI → import + build + download
```

## Requirements

- Windows
- CODESYS 3.5 SP17+
- Python 3.x (CPython, for `modify.py` and `setup_workspace.py`)

## Installation

1. Download the latest `.skill` file from [Releases](../../releases)
2. Go to claude.ai → Settings → Features → Skills → Upload skill
3. Select the `.skill` file and toggle the skill ON

Or clone the repo and zip the folder manually:

```bat
git clone https://github.com/your-username/claude-skill-codesys-modifier
cd claude-skill-codesys-modifier
zip -r codesys-modifier.skill codesys-modifier/
```

## Setup

### 1. Register your product templates

Edit `templates.json` to point to your base `.project` files:

```json
{
  "templates": {
    "my-device": {
      "description": "My PLC base project",
      "project": "C:\\templates\\my_device_base.project",
      "codesys_profile": "CODESYS V3.5 SP17 Patch 20"
    }
  },
  "defaults": {
    "workspace_root": "C:\\codesys-workspaces",
    "codesys_exe": "C:\\Program Files\\CODESYS 3.5.17.20\\CODESYS\\Common\\CODESYS.exe"
  }
}
```

> The `codesys_profile` string must match exactly what's shown in CODESYS → Help → About.

### 2. List available templates

```bat
python scripts\setup_workspace.py --list
```

### 3. Ask Claude to modify a project

```
Create a new workspace from the my-device template called TestProject,
change the MainTask cycle time to 20ms and add a BOOL variable called g_Enable to GVL_Main.
```

Claude will generate the appropriate `modify.py` code, create the workspace, run the full pipeline, and report the result.

## File structure

```
codesys-modifier/
├── SKILL.md                      ← skill instructions for Claude
├── templates.json                ← user-maintained product template registry
├── scripts/
│   ├── setup_workspace.py        ← CPython: copy template to new workspace
│   ├── export.py                 ← IronPython: export .project to XML
│   ├── modify.py                 ← CPython: XML modification template
│   └── import_deploy.py          ← IronPython: import + build + download
└── references/
    └── xml-schema.md             ← PLCopen XML node map (ST, VAR, FBD, task config)
```

## Notes

- Paths in `--scriptargs` use `|` as separator to handle spaces in directory names
- `modify.py` is a template — Claude fills in the modification logic per request
- Original template `.project` files are never modified (always copied first)
- `run.bat` uses `%~dp0` for paths so it works regardless of CWD

## References

- [CODESYS Scripting Snippets](https://forge.codesys.com/tol/scripting/snippets/)
- [ScriptEngine API (Schneider Electric mirror)](https://product-help.schneider-electric.com/Machine%20Expert/V1.1/en/ScriptEngine/topics/scriptproject.htm)
- [PLCopen XML TC6 schema](https://plcopen.org/technical-activities/xml-exchange)
