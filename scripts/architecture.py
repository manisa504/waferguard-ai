"""Generate editable draw.io architecture from the Gate 0 design."""

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, indent, tostring


def cell(root, identity, label, x, y, width=210, height=78, icon=None, color="#232F3E"):
    style = "rounded=1;whiteSpace=wrap;html=1;fontSize=12;fillColor=none;"
    if icon:
        style = (
            f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{icon};"
            f"fillColor={color};strokeColor=#ffffff;sketch=0;fontSize=12;"
            "verticalLabelPosition=bottom;verticalAlign=top;align=center;"
        )
        width = 78
    c = SubElement(root, "mxCell", id=identity, value=label, style=style, vertex="1", parent="1")
    SubElement(
        c,
        "mxGeometry",
        x=str(x),
        y=str(y),
        width=str(width),
        height=str(height),
        attrib={"as": "geometry"},
    )


def edge(root, source, target, dashed=False):
    c = SubElement(
        root,
        "mxCell",
        id=f"{source}-{target}",
        source=source,
        target=target,
        edge="1",
        parent="1",
        style=(
            "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
            "html=1;strokeWidth=2;exitX=1;exitY=0.5;exitDx=0;exitDy=0;"
            "entryX=0;entryY=0.5;entryDx=0;entryDy=0;" + ("dashed=1;" if dashed else "")
        ),
    )
    geometry = SubElement(c, "mxGeometry", relative="1", attrib={"as": "geometry"})
    nodes = {node.get("id"): node for node in root if node.get("vertex") == "1"}
    source_y = float(nodes[source].find("mxGeometry").get("y"))
    target_y = float(nodes[target].find("mxGeometry").get("y"))
    if source_y != target_y:
        style = c.get("style").replace(
            "exitX=1;exitY=0.5", "exitX=0.5;exitY=1" if source_y < target_y else "exitX=0.5;exitY=0"
        )
        style = style.replace(
            "entryX=0;entryY=0.5",
            "entryX=0.5;entryY=0" if source_y < target_y else "entryX=0.5;entryY=1",
        )
        c.set("style", style)
    if (source, target) == ("inference", "models"):
        c.set(
            "style",
            c.get("style")
            .replace("exitX=1;exitY=0.5", "exitX=0.5;exitY=0")
            .replace("entryX=0;entryY=0.5", "entryX=0.5;entryY=0"),
        )
        points = SubElement(geometry, "Array", attrib={"as": "points"})
        SubElement(points, "mxPoint", x="1039", y="150")
        SubElement(points, "mxPoint", x="1679", y="150")
    if source == "source":
        c.set(
            "style",
            c.get("style")
            .replace("exitX=1;exitY=0.5", "exitX=0.5;exitY=0")
            .replace("entryX=0;entryY=0.5", "entryX=0.5;entryY=0"),
        )
        points = SubElement(geometry, "Array", attrib={"as": "points"})
        SubElement(points, "mxPoint", x="1930", y="150")
        SubElement(points, "mxPoint", x="555", y="150")


def page(file, name, title):
    diagram = SubElement(file, "diagram", id=name.lower(), name=name)
    model = SubElement(
        diagram,
        "mxGraphModel",
        dx="2800",
        dy="1600",
        grid="1",
        page="1",
        pageWidth="2400",
        pageHeight="1400",
    )
    root = SubElement(model, "root")
    SubElement(root, "mxCell", id="0")
    SubElement(root, "mxCell", id="1", parent="0")
    cell(root, "background", "", 0, 0, 2400, 1400)
    root[-1].set("style", "fillColor=#F5F5F5;strokeColor=none;")
    cell(
        root,
        "title",
        f"<b>{title}</b><br>WaferGuard contributors | 2026-11-10 | v0.1 | us-east-2",
        40,
        30,
        1000,
        60,
    )
    root[-1].set(
        "style",
        "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=14;spacing=8;",
    )
    return root


file = Element("mxfile", host="app.diagrams.net")
r = page(file, "Foundation", "WaferGuard AI — Gate 0–1: authored locally, not deployed")
cell(r, "owner", "Owner / developer", 100, 230)
cell(r, "tools", "Pinned acquisition + integrity / quality audits", 450, 230)
cell(r, "raw", "S3 raw originals (retained)", 900, 230, icon="s3", color="#7AA116")
cell(r, "artifacts", "S3 artifacts (retained)", 1250, 230, icon="s3", color="#7AA116")
cell(r, "source", "WM-811K / Kaggle source — real data", 1800, 230, 260)
cell(r, "logs", "S3 access logs / 90-day retention", 900, 650, icon="s3", color="#7AA116")
cell(r, "budget", "AWS Budgets: account-wide actual 80% / forecast 100% alerts", 1250, 650, 280)
cell(
    r,
    "note",
    "Private storage, TLS, encryption, versioning. No compute or frontend provisioned. "
    "Data remains local until a reviewed deployment. Budget warnings do not cap spending.",
    100,
    1050,
    1100,
    100,
)
edge(r, "owner", "tools")
edge(r, "tools", "raw", True)
edge(r, "raw", "artifacts", True)
edge(r, "source", "tools", True)
edge(r, "raw", "logs", True)
edge(r, "artifacts", "logs", True)
r = page(file, "Target", "WaferGuard AI — target architecture: future gates, not deployed")
for identity, label, x, icon, color in [
    ("delivery", "React / S3 + CloudFront", 360, "cloudfront", "#8C4FFF"),
    ("api", "Authenticated REST API", 680, "api_gateway", "#E7157B"),
    ("inference", "FastAPI / Lambda CPU inference", 1000, "lambda", "#ED7100"),
    ("cases", "DynamoDB cases + versioned audit", 1320, "dynamodb", "#C925D1"),
    ("models", "S3 model + calibration artifacts", 1640, "s3", "#7AA116"),
]:
    cell(r, identity, label, x, 240, icon=icon, color=color)
cell(r, "user", "Guest / authorized reviewer", 40, 240)
for a, b in [
    ("user", "delivery"),
    ("delivery", "api"),
    ("api", "inference"),
    ("inference", "cases"),
    ("inference", "models"),
]:
    edge(r, a, b)
for identity, label, x, icon, color in [
    ("auth", "Cognito reviewer identity", 360, "cognito", "#DD344C"),
    ("workflow", "Step Functions Standard callback", 1000, "step_functions", "#E7157B"),
    ("events", "EventBridge + SQS / DLQ", 1320, "eventbridge", "#E7157B"),
    ("training", "Offline training / model registry", 1640, "sagemaker", "#01A88D"),
]:
    cell(r, identity, label, x, 650, icon=icon, color=color)
edge(r, "auth", "api", True)
edge(r, "inference", "workflow", True)
edge(r, "workflow", "cases", True)
edge(r, "workflow", "events", True)
edge(r, "training", "models", True)
cell(
    r,
    "monitor",
    "CloudWatch metrics / operational alarms",
    1000,
    1080,
    icon="cloudwatch_2",
    color="#E7157B",
)
cell(
    r,
    "limits",
    "Task tokens stay server-side. Revalidate authorization, case/model versions "
    "and approval expiry before resume. Review is simulated quality disposition. "
    "No real factory release authorization.",
    1360,
    1080,
    650,
    100,
)
indent(file)
Path("DOC/architecture.drawio").write_bytes(tostring(file, encoding="utf-8", xml_declaration=True))
