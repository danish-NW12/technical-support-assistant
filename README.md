# 🧠 RAG Assignment — Orbit Technical Support Agent

This repository contains a hands-on assignment for building a **Retrieval-Augmented Generation (RAG)** system using **LangChain**, **ChromaDB**, and the **OpenAI API**.

You will implement document indexing, retrieval, and answer generation for a fictional technical support assistant called **Orbit**.

---

## 📁 Repository Overview

```
.
├─ rag_support_dataset/        # Dataset (see its own README)
├─ src/
│  ├─ build_index.py           # Indexing pipeline (you modify this)
│  └─ rag_pipeline.py          # RAG logic (you modify this)
├─ run_self_eval.py            # Runs evaluation locally
├─ grade_rag.py                # Automatic grader
├─ pyproject.toml              # uv / dependency config
├─ uv.lock                     # Locked environment (if provided)
├─ .env.example                # API key template
├─ README.md                   # This file
└─ instructions.md             # Detailed assignment instructions
```

---

## 🎯 Goal

Build a RAG-based **technical support assistant** that:

- retrieves relevant information from the dataset
- answers questions accurately
- provides clear citations for every answer

---

## 🗂 Dataset

The dataset should be placed in `rag_support_dataset/` and contain:

- structured documentation (`docs/`)
- noisy support tickets (`tickets/`)
- evaluation questions (`gold_questions_public.json`)

> **Note:** This portfolio snippet does not include the dataset. Obtain the assignment dataset separately or use your own support docs/tickets for testing.

---

## ⚙️ Environment Setup (uv)

```bash
uv sync
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```bash
OPENAI_API_KEY=your_key_here
```

---

## 🚀 High-Level Workflow

1. Build a vector index using `src/build_index.py`
2. Implement retrieval + generation in `src/rag_pipeline.py`
3. Run local self-evaluation with `run_self_eval.py`
4. Improve retrieval quality and citations

Detailed instructions are in **`instructions.md`**.

---

## 📊 Evaluation

- Gold questions are evaluated by default
- Hidden questions exist and can be enabled with a flag
- Grading is fully automated and runs locally

---

## 📌 Notes

- Do not hardcode answers
- Use only the provided dataset
- Citations are mandatory
- Focus on retrieval quality over long answers

---

See **`instructions.md`** for full step-by-step guidance.
