from fastapi import (
    FastAPI, 
    HTTPException
)

from schemas import ChatRequest
from index import index_store
from session import session_store

app = FastAPI(title = "Research Protocol Chat App")

@app.post("/ingest")
async def ingest():
    import glob
    pdf_paths = glob.glob("data/*.pdf")
    count = index_store.ingest_pdfs(pdf_paths)
    return {"status": "ok", "indexed_snippets": count}

@app.get("/documents")
async def get_docs():
    return index_store.get_docs()

@app.get("/snippets/{snippet_id}")
def get_snippet(snippet_id: str):
    snippet = index_store.get_snippet_id(snippet_id)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return snippet

@app.post("/chat")
async def chat(body: ChatRequest):
    session_id = body.session_id
    message = body.message

    session_store.add_message(session_id, {"user": message})
    print(message)
    # Query index
    result = index_store.query(message)
    # Ensure at least one citation
    citations = []
    for src in getattr(result, "source_nodes", []):
        print(src)
        snippet_id = f"snippet_{src.node_id}"
        meta = index_store.doc_snippets.get(snippet_id, {})
        print(meta.get('Text'))
        citations.append({
            "doc_id": meta.get("Node_id"),
            "page_number": meta.get('page'),
            "snippet_id": snippet_id,
            "excerpt": meta.get('Text')
        })

    # Build answer or fallback
    answer_text = result.response or ""
    if not answer_text.strip():
        answer_text = "I don’t know based on the provided documents."

    session_store.add_message(session_id, {"assistant": answer_text})

    return {
        "answer": answer_text,
        "citations": citations
    }
