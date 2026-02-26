# 📘 Assignment Instructions — Orbit Technical Support RAG

This document contains the **step-by-step instructions** for completing the Orbit Technical Support RAG assignment.

Read this fully before starting.

---

## 1️⃣ What You Are Building

You are building a **Retrieval-Augmented Generation (RAG)** system that acts as a **technical support assistant** for a fictional product platform called **Orbit**.

Your system should:

- retrieve relevant documents from the dataset
- generate correct answers grounded in those documents
- include citations for every answer

You will **not** manually write answers.  
Your code will generate answers automatically and evaluate itself.

---

## 2️⃣ Dataset Overview (Read-Only)

The dataset is located in:

```
rag_support_dataset/
```

It contains:

- `docs/` — manuals, KB articles, troubleshooting guides, release notes
- `tickets/` — noisy historical support tickets
- `gold_questions_public.json` — evaluation questions

📌 **Do not modify dataset files.**

Refer to:

```
rag_support_dataset/README.md
```

for citation examples and dataset structure.

---

## 3️⃣ Environment Setup (uv)

From the project root:

```bash
uv sync
copy .env.example .env
```

Edit `.env` and add your OpenAI API key:

```bash
OPENAI_API_KEY=your_key_here
```

---

## 4️⃣ Step 1 — Build the Vector Index

You will build a ChromaDB index from the dataset.

The indexing script is:

```
src/build_index.py
```

### What you should experiment with:

- chunk size and overlap
- text splitting strategy
- embedding model choice
- whether to re-index from scratch or reuse an index

Run:

```bash
uv run python src/build_index.py --dataset rag_support_dataset --persist_dir chroma_store
```

You may run this multiple times while experimenting.

---

## 5️⃣ Step 2 — Implement the RAG Pipeline

The RAG logic is implemented in:

```
src/rag_pipeline.py
```

You are expected to:

- tune retrieval parameters (e.g. `k`)
- improve prompt quality
- ensure answers are grounded in retrieved context
- return citations using document metadata

### Required function behavior

```python
def rag_answer(question: str, ...) -> dict:
    return {
        "answer": "...",
        "citations": ["docs/cli_reference.md", ...]
    }
```

📌 Citations **must** refer to dataset file paths.

---

## 6️⃣ Step 3 — Self-Evaluation

You do **not** manually create answer files.

Run the self-evaluation script:

```bash
uv run python run_self_eval.py --dataset rag_support_dataset --persist_dir chroma_store
```

This will:

1. Run your RAG pipeline on all gold questions
2. Automatically generate `student_answers.json`
3. Run the grading script
4. Print your score and per-question breakdown

---

## 7️⃣ Optional — Hidden Questions

The dataset also contains **hidden evaluation questions**.

These are **not included by default**.

To include them:

```bash
uv run python run_self_eval.py --dataset rag_support_dataset --persist_dir chroma_store --include_hidden
```

These questions are:

- slightly harder
- optional
- meant for self-challenge or extra credit

---

## 8️⃣ How Grading Works

Each question is scored on:

- **content correctness**
- **citation correctness**

Partial credit is possible.

A detailed report is written to:

```
grading_report.json
```

---

## 9️⃣ Rules & Constraints

- ❌ Do not hardcode answers
- ❌ Do not use external knowledge sources
- ❌ Do not modify dataset files
- ✅ Use only retrieved context to answer
- ✅ Every answer must include citations

---

## 🔍 What We Are Looking For

- correct retrieval (not hallucination)
- clean and relevant citations
- reasonable chunking strategy
- thoughtful prompt design

Long answers are **not** required.  
Correct, grounded answers are.

---

## 🧪 Suggestions for Improvement

You are encouraged to try:

- different chunk sizes
- Max Marginal Relevance (MMR)
- metadata filtering
- better prompts
- re-indexing with different strategies

---

## 🧑‍🏫 Final Notes

This assignment mirrors real-world RAG system design.

If something breaks:

- inspect your retrieved context
- print intermediate outputs
- debug like a production system

Good luck — and focus on **retrieval quality first** 🚀
