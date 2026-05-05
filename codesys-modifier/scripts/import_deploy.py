# import_deploy.py — IronPython, run via: CODESYS.exe --noUI --runscript="scripts\import_deploy.py"
# --scriptargs="<project_path>|<modified_xml_path>[|<gateway_ip>]"
# Paths separated by | to handle spaces in directory names.

args = [a.strip() for a in system.get_scriptargs().split("|")]
PROJECT_PATH = args[0]
MODIFIED_XML = args[1]
GATEWAY_IP   = args[2] if len(args) > 2 else None

proj = projects.open(PROJECT_PATH)
app  = proj.active_application

# Import modified XML — replaces matching objects by name
proj.import_xml(MODIFIED_XML)

proj.save()

# Build (generate code)
app.build()

# Log build messages regardless of outcome
for msg in app.messages:
    system.write_message(Severity.Information, "Build: " + str(msg))

if app.has_compile_error:
    system.write_message(Severity.Error, "Build failed — aborting")
    proj.close()
    raise Exception("Build error")

system.write_message(Severity.Information, "Build OK")

# Download to PLC
if GATEWAY_IP:
    system.write_message(Severity.Information, "Connecting to gateway: " + GATEWAY_IP)
    onlineapp = online.create_online_application(app)
    # OnlineChangeOption.Try: online change if delta is compatible, else full download
    onlineapp.login(OnlineChangeOption.Try, True)
    onlineapp.download(OnlineChangeOption.Try)
    system.delay(2000)
    onlineapp.start()
    onlineapp.logout()
    system.write_message(Severity.Information, "Download and start done.")
else:
    system.write_message(Severity.Information, "No gateway specified — skipping download.")

proj.close()
system.write_message(Severity.Information, "import_deploy.py done.")
