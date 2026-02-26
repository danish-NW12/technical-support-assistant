import argparse
import json
import os
import subprocess

from src.rag_pipeline import rag_answer


def main():
    ap = argparse.ArgumentParser(description="Run self-evaluation on gold (and optionally hidden) questions.")
    ap.add_argument("--dataset", default="rag_support_dataset", help="Path to dataset folder")
    ap.add_argument("--persist_dir", default="chroma_store", help="Chroma persist directory")
    ap.add_argument("--collection", default="orbit_support", help="Chroma collection name")
    ap.add_argument("--out", default="student_answers.json", help="Where to write generated answers JSON")
    ap.add_argument(
        "--include_hidden",
        action="store_true",
        help="If set, also evaluate hidden_questions_instructor.json (if present).",
    )
    args = ap.parse_args()

    gold_path = os.path.join(args.dataset, "gold_questions_public.json")
    if not os.path.exists(gold_path):
        raise FileNotFoundError(f"Missing gold questions file: {gold_path}")

    with open(gold_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    mode = "gold only"

    if args.include_hidden:
        hid_path = os.path.join(args.dataset, "hidden_questions_instructor.json")
        if os.path.exists(hid_path):
            with open(hid_path, "r", encoding="utf-8") as f:
                questions += json.load(f)
            mode = "gold + hidden"
        else:
            print("Hidden questions file not found. Continuing with gold only.")

    print(f"Evaluating {len(questions)} questions ({mode}).")

    outputs = []
    for q in questions:
        qid = q.get("id")
        qtext = q.get("question", "")

        if not qid or not qtext:
            # Skip malformed entries
            continue

        print(f"\n[{qid}] {qtext}")

        try:
            out = rag_answer(qtext, persist_dir=args.persist_dir, collection=args.collection)
            answer = out.get("answer", "")
            citations = out.get("citations", [])
        except Exception as e:
            answer = f"[ERROR] {type(e).__name__}: {e}"
            citations = []

        outputs.append({"id": qid, "answer": answer, "citations": citations})

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2)

    print(f"\n✅ Wrote: {args.out}")

    cmd = ["python", "grade_rag.py", "--dataset", args.dataset, "--answers", args.out]
    if args.include_hidden:
        cmd.append("--include_hidden")

    print("\nRunning grader:\n", " ".join(cmd))
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
