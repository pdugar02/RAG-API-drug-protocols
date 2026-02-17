from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

import pymupdf4llm as pymupdf
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
        all_nodes = []
        # 1) Load PDFs
        for pdf_path in pdf_paths:
            # Extract filename from pdf_path
            filename = os.path.basename(pdf_path)
            
            pages = pymupdf.LlamaMarkdownReader().load_data(pdf_path)
            parser = HierarchicalNodeParser.from_defaults()
            nodes = parser(pages)
            for node in nodes:
                # Set or replace document_id with filename
                node.metadata['document_id'] = filename
                
                # Add node to doc_snippets using id_ as snippet_id
                snippet_id = f"snippet_{node.id_}"
                meta = {
                    "doc_id": filename,
                    "page": node.metadata.get("page"),
                    "text": node.text
                }
                self.doc_snippets[snippet_id] = meta
            
            # Add filename to doc_store if not already present
            if filename not in self.doc_store:
                self.doc_store[filename] = {
                    "title": filename,
                    "num_pages": nodes[0].metadata.get("total_pages"),
                    "num_snippets": len(nodes)
                }

            all_nodes.extend(nodes)
   
        print("Nodes are parsed!")
        # 3) Build index with empty storage, then persist to disk
        embed_model = OpenAIEmbedding(model="text-embedding-3-large")
        storage_context = StorageContext.from_defaults()
        self.index = VectorStoreIndex(all_nodes, embed_model=embed_model, storage_context=storage_context, show_progress=True)
        os.makedirs(INDEX_PATH, exist_ok=True)
        storage_context.persist(persist_dir=INDEX_PATH)
        print("Index is built!")

        # Note: doc_store and doc_snippets are now built during the loop above
        print("finished ingestion!")
        return len(all_nodes)

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
