"""Generate the high-level target and authored-foundation draw.io views."""

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, indent, tostring

OUT = Path(__file__).resolve().parents[1] / "DOC"
INK = "#183A34"
MUTED = "#52665E"
LINE = "#D5DDD4"
PAPER = "#F7F6F0"


def box(root, identity, x, y, w, h, fill="#FFFEFA", stroke=LINE, extra=""):
    style = (
        "rounded=1;arcSize=8;html=1;whiteSpace=wrap;"
        f"fillColor={fill};strokeColor={stroke};strokeWidth=2;{extra}"
    )
    node = SubElement(root, "mxCell", id=identity, style=style, vertex="1", parent="1")
    SubElement(node, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h),
               attrib={"as": "geometry"})
    return node


def text(root, identity, label, x, y, w, h, size=24, color=INK, bold=False):
    node = box(root, identity, x, y, w, h, "none", "none")
    node.set("value", label)
    node.set("style", "text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;"
             f"spacing=0;fontFamily=Helvetica;fontSize={size};fontColor={color};"
             f"fontStyle={int(bold)};")
    return node


def icon(root, identity, name, x, y, color, size=78):
    node = box(root, identity, x, y, size, size)
    node.set("style", f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{name};"
             f"fillColor={color};strokeColor=#ffffff;sketch=0;fontSize=12;")
    return node


def edge(root, identity, source, target, dashed=False, vertical=False, points=()):
    anchors = ("exitX=0.5;exitY=1;entryX=0.5;entryY=0;" if vertical else
               "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    node = SubElement(
        root, "mxCell", id=identity, source=source, target=target, edge="1", parent="1",
        style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
        "html=1;strokeWidth=3;strokeColor=#183A34;endArrow=block;endFill=1;"
        "exitDx=0;exitDy=0;entryDx=0;entryDy=0;labelBackgroundColor=#F7F6F0;"
        + anchors + ("dashed=1;dashPattern=6 5;" if dashed else ""),
    )
    geometry = SubElement(node, "mxGeometry", relative="1", attrib={"as": "geometry"})
    if points:
        array = SubElement(geometry, "Array", attrib={"as": "points"})
        for x, y in points:
            SubElement(array, "mxPoint", x=str(x), y=str(y))
    return node


def page(file, identity, name, heading, subtitle, status):
    diagram = SubElement(file, "diagram", id=identity, name=name)
    model = SubElement(diagram, "mxGraphModel", dx="2800", dy="1600", grid="1",
                       page="1", pageWidth="2400", pageHeight="1400")
    root = SubElement(model, "root")
    SubElement(root, "mxCell", id="0")
    SubElement(root, "mxCell", id="1", parent="0")
    box(root, "background", 0, 0, 2400, 1400, PAPER, "none", "rounded=0;")
    text(root, "title", f"<b>{heading}</b><br>"
         "<font style='font-size:18px'>WaferGuard contributors | 2026-11-13 | v2</font>",
         60, 38, 2200, 95, size=46)
    text(root, "subtitle", subtitle, 60, 140, 2240, 42, size=25, color=MUTED)
    box(root, "status-background", 60, 205, 2280, 54, "#F8EDDC", "none")
    text(root, "status", status, 80, 211, 2230, 40, size=23, color="#82521F", bold=True)
    return root


def stage(root, identity, number, title, service, description, x, width, name, color):
    y = 580
    box(root, identity, x, y, width, 270)
    icon(root, identity + "-icon", name, x + 24, y + 24, color)
    text(root, identity + "-number", number, x + 122, y + 20, width - 140, 28,
         size=19, color=MUTED, bold=True)
    text(root, identity + "-service", service, x + 122, y + 54, width - 140, 58,
         size=20, color=MUTED)
    text(root, identity + "-title", title, x + 24, y + 130, width - 48, 44,
         size=30, bold=True)
    text(root, identity + "-description", description, x + 24, y + 184,
         width - 48, 64, size=21, color=MUTED)


file = Element("mxfile", host="app.diagrams.net")
r = page(file, "overview", "High-level overview", "WaferGuard / high-level architecture",
         "Business goal: support inspection review "
         "while keeping quality decisions under human authority.",
         "PLANNED AWS APPLICATION · Not deployed · "
         "Model promotion blocked · Automatic acceptance off")
box(r, "aws-boundary", 410, 280, 1950, 1050, "none", "#9CAC9E", "dashed=1;")
text(r, "aws-title", "AWS TARGET  /  US East (Ohio) · us-east-2", 440, 291, 1470, 36,
     size=22, color=MUTED, bold=True)
box(r, "people", 60, 580, 245, 270, "#E9EEE5", "none")
text(r, "people-kicker", "THE USER", 82, 610, 200, 32, size=19, color=MUTED, bold=True)
text(r, "people-title", "Engineer<br>or reviewer", 82, 661, 200, 95, size=31, bold=True)
text(r, "people-detail", "Inspect evidence.<br>Record a decision.", 82, 773, 200, 54,
     size=20, color=MUTED)
stage(r, "web", "01 / ACCESS", "Web workspace", "CloudFront + S3",
      "Upload a map.<br>Explore the result.", 460, 350, "cloudfront", "#8C4FFF")
