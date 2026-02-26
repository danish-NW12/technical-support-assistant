#!/usr/bin/env python3
import argparse
import fnmatch
import json
import os
import re
from typing import Dict, List, Tuple


# -------- rubric rules (medium difficulty) --------
# Each question:
# - content_rules: list of alternatives; each alternative is a list of required substrings
#   Example: [["time", "ntp"], ["clock", "ntp"]] means either (time+ntp) OR (clock+ntp)
# - cite_rules: list of acceptable filename patterns (glob-like)
RUBRIC = {
    "G1": {
        "content_rules": [["support bundle"]],
        "cite_rules": ["docs/cli_reference.md"],
    },
    "G2": {
        "content_rules": [["time", "ntp"], ["clock", "ntp"]],
        "cite_rules": ["docs/kb_ntp_time.md", "docs/troubleshooting_auth.md"],
    },
    "G3": {
        "content_rules": [["error code catalog"], ["support error code catalog"]],
        "cite_rules": ["docs/error_code_catalog.md"],
    },
    "G4": {
        # 2-of-3 gives partial credit
        "content_rules": [["support bundle"], ["error code"], ["10 minutes"]],
        "cite_rules": ["docs/troubleshooting_*.md"],
        "special": "two_of_three",
    },
    "G5": {
        "content_rules": [["vlan", "both ends"], ["native vlan", "both ends"], ["align", "vlan"]],
        "cite_rules": ["docs/kb_vlan_mismatch.md"],
    },
    "G6": {
        "content_rules": [["vpn tunnel up corp-vpn"]],
        "cite_rules": ["docs/cli_reference.md"],
    },
    "G7": {
        "content_rules": [
            ["e2501", "config database", "locked", "cfg unlock"],
            ["config database", "locked", "cfg unlock"],
        ],
        "cite_rules": ["docs/error_code_catalog.md", "docs/troubleshooting_storage.md", "docs/cli_reference.md"],
    },
    "G8": {
        # 2-of-3 gives partial credit
        "content_rules": [["reachability"], ["psk", "proposal"], ["vpn tunnel up"]],
        "cite_rules": ["docs/kb_vpn_basics.md"],
        "special": "two_of_three",
    },

    # Hidden (instructor)
    "H1": {
        "content_rules": [
            ["e2103", "time", "ntp", "ca"],
            ["time", "ntp", "ca bundle"],
            ["clock", "ntp", "ca bundle"],
        ],
        "cite_rules": ["docs/error_code_catalog.md", "docs/kb_ntp_time.md", "docs/troubleshooting_auth.md"],
    },
    "H2": {
        "content_rules": [["3.2"]],
        "cite_rules": ["docs/release_notes.md"],
    },
    "H3": {
        "content_rules": [["cfg unlock"]],
        "cite_rules": ["docs/cli_reference.md", "docs/error_code_catalog.md", "docs/troubleshooting_storage.md"],
    },
    "H4": {
        "content_rules": [["e2701", "cable"], ["e2701", "sfp"], ["replace", "cable"], ["replace", "sfp"]],
        "cite_rules": ["docs/error_code_catalog.md", "docs/troubleshooting_switching.md"],
    },

    # Real-world test questions
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
    """
    Accepts citations if any citation contains a required file pattern
    (supports substring or glob-like matching).
    """
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
    cfg = RUBRIC[qid]
    a = norm(answer)

    # Special scoring: 2-of-3 (or 3-of-3) checks
    if cfg.get("special") == "two_of_three":
        checks = cfg["content_rules"]
        hit = 0
        for reqs in checks:
            if all(r in a for r in reqs):
                hit += 1
        if hit >= 3:
            return 1.0, "content: full (3/3 checks)"
        if hit == 2:
            return 0.7, "content: partial (2/3 checks)"
        if hit == 1:
            return 0.3, "content: minimal (1/3 checks)"
        return 0.0, "content: miss"

    # Normal scoring: any alternative gives full credit
    for alt in cfg["content_rules"]:
        if all(r in a for r in alt):
            return 1.0, "content: full"
    return 0.0, "content: miss"


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="Grade RAG answers against gold (and optionally hidden) questions.")
    ap.add_argument("--dataset", required=True, help="Path to rag_support_dataset folder")
    ap.add_argument("--answers", required=True, help="Path to student_answers.json (generated by run_self_eval.py)")
    ap.add_argument("--include_hidden", action="store_true", help="Include instructor hidden questions")
    args = ap.parse_args()

    gold_path = os.path.join(args.dataset, "gold_questions_public.json")
    hid_path = os.path.join(args.dataset, "hidden_questions_instructor.json")

    if not os.path.exists(gold_path):
        raise FileNotFoundError(f"Missing gold questions file: {gold_path}")
    if not os.path.exists(args.answers):
        raise FileNotFoundError(f"Missing answers file: {args.answers}")

    gold = load_json(gold_path)
    hidden = load_json(hid_path) if args.include_hidden and os.path.exists(hid_path) else []

    key_ids = {q["id"] for q in gold}
    if args.include_hidden:
        key_ids |= {q["id"] for q in hidden}

    student = load_json(args.answers)
    by_id: Dict[str, Dict] = {x["id"]: x for x in student if "id" in x}

    mode = "gold + hidden" if args.include_hidden else "gold only"
    print(f"Grading mode: {mode}\n")

    results = []
    total = 0.0
    max_total = 0.0

    for qid in sorted(key_ids):
        if qid not in RUBRIC:
            # If a question exists but isn't in RUBRIC, skip it.
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
        })

    print("=== RAG Grading Report ===")
    print(f"Total: {total:.1f} / {max_total:.1f} ({(100*total/max_total if max_total else 0):.1f}%)\n")
    for r in results:
        print(f"{r['id']}: {r['score']:.1f}/2.0  | {r['content_msg']} | citations_ok={r['citations_ok']}")

    report_path = os.path.join(os.path.dirname(args.answers), "grading_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"total": total, "max_total": max_total, "results": results}, f, indent=2)
    print(f"\nWrote: {report_path}")


if __name__ == "__main__":
    main()
