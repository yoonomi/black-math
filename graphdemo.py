import os

from graphrag.config import get_chat_llm, get_embedding, load_env, neo4j_conf
from graphrag.graph import TinyGraph

load_env()

llm = get_chat_llm("zhipu")
emb = get_embedding()
neo4j_url, neo4j_username, neo4j_password = neo4j_conf()

graph = TinyGraph(
    url=neo4j_url,
    username=neo4j_username,
    password=neo4j_password,
    llm=llm,
    emb=emb,
)

if __name__ == "__main__":
    sample = os.path.join("data", "samples", "portraits_sample.md")
    if os.path.exists(sample):
        graph.add_document(sample)
    query = "黑风山土地是谁"
    print("no_graph:", llm.predict(query))
    print("local:", graph.local_query(query))
