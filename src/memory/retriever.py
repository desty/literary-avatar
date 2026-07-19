"""RAG 검색 시스템: 소설 텍스트를 임베딩하고 검색."""

import hashlib
import json
import re
from pathlib import Path
from typing import Optional

import chromadb

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR = DATA_DIR / "vectordb"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[dict]:
    """텍스트를 겹치는 청크로 분할."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        chunks.append({
            "text": chunk_text,
            "start_word": start,
            "end_word": min(end, len(words)),
        })

        start += chunk_size - overlap

    return chunks


def build_index(book_id: str = "sherlock_holmes", force: bool = False) -> chromadb.Collection:
    """소설 텍스트를 청크로 분할하고 ChromaDB에 색인."""
    DB_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(DB_DIR))
    processed = DATA_DIR / "processed" / f"{book_id}.json"
    source_hash = hashlib.sha256(processed.read_bytes()).hexdigest()

    # 원본이 동일한 인덱스만 재사용한다.
    existing = client.list_collections()
    if book_id in [c.name for c in existing]:
        collection = client.get_collection(book_id)
        indexed_hash = (collection.metadata or {}).get("source_sha256")
        if not force and indexed_hash == source_hash:
            print(f"[skip] Collection '{book_id}' is up to date")
            return collection
        reason = "forced" if force else "source changed"
        print(f"[rebuild] Collection '{book_id}' ({reason})")
        client.delete_collection(book_id)

    data = json.loads(processed.read_text(encoding="utf-8"))

    all_docs = []
    all_ids = []
    all_meta = []

    for story in data["stories"]:
        story_num = story["number"]
        story_title = story["title"]
        text = story["text"]

        # 줄바꿈 정리
        text = re.sub(r'\s+', ' ', text)

        chunks = chunk_text(text, chunk_size=400, overlap=80)

        for i, chunk in enumerate(chunks):
            doc_id = f"s{story_num:02d}_c{i:04d}"
            all_docs.append(chunk["text"])
            all_ids.append(doc_id)
            all_meta.append({
                "story_number": story_num,
                "story_title": story_title,
                "chunk_index": i,
            })

    print(f"[indexing] {len(all_docs)} chunks from {len(data['stories'])} stories...")

    # ChromaDB 기본 임베딩 함수 사용 (onnxruntime all-MiniLM-L6-v2)
    collection = client.create_collection(
        name=book_id,
        metadata={"hnsw:space": "cosine", "source_sha256": source_hash},
    )

    # 배치로 추가 (ChromaDB 제한: 한번에 ~5000개)
    batch_size = 500
    for start in range(0, len(all_docs), batch_size):
        end = min(start + batch_size, len(all_docs))
        collection.add(
            documents=all_docs[start:end],
            ids=all_ids[start:end],
            metadatas=all_meta[start:end],
        )

    print(f"[done] Indexed {collection.count()} chunks")
    return collection


def search(
    query: str,
    book_id: str = "sherlock_holmes",
    n_results: int = 5,
    max_story_number: Optional[int] = None,
) -> list[dict]:
    """쿼리와 관련된 소설 텍스트 청크를 검색."""
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection(book_id)

    query_args = {
        "query_texts": [query],
        "n_results": n_results,
    }
    if max_story_number is not None:
        query_args["where"] = {"story_number": {"$lte": max_story_number}}

    results = collection.query(
        **query_args,
    )

    output = []
    for i in range(len(results["ids"][0])):
        output.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })

    return output


if __name__ == "__main__":
    collection = build_index()
    print()

    # 테스트 검색
    test_queries = [
        "Holmes deduction method",
        "Watson description of Holmes",
        "violin and cocaine",
    ]
    for q in test_queries:
        print(f"\n=== Query: {q} ===")
        results = search(q, n_results=2)
        for r in results:
            print(f"  [{r['metadata']['story_title']}] (dist: {r['distance']:.3f})")
            print(f"  {r['text'][:150]}...")
