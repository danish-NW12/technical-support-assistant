import os
import glob
import argparse
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv(override=True)


def load_dataset(dataset_dir: str) -> list[Document]:
    patterns = [
        os.path.join(dataset_dir, "docs", "**", "*.md"),
        os.path.join(dataset_dir, "tickets", "**", "*.txt"),
    ]
    file_paths = []
    for p in patterns:
        file_paths.extend(glob.glob(p, recursive=True))

    documents: list[Document] = []
    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Make paths nice for citations (docs/... or tickets/...)
            norm = path.replace("\\", "/")
            if "/docs/" in norm:
                rel = "docs/" + norm.split("/docs/")[1]
                doc_type = "documentation"
            elif "/tickets/" in norm:
                rel = "tickets/" + norm.split("/tickets/")[1]
                doc_type = "ticket"
            else:
                rel = os.path.basename(norm)
                doc_type = "unknown"

            # Add metadata for potential filtering
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": rel,
                        "doc_type": doc_type,
                        "filename": os.path.basename(norm)
                    }
                )
            )
        except Exception as e:
            print(f"Warning: Failed to load {path}: {e}")
            continue

    if not documents:
        raise ValueError(f"No documents loaded from {dataset_dir}")
    return documents


def main():
    ap = argparse.ArgumentParser(
        description="Build ChromaDB vector index from Orbit support dataset"
    )
    ap.add_argument(
        "--dataset",
        default="rag_support_dataset",
        help="Path to dataset directory"
    )
    ap.add_argument(
        "--persist_dir",
        default="chroma_store",
        help="Directory to persist ChromaDB index"
    )
    ap.add_argument(
        "--collection",
        default="orbit_support",
        help="ChromaDB collection name"
    )
    args = ap.parse_args()

    if not os.path.exists(args.dataset):
        raise FileNotFoundError(
            f"Dataset directory not found: {args.dataset}"
        )

    docs = load_dataset(args.dataset)
    print(f"Loaded {len(docs)} raw documents.")

    # Optimized chunking strategy for technical documentation
    # Chunk size: 1000 chars balances context with precision
    # Overlap: 200 chars ensures important context spans chunk boundaries
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"Split into {len(chunks)} chunks.")

    # Using text-embedding-3-small for good balance of quality and cost
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Build/persist Chroma
    vectordb = Chroma(
        collection_name=args.collection,
        embedding_function=embeddings,
        persist_directory=args.persist_dir,
    )

    # Optional: clear old data (students can comment this out to experiment)
    try:
        vectordb.delete_collection()
        vectordb = Chroma(
            collection_name=args.collection,
            embedding_function=embeddings,
            persist_directory=args.persist_dir,
        )
    except Exception:
        pass

    vectordb.add_documents(chunks)
    print(
        f"✅ Indexed {len(chunks)} chunks into "
        f"'{args.persist_dir}' (collection='{args.collection}')"
    )


if __name__ == "__main__":
    main()
