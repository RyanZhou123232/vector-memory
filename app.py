"""Current vector-memory app: real HappyDB experiences plus explicit user-added notes."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
DEFAULT_STORE = ROOT / "chroma_store_happydb"
DEFAULT_DATA = ROOT / "data" / "happydb" / "sample_500.jsonl"
COLLECTION = "happydb_experiences_minilm_v1"
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
if os.name == "nt" and (ROOT / ".runtime" / "dlls" / "msvcp140.dll").exists():
    import ctypes
    _runtime_directory = os.add_dll_directory(str(ROOT / ".runtime" / "dlls"))
    _cpp_runtime = ctypes.WinDLL(str(ROOT / ".runtime" / "dlls" / "msvcp140.dll"))

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from retrieval import search

_EMBEDDER = None
_TOKENIZER = None


def embedding_function():
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = DefaultEmbeddingFunction()
    return _EMBEDDER


def open_collection(store=DEFAULT_STORE):
    client = chromadb.PersistentClient(path=str(Path(store).resolve()),
        settings=Settings(anonymized_telemetry=False))
    return client.get_or_create_collection(name=COLLECTION,
        embedding_function=embedding_function(),
        configuration={"hnsw": {"space": "cosine"}},
        metadata={"source_dataset": "HappyDB", "content_type": "experience_memories"})


def split_text(text, budget=220):
    """Use actual model tokens; preserve all original characters across chunks."""
    global _TOKENIZER
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Enter some experience text.")
    if len(text) > 100_000:
        raise ValueError("Please import a smaller text, under 100,000 characters.")
    if _TOKENIZER is None:
        from tokenizers import Tokenizer
        model_cache = Path.home() / ".cache" / "chroma" / "onnx_models" / "all-MiniLM-L6-v2" / "onnx" / "tokenizer.json"
        if not model_cache.is_file():
            embedding_function()(["Initialize the local embedding model."])
        _TOKENIZER = Tokenizer.from_file(str(model_cache))
        _TOKENIZER.no_truncation()
        _TOKENIZER.no_padding()
    encoded = _TOKENIZER.encode(text, add_special_tokens=False)
    if len(encoded.ids) <= budget:
        return [text]
    chunks = []
    start = 0
    for token_index in range(budget, len(encoded.ids), budget):
        end = encoded.offsets[token_index][0]
        if end > start:
            chunks.append(text[start:end])
            start = end
    chunks.append(text[start:])
    assert "".join(chunks) == text
    return chunks


def validate_happydb_record(record):
    if not isinstance(record, dict) or record.get("source_dataset") != "HappyDB":
        raise ValueError("Seed input must be HappyDB records, not contact scenarios.")
    for key in ("source_record_id", "anonymous_author_id", "text", "reflection_period"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f"Missing HappyDB field: {key}")
    if record["reflection_period"] not in ("24h", "3m"):
        raise ValueError("Unexpected HappyDB reflection period.")
    if record.get("perspective") != "third_party_self_report":
        raise ValueError("HappyDB text must be marked as a third-party self-report.")
    return record


def seed(collection, path=DEFAULT_DATA):
    records = []
    seen = set()
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = validate_happydb_record(json.loads(line))
            if record["source_record_id"] in seen:
                raise ValueError("Repeated HappyDB record ID.")
            seen.add(record["source_record_id"])
            records.append(record)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Input line {line_number}: {exc}") from exc
    prepared = []
    for record in records:
        chunks = split_text(record["text"])
        base_id = "happydb_" + record["source_record_id"]
        for index, chunk in enumerate(chunks):
            key = base_id if len(chunks) == 1 else f"{base_id}_chunk_{index + 1}"
            metadata = {"source_dataset": "HappyDB", "source_record_id": record["source_record_id"],
                "anonymous_author_id": record["anonymous_author_id"],
                "reflection_period": record["reflection_period"],
                "perspective": "third_party_self_report",
                "source_url": "https://github.com/megagonlabs/HappyDB",
                "chunk_index": index, "chunk_count": len(chunks)}
            prepared.append({"id": key, "text": chunk, "metadata": metadata})
    existing = {}
    if prepared:
        rows = collection.get(ids=[item["id"] for item in prepared], include=["documents", "metadatas"])
        existing = {key: (text, meta) for key, text, meta in zip(rows["ids"], rows["documents"], rows["metadatas"])}
    pending = []
    for item in prepared:
        if item["id"] in existing:
            if existing[item["id"]] != (item["text"], item["metadata"]):
                raise ValueError(f"Existing ID has different data: {item['id']}")
        else:
            pending.append(item)
    for offset in range(0, len(pending), 50):
        batch = pending[offset:offset + 50]
        collection.add(ids=[n["id"] for n in batch], documents=[n["text"] for n in batch],
            metadatas=[n["metadata"] for n in batch])
        print(f"Indexed {min(offset + 50, len(pending))}/{len(pending)} new chunks.", file=sys.stderr, flush=True)
    return {"source_records": len(records), "added_chunks": len(pending),
            "skipped_chunks": len(prepared) - len(pending), "stored_chunks": collection.count()}


def add_note(collection, text):
    chunks = split_text(text)
    note_id = "memory_" + uuid4().hex
    created = datetime.now(timezone.utc).isoformat()
    ids = [note_id if len(chunks) == 1 else f"{note_id}_chunk_{i + 1}" for i in range(len(chunks))]
    collection.add(ids=ids, documents=chunks, metadatas=[
        {"source_dataset": "User input", "perspective": "user_note", "created_at": created,
         "source_record_id": note_id, "chunk_index": i, "chunk_count": len(chunks)}
        for i in range(len(chunks))])
    return {"added_ids": ids, "stored_chunks": collection.count()}


def ask(collection, question, trace=None):
    from deepseek_memory import answer_question
    return answer_question(collection, question, trace=trace)


def display(result, as_json=False):
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if "summary" in result:
        print("\n" + result["summary"])
        for index, insight in enumerate(result.get("insights", []), 1):
            print(f"\n{index}. {insight['point']}")
            for source in insight["sources"]:
                print(f"   [{source['id']}] {source['quote']}")
        if result.get("evidence"):
            print("\nOriginal sources:")
            for note in result["evidence"]:
                print(f"  [{note['id']}] {note['metadata']['source_dataset']}: {note['text']}")
        return
    if "matches" in result:
        print("\nRetrieved experiences (distance is similarity, not factual confidence):")
        for rank, item in enumerate(result["matches"], 1):
            meta = item["metadata"]
            print(f"\n{rank}. [{item['id']}] {meta['source_dataset']} | distance {item['distance']:.4f}")
            print(item["text"])
        if not result["matches"]:
            print("No records are stored.")
        return
    print(json.dumps(result, ensure_ascii=False, indent=2))


def menu(collection):
    print("Source: HappyDB — anonymous, human-reported daily experiences.")
    print("These accounts are not your personal contacts. Newly added notes stay marked as user input.")
    while True:
        print(f"\nMemory app — {collection.count()} stored experience chunks")
        choice = input("1 Ask about experiences | 2 Add a note | 3 Count | 4 Quit | 5 Search passages\n> ").strip()
        try:
            if choice == "1":
                question = input("Question: ")
                print("Searching experiences and checking source support...")
                display(ask(collection, question))
            elif choice == "2":
                display(add_note(collection, input("Describe the experience: ")))
            elif choice == "3":
                display({"stored_chunks": collection.count()})
            elif choice == "4":
                return
            elif choice == "5":
                display(search(collection, input("Search: ")))
            else:
                print("Choose 1, 2, 3, 4, or 5.")
        except (ValueError, OSError) as exc:
            print(f"Could not complete: {exc}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(dest="command")
    importer = commands.add_parser("seed")
    importer.add_argument("path", nargs="?", type=Path, default=DEFAULT_DATA)
    finder = commands.add_parser("search")
    finder.add_argument("query")
    finder.add_argument("--k", type=int, default=8)
    question = commands.add_parser("ask")
    question.add_argument("query")
    adder = commands.add_parser("add")
    adder.add_argument("--text", required=True)
    commands.add_parser("stats")
    args = parser.parse_args()
    try:
        collection = open_collection(args.store)
        if args.command == "seed":
            display(seed(collection, args.path), args.json)
        elif args.command == "search":
            display(search(collection, args.query, args.k), args.json)
        elif args.command == "ask":
            display(ask(collection, args.query), args.json)
        elif args.command == "add":
            display(add_note(collection, args.text), args.json)
        elif args.command == "stats":
            display({"stored_chunks": collection.count(), "store": str(args.store.resolve()),
                     "collection": COLLECTION, "primary_source": "HappyDB",
                     "embedding_model": "all-MiniLM-L6-v2"}, args.json)
        else:
            menu(collection)
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nClosed. Stored memories remain on disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
