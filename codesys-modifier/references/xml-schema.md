# PLCopen XML Schema Reference (CODESYS 3.5 Export)

Namespace: `http://www.plcopen.org/xml/tc6_0201`
Schema version: tc6_xml_v201

CODESYS uses standard PLCopen XML **plus** proprietary `<addData>` extensions.

---

## Top-Level Structure

```xml
<project xmlns="http://www.plcopen.org/xml/tc6_0201">
  <fileHeader ... />
  <contentHeader>
    <coordinateInfo> ... </coordinateInfo>
  </contentHeader>
  <types>
    <dataTypes> ... </dataTypes>
    <pous>
      <pou name="MyPOU" pouType="program|functionBlock|function"> ... </pou>
    </pous>
  </types>
  <instances>
    <configurations>
      <configuration name="...">
        <resource name="...">
          <task ...> ... </task>
          <pouInstance ...> ... </pouInstance>
        </resource>
      </configuration>
    </configurations>
  </instances>
  <addData>
    <!-- CODESYS-proprietary: device tree, task config, GVLs, etc. -->
  </addData>
</project>
```

---

## POU Node

```xml
<pou name="MyProgram" pouType="program">
  <interface>
    <localVars>         <!-- VAR ... END_VAR -->
    <inputVars>         <!-- VAR_INPUT ... END_VAR -->
    <outputVars>        <!-- VAR_OUTPUT ... END_VAR -->
    <inOutVars>         <!-- VAR_IN_OUT ... END_VAR -->
    <externalVars>      <!-- VAR_EXTERNAL ... END_VAR -->
    <globalVars>        <!-- VAR_GLOBAL (in GVL pou) -->
  </interface>
  <body>
    <!-- One of: ST, IL, FBD, LD, SFC -->
  </body>
  <addData>
    <!-- CODESYS plaintext declaration if declarations_as_plaintext=True -->
    <data name="http://www.3s-software.com/plcopenxml/poudeclaration" handleUnknown="implementation">
      <Declaration><![CDATA[
PROGRAM MyProgram
VAR
  x : INT;
END_VAR
      ]]></Declaration>
    </data>
  </addData>
</pou>
```

### Accessing declarations

**With `declarations_as_plaintext=True` (recommended):**
The full ST text including `PROGRAM ... VAR ... END_VAR` is in `<addData>/<data>/<Declaration>` as CDATA.
This is lossless. Edit the CDATA string directly.

XPath: `.//pou[@name='MyProgram']/addData/data/Declaration`

**Without plaintext flag:**
VAR blocks are structured:
```xml
<localVars>
  <variable name="x">
    <type><INT/></type>
    <initialValue><simpleValue value="0"/></initialValue>
    <documentation><xhtml:p>comment</xhtml:p></documentation>
  </variable>
</localVars>
```

---

## ST Body

```xml
<body>
  <ST>
    <xhtml:p xmlns:xhtml="http://www.w3.org/1999/xhtml">
      x := x + 1;&#xA;y := y + 2;
    </xhtml:p>
  </ST>
</body>
```

XPath (with NS): `.//plc:pou[@name='X']/plc:body/plc:ST/xhtml:p`

The ST text uses `&#xA;` for newlines. Edit `.text` directly in ElementTree.

---

## FBD Body

FBD is a full syntax tree — not plain text. Structure:

```xml
<body>
  <FBD>
    <block localId="1" typeName="ADD" executionOrderId="0">
      <position x="200" y="100"/>
      <inputVariables>
        <variable formalParameter="IN1">
          <connectionPointIn>
            <connection refLocalId="2"/>  <!-- wire from block 2 -->
          </connectionPointIn>
        </variable>
      </inputVariables>
      <outputVariables>
        <variable formalParameter="OUT">
          <connectionPointOut/>
        </variable>
      </outputVariables>
    </block>
    <inVariable localId="2" negated="false">
      <position x="50" y="100"/>
      <expression>MyVar</expression>
    </inVariable>
    <outVariable localId="3" negated="false">
      <position x="400" y="100"/>
      <expression>Result</expression>
    </outVariable>
  </FBD>
</body>
```

**FBD modification approach:**
- To change a variable name: edit `<expression>` text in `<inVariable>` / `<outVariable>`
- To change a block type: edit `typeName` attribute on `<block>`
- To add/remove blocks: manipulate `localId` and `<connection refLocalId>` carefully
- To replace an entire FBD network: export the POU as PLCopen XML from a reference project and substitute the `<FBD>` subtree

---

## LD (Ladder) Body

