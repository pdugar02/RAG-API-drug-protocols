from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    PromptHelper
)
from llama_index.core.node_parser import HierarchicalNodeParser
# from llama_index.embeddings.openai import OpenAIEmbeddings
import os
import glob
pdf_paths = glob.glob("data/*.pdf")
docs = SimpleDirectoryReader(input_files=pdf_paths).load_data()
# print(docs)
# 2) Chunk while preserving headings/structure
parser = HierarchicalNodeParser.from_defaults()
nodes = parser(docs)
print(nodes[0])