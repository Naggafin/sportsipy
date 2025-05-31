import os
import hashlib
import json
from pathlib import Path
import sqlite3
from hashlib import md5

DB_PATH = Path(".embed_cache/code_embeddings.db")
DB_PATH.parent.mkdir(exist_ok=True)

try:
    from transformers import AutoTokenizer, AutoModel
    from sentence_transformers import SentenceTransformer
    import torch
    CODE_TOKENIZER = AutoTokenizer.from_pretrained("microsoft/codebert-base")
    CODE_MODEL = AutoModel.from_pretrained("microsoft/codebert-base")
    CODE_MODEL.eval()
    TEXT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False
    CODE_TOKENIZER, CODE_MODEL, TEXT_MODEL = None, None, None
    print("Models unavailable. Install `transformers`, `sentence-transformers`, `torch`.")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                text TEXT,
                embedding TEXT,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def get_cache_key(text: str, model: str) -> str:
    return md5(f"{text}-{model}".encode()).hexdigest()

def load_from_cache(key: str):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT embedding FROM embeddings WHERE id = ?", (key,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None

def save_to_cache(key: str, text: str, embedding, model):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO embeddings (id, text, embedding, model) VALUES (?, ?, ?, ?)",
            (key, text, json.dumps(embedding), model)
        )

def embed(texts, batch_size=32):
    if not MODEL_AVAILABLE:
        raise RuntimeError("Models unavailable. Install required packages.")
    
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        for text in batch:
            model_name = "codebert-base" if Path(text).suffix in [".py"] else "all-MiniLM-L6-v2"
            key = get_cache_key(text, model_name)
            cached = load_from_cache(key)
            if cached:
                results.append(cached)
                continue
            
            if model_name == "codebert-base":
                tokens = CODE_TOKENIZER(text, return_tensors="pt", truncation=True, padding=True)
                with torch.no_grad():
                    output = CODE_MODEL(**tokens)
                    embedding = output.last_hidden_state.mean(dim=1).squeeze().tolist()
            else:
                embedding = TEXT_MODEL.encode(text, convert_to_tensor=False).tolist()
            
            save_to_cache(key, text, embedding, model_name)
            results.append(embedding)
    
    return results