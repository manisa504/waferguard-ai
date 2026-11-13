"""Render the portable campaign brief from the same content used by the campaign page."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "DOC/campaign.json").read_text())
repo = "https://github.com/manisa504/waferguard-ai/blob/main/"
lines = [
    "# WaferGuard — Campaign brief",
    "",
    "Evidence snapshot: November 13, 2026. Audience: " + data["audience"] + ".",
    "",
    "## Editorial guidance",
    "",
    "Prepare this as a 12-day LinkedIn campaign for review. Do not publish or schedule "
    "until the account owner confirms the LinkedIn account, start date, posting timezone, "
    "cadence, and final text. Day numbers are relative sequence positions, not dates. "
    "This document does not grant account access or publishing permission.",
    "",
    "Lead with business context, then technical evidence, then the engineering decision "
    "and architectural decision. Use plain language, short paragraphs, and one discussion "
    "question. Keep evidence links attached. Avoid invented ROI, savings, customer use, "
    "hiring claims, latency, cost, or production readiness. Do not add a personal name.",
    "",
    "Model qualification FAILED. Promotion is blocked and operational automatic "
    "acceptance is disabled. API/review modules are drafts; Gate 5 is not passed. "
    "The AWS application is not deployed. The observed test must not be described "
    "as untouched. Historical validation metrics are not current test results. "
    "The 62.1% offline coverage is not achieved labor savings.",
    "",
    "Use only aggregate evidence, committed plots, and labeled architecture diagrams. "
    "Never publish raw maps, trained weights, credentials, or synthetic wafer imagery "
    "presented as source data. The actual 90-second video and Vercel URL were not "
    "supplied. Keep these integrations pending; do not fabricate URLs or imply a live app.",
    "",
    "## Content inventory",
    "",
    "18 potential assets: 12 written posts, four six-slide carousel outlines, one "
    "90-second video script, and one case-study brief. The last six are adaptations "
    "requiring production. Do not post all adaptations during the same twelve days "
    "without an approved cadence. No reach, engagement, or conversion forecast is claimed.",
    "",
    "## Measurement plan",
    "",
    "Record actual impressions, substantive comments, repository/site referrals, and "
    "qualified hiring conversations when available from authorized account analytics. "
    "There is no baseline or target forecast in this brief. Review responses after "
    "days 4, 8, and 12 to decide which subjects need clearer explanation. Do not add "
    "tracking identifiers or analytics credentials to public source.",
    "",
]
for post in data["days"]:
    lines.extend([f"## Day {post['day']} — {post['title']}", "", "### LinkedIn copy", ""])
    lines.extend([
        post["title"], "", post["business"], "", post["technical"], "",
        "Engineering decision: " + post["decision"], "",
        "Architectural decision: " + post["architecture"], "", post["question"], "",
        "Evidence:", "",
    ])
    lines.extend(f"- [{path}]({repo}{path})" for path in post["evidence"])
    lines.extend(["", "### Production note (not post copy)", "", post["visual"], ""])
lines.extend(["## Four carousel adaptations", ""])
for carousel in data["carousels"]:
    lines.extend(["### " + carousel["title"], ""])
    lines.extend(f"{index}. {slide}" for index, slide in enumerate(carousel["slides"], 1))
    days = ", ".join(map(str, carousel["days"]))
    lines.extend(["", "Evidence comes from days " + days + ".", ""])
lines.extend(["## 90-second walkthrough script", "", data["video"]["title"], ""])
for segment in data["video"]["segments"]:
    lines.extend([f"### {segment['time']} — {segment['visual']}", "", segment["voiceover"], ""])
lines.extend([
    "Target duration only; record and verify final timing. Use real committed plots "
    "and captions. Label diagrams as authored foundation or future target. "
    "Generated decorative media must not masquerade as measured results.", "",
    "## One-page case-study brief", "", "### " + data["caseStudy"]["title"], "",
])
for key, label in [("business", "Business context"), ("work", "Technical work"),
                   ("result", "Measured outcome and decision"),
                   ("architecture", "Architectural decision"), ("next", "Next gate")]:
    lines.extend(["### " + label, "", data["caseStudy"][key], ""])
lines.extend([
    "## Handoff fields still pending", "",
    "- LinkedIn account, campaign start date, timezone, cadence, and publication approval.",
    "- Actual video URL/file and captions; current deliverable is a script.",
    "- Actual Vercel application URL and a verified description of what it demonstrates.",
    "- Visual production for the four carousel outlines.", "",
    "## Source of truth", "",
    "- [Repository](https://github.com/manisa504/waferguard-ai)",
    "- [Gate 4 qualification](" + repo + "reports/gates/gate_4.md)",
    "- [Current model card](" + repo + "DOC/model_card.md)",
    "- [AWS plan](" + repo + "DOC/PROJECT_STATUS_AND_AWS_PLAN.md)", "",
])
(ROOT / "DOC/CAMPAIGN_BRIEF.md").write_text("\n".join(lines))
print("Rendered 12 posts, four carousel outlines, video script, and case-study brief.")
