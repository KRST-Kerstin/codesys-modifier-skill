# modify.py — CPython 3.x
# Usage: python scripts\modify.py <xml_input_path> <xml_output_path>
#
# This is a TEMPLATE — implement your actual modifications below.
# See references/xml-schema.md for node paths for ST, VAR, FBD, task config.

import sys
import xml.etree.ElementTree as ET

PLCopen_NS = "http://www.plcopen.org/xml/tc6_0201"
XHTML_NS   = "http://www.w3.org/1999/xhtml"
NS = {"plc": PLCopen_NS, "xhtml": XHTML_NS}

ET.register_namespace("", PLCopen_NS)
ET.register_namespace("xhtml", XHTML_NS)


def find_pou(root, name):
    return next(
        (p for p in root.findall(".//plc:pou", NS) if p.get("name") == name),
        None,
    )


def set_st_body(pou, new_code):
    """Replace ST body text of a POU."""
    p = pou.find(".//plc:body/plc:ST/xhtml:p", NS)
    if p is not None:
        p.text = new_code
        return True
    return False


def set_declaration(pou, new_decl):
    """Replace plaintext VAR block declaration (declarations_as_plaintext export only)."""
    decl = pou.find(".//addData/data/Declaration")
    if decl is not None:
        decl.text = new_decl
        return True
    return False


def main():
    if len(sys.argv) < 3:
        print("Usage: modify.py <input_xml> <output_xml>")
        sys.exit(1)

    input_path  = sys.argv[1]
    output_path = sys.argv[2]

    tree = ET.parse(input_path)
    root = tree.getroot()

    # ----------------------------------------------------------------
    # TODO: implement your modifications here
    # Example: replace ST body of "MyProgram"
    #
    # pou = find_pou(root, "MyProgram")
    # if pou:
    #     set_st_body(pou, "x := x + 1;\n")
    #
    # Example: replace VAR declaration of "GVL_Main"
    #
    # gvl = find_pou(root, "GVL_Main")
    # if gvl:
    #     set_declaration(gvl, "VAR_GLOBAL\n  g_Counter : INT := 0;\nEND_VAR\n")
    # ----------------------------------------------------------------

    tree.write(output_path, xml_declaration=True, encoding="utf-8")
    print("Modified XML written to: %s" % output_path)


if __name__ == "__main__":
    main()
