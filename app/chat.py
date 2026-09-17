"""Offline CLI demo: python -m app.chat --demo demo/example_semi_arid.json"""
import json, argparse, sys
sys.path.insert(0, ".")
from src.conversation import chat
from src.reasoner import assess

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", default="")
    ap.add_argument("--session", default="demo1")
    a = ap.parse_args()
    if a.demo:
        site = json.load(open(a.demo))
        q = site.pop("query", "")
        print(json.dumps(assess(site, q), indent=2))
        return
    print("Darukaa.Earth scientist (type quit to exit)")
    site = {}
    while True:
        m = input("you> ").strip()
        if m.lower() in ("quit", "exit"): break
        r = chat(a.session, m, site)
        site = r["site"]
        print("ai>", r["reply"][:2000])

if __name__ == "__main__":
    main()
