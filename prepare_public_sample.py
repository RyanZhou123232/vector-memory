"""Download verified HappyDB source data and recreate the active 500-record sample."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

ROOT=Path(__file__).resolve().parent
URL="https://raw.githubusercontent.com/megagonlabs/HappyDB/master/happydb/data/original_hm.csv"
EXPECTED_BLOB_SHA="a7551bb8571a7538d333828198864db48aac6194"


def main():
    directory=ROOT/"data"/"happydb"
    directory.mkdir(parents=True,exist_ok=True)
    raw=directory/"original_hm.csv"
    if not raw.exists():
        temporary=raw.with_suffix(".csv.download")
        with urllib.request.urlopen(URL,timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response,output)
        temporary.replace(raw)
    payload=raw.read_bytes()
    git_sha=hashlib.sha1(b"blob "+str(len(payload)).encode()+b"\0"+payload).hexdigest()
    if git_sha!=EXPECTED_BLOB_SHA:
        raise ValueError("Source changed from the inspected GitHub blob; review the source before proceeding.")
    sample=[]
    total=0
    with raw.open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        fields=reader.fieldnames
        for record in reader:
            total+=1
            text=record["hm"]
            if len(sample)<500 and 30<=len(text.strip())<=600:
                sample.append({"source_dataset":"HappyDB","source_record_id":record["hmid"],
                    "anonymous_author_id":record["wid"],"text":text,
                    "reflection_period":record["reflection"],
                    "perspective":"third_party_self_report"})
    output=directory/"sample_500.jsonl"
    output.write_text("\n".join(json.dumps(item,ensure_ascii=False) for item in sample)+"\n",encoding="utf-8")
    manifest={"dataset":"HappyDB","repository":"https://github.com/megagonlabs/HappyDB",
        "download_url":URL,"original_git_blob_sha":git_sha,
        "raw_sha256":hashlib.sha256(payload).hexdigest(),"source_rows":total,"source_fields":fields,
        "sample_rows":len(sample),"selection":"First 500 original records with 30–600 non-whitespace-trimmed characters; text preserved verbatim.",
        "sample_file":str(output),
        "important":"Active source for the experience-memory app. Anonymous third-party reports; no names, event dates or user relationships are invented.",
        "documentation":"Repository describes crowdsourced recollections and requests citation of the HappyDB LREC 2018 paper. No explicit license claim is made here."}
    (directory/"source_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
    print("First sample records:")
    for record in sample[:4]:
        print(json.dumps(record,ensure_ascii=True))


if __name__=="__main__": main()
