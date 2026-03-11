# scripts/generate_check_sheet.py

import os
import urllib.request
import urllib.parse
import json
from collections import defaultdict
from datetime import datetime

REPO = os.environ["GITHUB_REPOSITORY"] 
TOKEN = os.environ["GITHUB_TOKEN"]

LABELS = {
    "Test failures": "test-failure",
    "Incorrect output": "incorrect-output",
    "Incorrect reading": "incorrect-reading",
    "Build errors": "build-error",
}

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

def github_get(url: str):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def fetch_issues(label: str):
    encoded_label = urllib.parse.quote(label)
    url = f"https://api.github.com/repos/{REPO}/issues?state=all&labels={encoded_label}&per_page=100"
    return github_get(url)

def weekday_from_github_date(date_str: str):
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%a") 

def tally_marks(n: int) -> str:
    return "I" * n if n > 0 else ""

def main():
    results = {}

    for row_name, label in LABELS.items():
        counts = defaultdict(int)
        issues = fetch_issues(label)

        for issue in issues:
            if "pull_request" in issue:
                continue

            created_at = issue["created_at"]
            day = weekday_from_github_date(created_at)

            if day in DAYS:
                counts[day] += 1

        total = sum(counts[d] for d in DAYS)
        results[row_name] = {
            "days": {day: counts[day] for day in DAYS},
            "total": total,
        }

    lines = []
    lines.append("# Repository Check Sheet")
    lines.append("")
    lines.append("This file is generated automatically from GitHub Issues labels.")
    lines.append("")
    lines.append("| Issue / Event | Mon | Tue | Wed | Thu | Fri | Total |")
    lines.append("|---|---|---|---|---|---|---|")

    for row_name, data in results.items():
        row = [row_name]
        for day in DAYS:
            row.append(tally_marks(data["days"][day]))
        row.append(str(data["total"]))
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append("## Labels used")
    lines.append("")
    for row_name, label in LABELS.items():
        lines.append(f"- `{label}` → {row_name}")

    lines.append("")
    lines.append("Legend: `I` = 1 occurrence")

    output_path = os.path.join(os.path.dirname(__file__), "CHECK_SHEET.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()