# export.py — IronPython, run via: CODESYS.exe --noUI --runscript="scripts\export.py"
# --scriptargs="<project_path> <xml_output_path>"

args = system.get_scriptargs().split("|")
PROJECT_PATH = args[0].strip()
EXPORT_PATH  = args[1].strip()


class Reporter(ExportReporter):
    def error(self, obj, msg):
        system.write_message(Severity.Error, "Export error %s: %s" % (obj, msg))
    def warning(self, obj, msg):
        system.write_message(Severity.Warning, "Export warning %s: %s" % (obj, msg))
    def nonexportable(self, obj):
        system.write_message(Severity.Information, "Non-exportable: %s" % obj)
    @property
    def aborting(self):
        return False


proj = projects.open(PROJECT_PATH)
reporter = Reporter()

# declarations_as_plaintext=True preserves ST/VAR text losslessly as CDATA
proj.export_xml(
    reporter,
    proj.get_children(recursive=True),
    EXPORT_PATH,
    recursive=True,
    declarations_as_plaintext=True,
)
proj.close()
system.write_message(Severity.Information, "Export done: " + EXPORT_PATH)