stage(r, "prediction", "02 / ANALYZE", "Prediction API", "API Gateway<br>+ Lambda",
      "Class + confidence.<br>Policy checks.", 1000, 350, "lambda", "#ED7100")
stage(r, "review", "03 / DECIDE", "Human review", "Step Functions",
      "Authorized decision.<br>Controlled resume.", 1540, 350, "step_functions", "#E7157B")
stage(r, "records", "04 / RECORD", "Case history", "DynamoDB",
      "State, versions<br>and audit.", 2080, 250, "dynamodb", "#C925D1")
for source, target in [("people", "web"), ("web", "prediction"),
                       ("prediction", "review"), ("review", "records")]:
    edge(r, source + "-to-" + target, source, target)
box(r, "identity", 1000, 342, 350, 134)
icon(r, "identity-icon", "cognito", 1020, 366, "#DD344C", 65)
text(r, "identity-title", "Reviewer identity", 1103, 356, 225, 38, size=23, bold=True)
text(r, "identity-detail", "Amazon Cognito", 1103, 404, 225, 32, size=20, color=MUTED)
edge(r, "authorize-api", "identity", "prediction", vertical=True)
text(r, "serving-note", "CloudFront is global. Regional application services use Ohio.",
     460, 880, 1350, 40, size=21, color=MUTED)
box(r, "operations", 460, 1130, 550, 150)
icon(r, "operations-icon", "cloudwatch_2", 484, 1170, "#E7157B", 65)
text(r, "operations-title", "Operational visibility", 570, 1150, 415, 42, size=26, bold=True)
text(r, "operations-detail", "CloudWatch logs + alarms<br>Budget warnings are separate controls.",
     570, 1200, 415, 56, size=20, color=MUTED)
box(r, "artifacts", 1800, 1130, 530, 150)
icon(r, "artifacts-icon", "s3", 1824, 1170, "#7AA116", 65)
text(r, "artifacts-title", "Versioned model evidence", 1910, 1150, 395, 42,
     size=25, bold=True)
text(r, "artifacts-detail", "S3 · model + calibration artifacts<br>"
     "Serving requires release qualification.",
     1910, 1200, 395, 56, size=20, color=MUTED)
line = edge(r, "qualified-artifacts", "artifacts", "prediction", dashed=True,
            points=((2065, 990), (1175, 990)))
line.set("style", line.get("style").replace(
    "exitX=1;exitY=0.5;entryX=0;entryY=0.5;",
    "exitX=0.5;exitY=0;entryX=0.5;entryY=1;"))
text(r, "artifact-note", "Qualified artifacts only", 1370, 945, 425, 34,
     size=21, color=MUTED)
text(r, "today", "TODAY  /  Local audited data + measured experiments "
     "+ failed release qualification. "
     "Public portfolio: GitHub Pages.", 60, 1351, 2270, 35, size=20, color=MUTED)

r = page(file, "foundation", "Authored foundation", "WaferGuard / current foundation scope",
         "Local research is implemented. Cloud storage and budget controls are defined in CDK.",
         "AUTHORED, NOT DEPLOYED · No inference endpoint, reviewer service, or AWS-hosted web app")
box(r, "local", 100, 580, 480, 270, "#E9EEE5", "none")
text(r, "local-title", "Local evidence pipeline", 130, 620, 420, 45, size=32, bold=True)
text(r, "local-detail", "Audit → grouped splits → experiments<br>"
     "Calibration → frozen evaluation<br>Release decision: blocked", 130, 690,
     420, 120, size=23, color=MUTED)
box(r, "foundation-boundary", 780, 320, 1540, 1010, "none", "#9CAC9E", "dashed=1;")
text(r, "foundation-label", "AWS FOUNDATION  /  us-east-2", 820, 345, 1420, 45,
     size=25, color=MUTED, bold=True)
stage(r, "storage", "PRIVATE + VERSIONED", "Research storage", "Amazon S3",
      "Raw originals + artifacts.<br>Retained on stack deletion.", 860, 500, "s3", "#7AA116")
stage(r, "access-logs", "SEPARATE BUCKET", "Storage access logs", "Amazon S3",
      "Access-log storage.<br>90-day lifecycle.", 1740, 500, "s3", "#7AA116")
edge(r, "planned-upload", "local", "storage", dashed=True)
edge(r, "planned-logging", "storage", "access-logs", dashed=True)
box(r, "budgets", 860, 1130, 1380, 150)
text(r, "budgets-title", "Cost guardrail / AWS Budgets warnings", 895, 1150, 1280, 40,
     size=29, bold=True)
text(r, "budgets-detail", "80% actual + 100% forecast alerts · recipient needed before deployment\n"
     "Warnings do not cap spending. Retained bucket contents need explicit cleanup.",
     895, 1200, 1280, 57, size=23, color=MUTED)
text(r, "foundation-foot", "Dashed links: planned transfers or logging. "
     "All data and model artifacts remain local; none are published with the website.",
     100, 1351, 2220, 35, size=20, color=MUTED)
indent(file)
(OUT / "architecture.drawio").write_bytes(tostring(file, encoding="utf-8", xml_declaration=True))
print("Generated high-level overview and authored-foundation views.")
