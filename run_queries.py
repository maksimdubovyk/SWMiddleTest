import csv
import json
from datetime import datetime, timezone

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "mkr1/1.0", "Accept": "application/sparql-results+json"}
QUERIES = ["q1", "q2", "q3"]


def run(query):
    resp = requests.get(ENDPOINT, params={"query": query}, headers=HEADERS, timeout=120)
    resp.raise_for_status()
    return resp.json()


def save_csv(data, path):
    cols = data["head"]["vars"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for b in data["results"]["bindings"]:
            w.writerow([b[c]["value"] if c in b else "" for c in cols])
    return len(data["results"]["bindings"])


def main():
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for name in QUERIES:
        with open(f"{name}.rq", encoding="utf-8") as f:
            query = f.read()
        n = save_csv(run(query), f"{name}.csv")
        print(f"{name}.csv: {n} рядків")
    with open("meta.json", "w", encoding="utf-8") as f:
        json.dump({"retrieved_at": retrieved_at}, f, indent=2)
    print(f"meta.json: retrieved_at={retrieved_at}")


if __name__ == "__main__":
    main()
