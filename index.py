from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

import os
from pathlib import Path
from dotenv import load_dotenv
import openai

INDEX_PATH = "index_store"
# Load .env from project root (same dir as this file) so it works regardless of cwd
load_dotenv(Path(__file__).resolve().parent / ".env")
openai.api_key = os.getenv("OPENAI_API_KEY")

class IndexStore:
    def __init__(self):
        self.index = None
        self.doc_snippets = {}  # maps snippet ID -> metadata
        self.doc_store = {}  # maps doc_id -> document metadata
        
    def ingest_pdfs(self, pdf_paths: list[str]):
        print("starting ingestion")
        # 1) Load PDFs
        docs = SimpleDirectoryReader(input_files=pdf_paths).load_data()

        # 2) Chunk while preserving headings/structure
        parser = HierarchicalNodeParser.from_defaults()
        nodes = parser(docs)

        print("Nodes are parsed!")
        # 3) Build index with empty storage, then persist to disk
        embed_model = OpenAIEmbedding(model="text-embedding-3-large")
        storage_context = StorageContext.from_defaults()  # empty; do not use persist_dir here
        self.index = VectorStoreIndex(
            nodes,
            embed_model=embed_model,
            storage_context=storage_context,
            show_progress=True,
        )
        os.makedirs(INDEX_PATH, exist_ok=True)
        storage_context.persist(persist_dir=INDEX_PATH)
        print("Index is built!")
        # 1) Build doc_store and snippet_store
        for i, node in enumerate(nodes):
            # Create snippet_id
            snippet_id = f"snippet_{i}"
            meta = {
                "doc_id": node.metadata['file_name'],
                "page": node.extra_info.get("page", None),
                "text": node.text
            }

            # Add snippet → metadata
            self.doc_snippets[snippet_id] = meta

            # Initialize doc_store entry if not present
            if node.metadata['file_name'] not in self.doc_store:
                # Attempt to read title and num_pages from node or doc object
                title = getattr(node, "title", None) or node.metadata['file_name']
                num_pages = getattr(node, "num_pages", None) or "unknown"

                self.doc_store[node.metadata['file_name']] = {
                    "title": title,
                    "num_pages": num_pages,
                    "num_snippets": 0
                }

            # Increment snippet count for that document
            self.doc_store[node.metadata['file_name']]["num_snippets"] += 1
        print("finished ingestion!")
        return len(nodes)

    def query(self, query_str: str):
        if not self.index:
            try:
                storage_context = StorageContext.from_defaults(persist_dir=INDEX_PATH)
                self.index = load_index_from_storage(storage_context)
            except Exception as e:
                print(f"Could not load index from {INDEX_PATH}: {e}")
                return "No index loaded"
        # Use same embed model as at index time so query embedding dimension matches stored vectors
        embed_model = OpenAIEmbedding(model="text-embedding-3-large")
        llm = OpenAI(model="gpt-4o-mini", temperature=0.0)
        engine = self.index.as_query_engine(
            use_sources=True,
            similarity_top_k=3,
            llm=llm,
            embed_model=embed_model,
        )
        result = engine.query(query_str)
        return result

    def get_snippet_id(self, snippet_id: str):
        return self.doc_snippets[snippet_id]
    
    def get_docs(self):
        return self.doc_store
    
index_store = IndexStore()
