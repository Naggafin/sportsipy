import hashlib
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_db"
))

collection = client.get_or_create_collection("code_chunks")

def _compute_chunk_id(file_path, chunk_text):
    return hashlib.md5(f"{file_path}-{chunk_text}".encode()).hexdigest()

def add_chunks(chunks, embeddings, batch_size=100):
    documents = []
    ids = []
    metadatas = []
    
    existing_ids = set(collection.get()["ids"])
    
    for i, (file_path, chunk_data) in enumerate(chunks):
        chunk_text = chunk_data["text"]
        metadata = chunk_data["metadata"]
        metadata["path"] = str(file_path)
        metadata["mcp_id"] = _compute_chunk_id(file_path, chunk_text)
        metadata["source"] = "codebase"
        doc_id = metadata["mcp_id"]
        
        if doc_id not in existing_ids:
            documents.append(chunk_text)
            ids.append(doc_id)
            metadatas.append(metadata)
        
        if len(documents) >= batch_size or i == len(chunks) - 1:
            if documents:
                collection.upsert(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas,
                    embeddings=embeddings[i-len(documents):i] if embeddings else None
                )
                client.persist()
            documents, ids, metadatas = [], [], []
    
    if documents:
        collection.upsert(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
            embeddings=embeddings[-len(documents):] if embeddings else None
        )
        client.persist()

def query(text, embed_fn, k=5):
    embedding = embed_fn([text])[0]
    results = collection.query(query_embeddings=[embedding], n_results=k)
    
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    
    return docs, metas