#!/usr/bin/env python3
"""
Grade real-world test questions.
"""
import argparse
import fnmatch
import json
import os
import re
from typing import Dict, List, Tuple


# Rubric for real-world questions
RUBRIC = {
    "RW1": {
        "content_rules": [
            ["e2002", "dhcp", "vlan", "firmware"],
            ["e2002", "interface", "vlan", "firmware"],
            ["dhcp", "lease", "timeout", "vlan"],
        ],
        "cite_rules": ["docs/troubleshooting_dhcp.md", "docs/error_code_catalog.md"],
    },
    "RW2": {
        "content_rules": [
            ["interface", "vlan", "dhcp", "firmware"],
            ["show interfaces", "vlan", "dhcp", "firmware"],
            ["interface status", "vlan", "dhcp"],
        ],
        "cite_rules": ["docs/troubleshooting_dhcp.md"],
    },
    "RW3": {
        "content_rules": [
            ["e2002", "dhcp", "lease", "timeout"],
            ["dhcp", "lease", "acquisition", "timeout"],
        ],
        "cite_rules": ["docs/error_code_catalog.md", "docs/troubleshooting_dhcp.md"],
    },
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def citation_ok(citations: List[str], patterns: List[str]) -> bool:
    """Check if citations match required patterns."""
    if not citations:
        return False
    c = [norm(x) for x in citations]
    for pat in patterns:
        pat_n = norm(pat)
        for item in c:
            if pat_n in item:
                return True
            if fnmatch.fnmatch(item, f"*{pat_n}*"):
                return True
    return False


def content_score(qid: str, answer: str) -> Tuple[float, str]:
    """Score content based on rubric rules."""
    if qid not in RUBRIC:
        return 0.0, "content: no rubric"
    
    cfg = RUBRIC[qid]
    a = norm(answer)

    # Check each alternative rule set
    for alt in cfg["content_rules"]:
        if all(r in a for r in alt):
            return 1.0, "content: full"
    
    # Partial credit: check if most keywords are present
    best_match = 0
    for alt in cfg["content_rules"]:
        matches = sum(1 for r in alt if r in a)
        if matches > best_match:
            best_match = matches
    
    if best_match >= len(cfg["content_rules"][0]) - 1:
        return 0.7, f"content: partial ({best_match}/{len(cfg['content_rules'][0])} keywords)"
    elif best_match >= len(cfg["content_rules"][0]) // 2:
        return 0.3, f"content: minimal ({best_match}/{len(cfg['content_rules'][0])} keywords)"
    
    return 0.0, "content: miss"


def main():
    ap = argparse.ArgumentParser(
        description="Grade real-world RAG answers"
    )
    ap.add_argument(
        "--answers",
        default="real_world_answers.json",
        help="Path to answers JSON file"
    )
    args = ap.parse_args()

    if not os.path.exists(args.answers):
        raise FileNotFoundError(f"Missing answers file: {args.answers}")

    with open(args.answers, "r", encoding="utf-8") as f:
        student = json.load(f)

    by_id: Dict[str, Dict] = {x["id"]: x for x in student if "id" in x}

    print("=== Real-World RAG Grading Report ===\n")

    results = []
    total = 0.0
    max_total = 0.0

    for qid in sorted(by_id.keys()):
        if qid not in RUBRIC:
            print(f"Warning: No rubric for {qid}, skipping...")
            continue

        max_total += 2.0  # 1 content + 1 citations

        entry = by_id.get(qid, {})
        ans = entry.get("answer", "")
        cites = entry.get("citations", [])

        cscore, cmsg = content_score(qid, ans)
        cite_good = citation_ok(cites, RUBRIC[qid]["cite_rules"])
        citescore = 1.0 if cite_good else 0.0

        score = cscore + citescore
        total += score

        results.append({
            "id": qid,
            "score": score,
            "content_score": cscore,
            "citation_score": citescore,
            "content_msg": cmsg,
            "citations_ok": cite_good,
            "citations": cites,
        })

    print(f"Total: {total:.1f} / {max_total:.1f} ({(100*total/max_total if max_total else 0):.1f}%)\n")
    
    for r in results:
        print(f"{r['id']}: {r['score']:.1f}/2.0")
        print(f"  Content: {r['content_score']:.1f}/1.0 - {r['content_msg']}")
        print(f"  Citations: {r['citation_score']:.1f}/1.0 - {r['citations_ok']}")
        print(f"  Sources: {', '.join(r['citations'][:3])}{'...' if len(r['citations']) > 3 else ''}")
        print()

    report_path = os.path.join(
        os.path.dirname(args.answers),
        "real_world_grading_report.json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "total": total,
            "max_total": max_total,
            "percentage": (100*total/max_total if max_total else 0),
            "results": results
        }, f, indent=2)
    print(f"✅ Wrote detailed report: {report_path}")


if __name__ == "__main__":
    main()
