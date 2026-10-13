"""全量抓取影神图并写入 Neo4j。"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from graphrag.config import get_chat_llm, get_embedding, load_env, neo4j_conf
from graphrag.graph import TinyGraph

MD = ROOT / "data" / "portraits.md"


def fetch():
    script = ROOT / "download_data" / "get_data_from_url.py"
    subprocess.check_call([sys.executable, str(script)], cwd=str(ROOT / "download_data"))


def ingest():
    load_env()
    url, user, password = neo4j_conf()
    graph = TinyGraph(url, user, password, get_chat_llm("zhipu"), get_embedding())
    print("loading", MD, "size", MD.stat().st_size)
    graph.add_document(str(MD))
    with graph.driver.session() as s:
        n = s.run("MATCH (e:Entity) RETURN count(e) AS c").single()["c"]
        r = s.run("MATCH ()-[rel]->() RETURN count(rel) AS c").single()["c"]
        print("entities", n, "rels", r)


if __name__ == "__main__":
    fetch()
    if not MD.exists() or MD.stat().st_size < 1000:
        raise SystemExit("portraits.md 未生成或过小")
    ingest()
