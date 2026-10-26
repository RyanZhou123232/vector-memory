"""Semantic retrieval over experience records. No person-name expansion."""
import unicodedata


def normalize_query(query):
    if not isinstance(query, str):
        raise ValueError("Enter a text question.")
    value=unicodedata.normalize("NFKC", query).translate(str.maketrans({
        "\u2018":"'", "\u2019":"'", "\u201c":'"', "\u201d":'"'}))
    return value.strip().strip('"').strip()


def search(collection, query, k=8):
    normalized=normalize_query(query)
    if not normalized or not 1 <= k <= 50:
        raise ValueError("Enter a question and choose k from 1 to 50.")
    if not collection.count():
        return {"query":query,"matches":[]}
    result=collection.query(query_texts=[normalized],n_results=min(k,collection.count()),
        include=["documents","metadatas","distances"])
    matches=[{"id":key,"text":text,"metadata":meta,"distance":float(distance)}
        for key,text,meta,distance in zip(result["ids"][0],result["documents"][0],
                                        result["metadatas"][0],result["distances"][0])]
    return {"query":query,"matches":matches}


def retrieve_evidence(collection, queries, trace=None):
    by_id={}
    for index, query in enumerate(queries,1):
        result=search(collection,query,40)
        hits=[{"rank":rank,**item} for rank,item in enumerate(result["matches"],1)]
        for item in hits:
            by_id.setdefault(item["id"],{"id":item["id"],"text":item["text"],"metadata":item["metadata"]})
        if trace is not None:
            trace.setdefault("searches",[]).append({"index":index,"query":query,"hits":hits,"returned_count":len(hits)})
    notes=list(by_id.values())
    if len(__import__("json").dumps(notes,ensure_ascii=False))>100_000:
        raise ValueError("Too much evidence matched. Please narrow the question.")
    if trace is not None:
        positions=sum(s["returned_count"] for s in trace["searches"])
        trace["merge"]={"search_count":len(trace["searches"]),"total_hit_positions":positions,
                        "unique_notes":len(notes),"repeated_hit_positions":positions-len(notes)}
        trace["evidence"]=notes
    return notes
