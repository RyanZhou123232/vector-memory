"""Small real-data smoke test: persistence/addition plus optional live synthesis."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import app
from deepseek_memory import configuration


def command(store,*arguments):
    result=subprocess.run([sys.executable,str(app.ROOT/"app.py"),"--store",str(store),"--json",*arguments],
        capture_output=True,text=True,encoding="utf-8",timeout=180,env={**os.environ,"PYTHONUTF8":"1"})
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    return json.loads(result.stdout)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true")
    args=parser.parse_args()
    started=time.perf_counter()
    report={"recorded_at_utc":datetime.now(timezone.utc).isoformat(),"source":"HappyDB","checks":{},"queries":[]}
    collection=app.open_collection()
    count=collection.count()
    assert count>=500
    assert command(app.DEFAULT_STORE,"stats")["stored_chunks"]==count
    repeated=app.seed(collection)
    assert repeated["added_chunks"]==0 and repeated["skipped_chunks"]==500
    report["checks"]["main_store_restart_and_repeat_import"]="passed"
    # An exact known passage checks storage wiring, not semantic-search quality.
    match=app.search(collection,"I went to the gym this morning and did yoga.",k=3)
    assert "happydb_27675" in [n["id"] for n in match["matches"]]
    report["checks"]["known_source_retrievable"]="passed"
    with tempfile.TemporaryDirectory(prefix=".test_happydb_",dir=app.ROOT) as temporary:
        probe=Path(temporary).resolve()
        assert probe.parent==app.ROOT.resolve()
        added=command(probe,"add","--text","Lifecycle test: I repaired my violet ceramic teapot during a pottery workshop.")
        result=command(probe,"search","Lifecycle test: I repaired my violet ceramic teapot during a pottery workshop.","--k","1")
        assert result["matches"][0]["id"]==added["added_ids"][0]
        assert result["matches"][0]["metadata"]["source_dataset"]=="User input"
        assert command(probe,"stats")["stored_chunks"]==1
    report["checks"]["runtime_add_search_and_restart"]="passed"
    if args.live:
        credential=configuration()["key"]
        questions=[
            ("connection","Which everyday moments helped people feel that they belonged?"),
            ("reset","What low-key activities could give someone a breather after a draining day?"),
            ("no_match","Which entries describe repairing a nuclear reactor coolant valve?"),
            ("chinese_question","这些记录里，人们通过哪些日常小事感到与他人更亲近？"),
        ]
        for name,question in questions:
            trace={}
            begin=time.perf_counter()
            try:
                result=app.ask(collection,question,trace=trace)
                entry={"case":name,"question":question,"elapsed_seconds":round(time.perf_counter()-begin,2),
                       "result":result,"trace":trace}
            except ValueError as exc:
                entry={"case":name,"question":question,"elapsed_seconds":round(time.perf_counter()-begin,2),
                       "error":str(exc),"trace":trace}
            report["queries"].append(entry)
            print(json.dumps({"case":name,"seconds":entry["elapsed_seconds"],
                "status":entry.get("result",{}).get("status"),"error":entry.get("error"),
                "unique_sources":entry.get("result",{}).get("retrieved_unique_notes")}),flush=True)
        encoded=json.dumps(report,ensure_ascii=False)
        assert credential not in encoded
    report["checks"]["main_corpus_unchanged"]=collection.count()==count
    report["elapsed_seconds"]=round(time.perf_counter()-started,2)
    directory=app.ROOT/".reports"
    directory.mkdir(exist_ok=True)
    (directory/"happydb_smoke.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"checks":report["checks"],"stored_chunks":count,"elapsed_seconds":report["elapsed_seconds"]},indent=2))
    if args.live:
        assert all("error" not in item for item in report["queries"])
        assert all(item["result"]["status"]=="answered" for item in report["queries"][:2])
        assert report["queries"][2]["result"]["status"]=="no_match"


if __name__=="__main__": main()
