from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    PromptHelper
)
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import os
from dotenv import load_dotenv
import openai

INDEX_PATH = "index.json"
# Load environment from .env (if present) and set OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class IndexStore:
    def __init__(self):
        self.index = None
        self.doc_snippets = {}  # maps snippet ID -> metadata
        self.doc_store = {} # maps doc_id -> document metadata

    def ingest_pdfs(self, pdf_paths: list[str]):
        print("starting ingestion")
        # 1) Load PDFs
        docs = SimpleDirectoryReader(input_files=pdf_paths).load_data()

        # 2) Chunk while preserving headings/structure
        parser = HierarchicalNodeParser.from_defaults()
        nodes = parser(docs)

        print("Nodes are parsed!")
        # 3) Build index
        embed_model = OpenAIEmbedding(model="text-embedding-3-large")
        self.index = VectorStoreIndex(
            nodes,
            embed_model=embed_model,
            show_progress=True
        )
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
            raise RuntimeError("No index loaded")
        llm = OpenAI(model="o1-mini", temperature=0.0)

        engine = self.index.as_query_engine(
            use_sources=True,
            similarity_top_k=3,
            llm=llm
        )
        result = engine.query(query_str)
        return result

    def get_snippet_id(self, snippet_id: str):
        return self.doc_snippets[snippet_id]
    
    def get_docs(self):
        return self.doc_store
    
index_store = IndexStore()
