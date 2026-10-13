import json
import os
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from file_operation import _create_file_if_not_exists, _create_folder_if_not_exists

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MD_PATH = DATA_DIR / "portraits.md"
PROGRESS_PATH = Path(__file__).resolve().parent / "fetch_progress.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def load_progress():
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    return {"done": [], "failed": []}


def save_progress(progress):
    PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def get_description(url: str) -> str:
    last_error = None
    for attempt in range(4):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            break
        except Exception as e:
            last_error = e
            time.sleep(1.5 * (attempt + 1))
    else:
        raise last_error
    soup = BeautifulSoup(response.content, "html.parser")
    page_pattern = re.compile(r"^第\d+页：")
    description = []
    for p in soup.find_all("p"):
        text = p.get_text()
        if page_pattern.match(text):
            continue
        if p.find("a") and "点击进入" in text:
            break
        if "GsImageLabel" in p.get("class", []):
            break
        if text.strip():
            description.append(text.strip() + "\n\n")
    return "".join(description).strip()


def write2md(role, level, description):
    _create_folder_if_not_exists(str(DATA_DIR))
    _create_file_if_not_exists(str(MD_PATH))
    markdown_content = f"""
## 影神图角色

{role}

### 类型

{level}

### 描述

{description}

"""
    with open(MD_PATH, "a", encoding="utf-8") as file:
        file.write(markdown_content)


if __name__ == "__main__":
    roleinfo_config = Path(__file__).resolve().parent / "roleinfo.json"
    roleinfo_dict = json.loads(roleinfo_config.read_text(encoding="utf-8"))
    progress = load_progress()
    done = set(progress.get("done") or [])
    failed = progress.setdefault("failed", [])

    total = sum(len(v) for v in roleinfo_dict.values())
    n = 0
    for level, items in roleinfo_dict.items():
        for item in items:
            n += 1
            role = item["role"]
            url = item["url"]
            key = f"{level}:{role}"
            if key in done:
                print(f"[{n}/{total}] skip {key}")
                continue
            try:
                description = get_description(url)
                if not description:
                    raise ValueError("empty description")
                write2md(role, level, description)
                done.add(key)
                progress["done"] = sorted(done)
                progress["failed"] = [f for f in failed if f.get("key") != key]
                failed[:] = progress["failed"]
                save_progress(progress)
                print(f"[{n}/{total}] ok {key} chars={len(description)}")
            except Exception as e:
                failed.append({"key": key, "url": url, "error": str(e)})
                progress["failed"] = failed
                save_progress(progress)
                print(f"[{n}/{total}] FAIL {key}: {e}")
            time.sleep(0.4)

    print("done", len(done), "failed", len(failed), "md", MD_PATH, "size", MD_PATH.stat().st_size if MD_PATH.exists() else 0)
