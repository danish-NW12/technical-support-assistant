#!/usr/bin/env python3
"""
Test script for real-world ticket and document evaluation.
"""
import argparse
import json
import os
import subprocess

from src.rag_pipeline import rag_answer


def main():
    ap = argparse.ArgumentParser(
        description="Test RAG system on real-world questions"
    )
    ap.add_argument(
        "--dataset",
        default="rag_support_dataset",
        help="Path to dataset folder"
    )
    ap.add_argument(
        "--persist_dir",
        default="chroma_store",
        help="Chroma persist directory"
    )
    ap.add_argument(
        "--collection",
        default="orbit_support",
        help="Chroma collection name"
    )
    ap.add_argument(
        "--questions",
        default="rag_support_dataset/real_world_test_questions.json",
        help="Path to real-world test questions JSON"
    )
    ap.add_argument(
        "--out",
        default="real_world_answers.json",
        help="Where to write generated answers JSON"
    )
    args = ap.parse_args()

    if not os.path.exists(args.questions):
        raise FileNotFoundError(f"Missing questions file: {args.questions}")

    with open(args.questions, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Evaluating {len(questions)} real-world questions.\n")

    outputs = []
    for q in questions:
        qid = q.get("id")
        qtext = q.get("question", "")

        if not qid or not qtext:
            continue

        print(f"[{qid}] {qtext}")
        print("-" * 80)

        try:
            out = rag_answer(
                qtext,
                persist_dir=args.persist_dir,
                collection=args.collection
            )
            answer = out.get("answer", "")
            citations = out.get("citations", [])
        except Exception as e:
            answer = f"[ERROR] {type(e).__name__}: {e}"
            citations = []

        print(f"Answer: {answer[:200]}..." if len(answer) > 200 else f"Answer: {answer}")
        print(f"Citations: {citations}")
        print("\n")

        outputs.append({"id": qid, "answer": answer, "citations": citations})

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2)

    print(f"✅ Wrote: {args.out}")

    # Run manual evaluation
    print("\n" + "=" * 80)
    print("MANUAL EVALUATION RESULTS")
    print("=" * 80)
    
    for q, out in zip(questions, outputs):
        print(f"\n[{out['id']}] {q['question']}")
        print(f"Expected: {q.get('expected_answer', 'N/A')}")
        print(f"Got: {out['answer'][:150]}...")
        print(f"Citations: {out['citations']}")
        print(f"Source hint: {q.get('source_hint', 'N/A')}")


if __name__ == "__main__":
    main()