```xml
<body>
  <LD>
    <leftPowerRail localId="1">
      <position x="0" y="0"/>
      <connectionPointOut formalParameter="0"/>
    </leftPowerRail>
    <contact localId="2" negated="false" edge="none">
      <position x="100" y="0"/>
      <variable>MyBool</variable>
      <connectionPointIn><connection refLocalId="1" formalParameter="0"/></connectionPointIn>
      <connectionPointOut/>
    </contact>
    <coil localId="3" negated="false" edge="none" storage="none">
      <position x="300" y="0"/>
      <variable>OutputBool</variable>
      <connectionPointIn><connection refLocalId="2"/></connectionPointIn>
    </coil>
    <rightPowerRail localId="4">
      <position x="400" y="0"/>
      <connectionPointIn formalParameter="0"><connection refLocalId="3"/></connectionPointIn>
    </rightPowerRail>
  </LD>
</body>
```

**LD modification:** same approach as FBD — edit variable names or substitute subtrees.

---

## Task Configuration

Task config is **not** in the standard PLCopen `<instances>` section.
CODESYS stores it in `<addData>` as a proprietary extension:

```xml
<addData>
  <data name="http://www.3s-software.com/plcopenxml/projectinformation" handleUnknown="implementation">
    ...
  </data>
  <data name="http://www.3s-software.com/plcopenxml/devicedescription" handleUnknown="discard">
    <DeviceDescription>
      <Device ...>
        <TaskConfig>
          <Task name="MainTask" priority="1" type="Cyclic" interval="T#10ms">
            <POUInstance name="PLC_PRG" typeName="PLC_PRG"/>
          </Task>
        </TaskConfig>
      </Device>
    </DeviceDescription>
  </data>
</addData>
```

XPath (no NS needed, addData is unnamespaced in CODESYS exports):
`.//addData/data[@name='http://www.3s-software.com/plcopenxml/devicedescription']//Task`

**Caveat:** Task config round-trip via PLCopen XML is unreliable in some CODESYS
versions — it may be placed as a duplicate branch on re-import. Prefer editing task
config directly in the IronPython script via the scriptengine API if possible:
```python
# IronPython — modify task interval via scripting API (safer than XML edit)
task_cfg = proj.find("Task Configuration", True)[0]
# Task config modification via API is limited; XML edit + careful import is often needed
```

---

## GVL (Global Variable List)

GVLs appear as POUs with `pouType` not set, inside `<pous>`:

```xml
<pou name="GVL_Main">
  <interface>
    <globalVars>
      <variable name="g_Counter"><type><INT/></type></variable>
    </globalVars>
  </interface>
  <addData>
    <data name="http://www.3s-software.com/plcopenxml/poudeclaration" ...>
      <Declaration><![CDATA[
VAR_GLOBAL
  g_Counter : INT;
END_VAR
      ]]></Declaration>
    </data>
  </addData>
</pou>
```

---

## Data Types (DUT)

```xml
<types>
  <dataTypes>
    <dataType name="MyStruct">
      <baseType>
        <struct>
          <variable name="Field1"><type><INT/></type></variable>
          <variable name="Field2"><type><BOOL/></type></variable>
        </struct>
      </baseType>
    </dataType>
  </dataTypes>
</types>
```

---

## Python XML Editing Tips

```python
import xml.etree.ElementTree as ET

PLCopen_NS = "http://www.plcopen.org/xml/tc6_0201"
XHTML_NS   = "http://www.w3.org/1999/xhtml"
NS = {"plc": PLCopen_NS, "xhtml": XHTML_NS}

# Register namespaces to avoid ns0: mangling on write
ET.register_namespace("", PLCopen_NS)
ET.register_namespace("xhtml", XHTML_NS)

tree = ET.parse("export.xml")
root = tree.getroot()

# Find POU by name
def find_pou(root, name):
    return next(
        (p for p in root.findall(".//plc:pou", NS) if p.get("name") == name),
        None
    )

# Edit ST body
def set_st_body(pou, new_code):
    p = pou.find(".//plc:body/plc:ST/xhtml:p", NS)
    if p is not None:
        p.text = new_code

# Edit Declaration (plaintext export)
def set_declaration(pou, new_decl):
    decl = pou.find(".//addData/data/Declaration")
    if decl is not None:
        decl.text = new_decl

# Write back
tree.write("export_modified.xml", xml_declaration=True, encoding="utf-8")
```

**Use lxml if namespace prefixes are critical** — ElementTree can emit `ns0:` prefixes
on write that confuse CODESYS import:
```python
from lxml import etree
tree = etree.parse("export.xml")
tree.write("out.xml", pretty_print=True, xml_declaration=True, encoding="utf-8")
```
