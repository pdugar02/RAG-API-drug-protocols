
# Research Protocol Chat App - Run Instructions

## Setup

1. Install dependencies:

```bash
pip install fastapi uvicorn llama-index openai pydantic
```

1. Set your OpenAI API key in a `.env` file (recommended) or via environment variable.

Example `.env` contents:

```python
OPENAI_API_KEY="sk-..."
```

1. Place PDF files in a `data/` directory.

## Start the Server

```bash
uvicorn app:app --reload
```

Server runs at `http://localhost:8000`

## API Endpoints

### 1. Ingest PDFs

```bash
curl -X POST http://127.0.0.1:8000/ingest
```

Indexes all PDFs from `data/` folder.

### 2. Get All Documents

```bash
GET /documents
```

Returns metadata for all indexed documents.

### 3. Get Specific Snippet

```bash
GET /snippets/{snippet_id}
```

Example: `/snippets/snippet_0`

### 4. Chat with Sources

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"user123\",\"message\":\"What's the name of the study?\"}"
```

Body:

```json
{
    "message": "Your question here",
    "session_id": "session_123"
}
```

Returns answer with citations.
