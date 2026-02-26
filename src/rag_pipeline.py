from dotenv import load_dotenv
from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(override=True)

SYSTEM = """You are a technical support assistant for the fictional Orbit Platform.
Your role is to provide accurate, concise answers based ONLY on the provided context documents.

CRITICAL RULES:
1. Use ONLY information from the provided context. Do not use external knowledge or make assumptions.
2. If the context doesn't contain enough information to answer, explicitly state: "I don't have enough information in the provided context to answer this question."
3. Keep answers concise and practical - focus on actionable steps or direct answers.
4. ALWAYS cite your sources using the exact file paths shown in the context metadata (e.g., "docs/cli_reference.md", "docs/error_code_catalog.md").
5. When mentioning commands, error codes, or specific procedures, you MUST cite the relevant source document.
6. Format citations clearly in your answer (e.g., "According to docs/cli_reference.md, the command is...").
7. If multiple sources are relevant, cite all of them."""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", """Question: {question}

Context from documentation:
{context}

IMPORTANT INSTRUCTIONS:
- Answer the question using ONLY the information from the context above.
- Be specific and cite the source files using the exact paths shown (e.g., "According to docs/cli_reference.md...").
- Every fact, command, or procedure you mention must be cited with its source file.
- If multiple sources are relevant, cite all of them.
- Keep your answer concise and practical.
- Do not make up information that is not in the context.""")
])


def _format_context(docs) -> str:
    parts = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "unknown")
        parts.append(f"[{i}] SOURCE: {src}\n{d.page_content.strip()}")
    return "\n\n".join(parts)


def _extract_citations(docs) -> List[str]:
    seen = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        if src not in seen:
            seen.append(src)
    return seen


def rag_answer(
    question: str,
    persist_dir: str = "chroma_store",
    collection: str = "orbit_support",
    filter_metadata: Optional[Dict] = None
) -> Dict:
    """
    Generate an answer using RAG pipeline.

    Args:
        question: The question to answer
        persist_dir: Directory where ChromaDB index is stored
        collection: ChromaDB collection name
        filter_metadata: Optional metadata filter
            (e.g., {"doc_type": "documentation"})

    Returns:
        Dictionary with "answer" and "citations" keys
    """
    if not question or not question.strip():
        return {
            "answer": "Please provide a valid question.",
            "citations": []
        }

    try:
        # Embeddings must match what you used during indexing
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        vectordb = Chroma(
            collection_name=collection,
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )

        # Use MMR (Max Marginal Relevance) for better diversity in retrieval
        # MMR balances relevance with diversity to avoid redundant chunks
        # k=6 retrieves more candidates, MMR selects diverse top results
        search_kwargs = {
            "k": 6,  # Fetch more candidates
            "fetch_k": 10,  # Consider top 10 for MMR selection
            "lambda_mult": 0.7  # Balance: 0.7 = more diversity
        }

        # Add metadata filter if provided
        if filter_metadata:
            search_kwargs["filter"] = filter_metadata

        retriever = vectordb.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs
        )
        retrieved = retriever.invoke(question)

        if not retrieved:
            return {
                "answer": "I don't have enough information in the provided context to answer this question.",
                "citations": []
            }

        context = _format_context(retrieved)
        citations = _extract_citations(retrieved)

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        msg = PROMPT.format_messages(question=question, context=context)
        resp = llm.invoke(msg)

        return {"answer": resp.content, "citations": citations}

    except Exception as e:
        return {
            "answer": f"Error generating answer: {str(e)}",
            "citations": []
        }
