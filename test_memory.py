import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import app
import deepseek_memory as memory
from retrieval import normalize_query, retrieve_evidence

NOTES = [
    {"id":"happydb_27673","text":"I went on a successful date with someone I felt sympathy and connection with.",
     "metadata":{"source_dataset":"HappyDB","perspective":"third_party_self_report"}},
    {"id":"happydb_27675","text":"I went to the gym this morning and did yoga.",
     "metadata":{"source_dataset":"HappyDB","perspective":"third_party_self_report"}},
]
PLAN={"intent":"recall","focus":"connection","search_queries":["moments of closeness"]}
VALID={"status":"answered","summary":"One contributor described a sense of connection [happydb_27673].",
       "insights":[{"point":"Shared time with someone may offer inspiration.",
                    "sources":[{"id":"happydb_27673","quote":"sympathy and connection"}]}],"clarification":""}


class FakeCollection:
    def count(self): return 2
    def query(self,**kwargs):
        return {"ids":[[n["id"] for n in NOTES]],"documents":[[n["text"] for n in NOTES]],
                "metadatas":[[n["metadata"] for n in NOTES]],"distances":[[0.1,0.2]]}


class MemoryChecks(unittest.TestCase):
    def test_current_store_is_happydb(self):
        self.assertEqual(app.COLLECTION,"happydb_experiences_minilm_v1")
        self.assertEqual(app.DEFAULT_DATA.parent.name,"happydb")

    def test_contact_schema_is_rejected(self):
        with self.assertRaises(ValueError):
            app.validate_happydb_record({"person":"Someone","date":"2026-01-01","text":"Old schema"})

    def test_happydb_has_no_invented_event_date(self):
        record={"source_dataset":"HappyDB","source_record_id":"27675","anonymous_author_id":"1936",
                "reflection_period":"24h","perspective":"third_party_self_report","text":NOTES[1]["text"]}
        self.assertEqual(app.validate_happydb_record(record),record)
        self.assertNotIn("date",record)

    def test_long_text_is_preserved_in_chunks(self):
        text=(NOTES[1]["text"]+"\n")*120
        chunks=app.split_text(text)
        self.assertGreater(len(chunks),1)
        self.assertEqual("".join(chunks),text)
        self.assertTrue(all(len(app._TOKENIZER.encode(c,add_special_tokens=False).ids)<=220 for c in chunks))

    def test_normalize_pasted_query(self):
        self.assertEqual(normalize_query("\u201cWho\u2019s there?\u201d"),"Who's there?")

    def test_multi_query_dedup_trace(self):
        trace={}
        notes=retrieve_evidence(FakeCollection(),["one","two"],trace)
        self.assertEqual(len(notes),2)
        self.assertEqual(trace["merge"]["total_hit_positions"],4)
        self.assertEqual(trace["merge"]["repeated_hit_positions"],2)

    def test_valid_answer(self):
        self.assertEqual(memory.validate_answer(copy.deepcopy(VALID),NOTES)["status"],"answered")

    def test_forged_source(self):
        value=copy.deepcopy(VALID)
        value["insights"][0]["sources"][0]["id"]="invented"
        with self.assertRaises(ValueError): memory.validate_answer(value,NOTES)

    def test_changed_quote(self):
        value=copy.deepcopy(VALID)
        value["insights"][0]["sources"][0]["quote"]="promised me a job"
        with self.assertRaises(ValueError): memory.validate_answer(value,NOTES)

    def test_uncited_summary(self):
        value=copy.deepcopy(VALID);value["summary"]="A claim with no citation."
        with self.assertRaises(ValueError): memory.validate_answer(value,NOTES)

    def test_empty_answer_has_no_insights(self):
        value=copy.deepcopy(VALID);value["status"]="no_match"
        with self.assertRaises(ValueError): memory.validate_answer(value,NOTES)

    def test_review_rejection_is_not_published(self):
        with patch.object(memory,"configuration",return_value={"model":"test"}), patch.object(
            memory,"chat_json",side_effect=[PLAN,copy.deepcopy(VALID),{"supported":False,"reason":"Wrong meaning"},
                                            copy.deepcopy(VALID),{"supported":False,"reason":"Still wrong"}]) as call:
            with self.assertRaisesRegex(ValueError,"source review"):
                memory.answer_question(FakeCollection(),"Find connection.")
            self.assertEqual(call.call_count,5)

    def test_repair_is_rechecked(self):
        with patch.object(memory,"configuration",return_value={"model":"test","key":"not-for-traces"}), patch.object(
            memory,"chat_json",side_effect=[PLAN,copy.deepcopy(VALID),{"supported":False,"reason":"Clarify"},
                                            copy.deepcopy(VALID),{"supported":True,"reason":"Supported"}]):
            trace={}
            result=memory.answer_question(FakeCollection(),"Find connection.",trace)
            self.assertTrue(result["verification"]["passed"])
            self.assertNotIn("not-for-traces",__import__("json").dumps(trace))

    def test_out_of_scope_stops_before_retrieval(self):
        with patch.object(memory,"configuration",return_value={"model":"test"}), patch.object(
            memory,"chat_json",return_value={"intent":"out_of_scope","search_queries":[]}) as call:
            result=memory.answer_question(FakeCollection(),"Which friend should I contact?")
            self.assertEqual(result["status"],"out_of_scope")
            self.assertEqual(call.call_count,1)

    def test_no_match_needs_no_fabricated_citation(self):
        empty={"status":"no_match","summary":"No relevant experience.","insights":[],"clarification":""}
        with patch.object(memory,"configuration",return_value={"model":"test"}), patch.object(
            memory,"chat_json",side_effect=[PLAN,empty,{"supported":True,"reason":"No evidence"}]):
            result=memory.answer_question(FakeCollection(),"Unrepresented experience?")
            self.assertEqual(result["status"],"no_match")
            self.assertEqual(result["evidence"],[])

    def test_http_error_redacts_credentials(self):
        with patch.object(memory.urllib.request,"urlopen",side_effect=HTTPError(
            "https://api.deepseek.com",401,"secret-test-key",{},None)):
            with self.assertRaises(ValueError) as error:
                memory.chat_json({"key":"secret-test-key","base_url":"https://api.deepseek.com","model":"test"},"JSON",{})
            self.assertNotIn("secret-test-key",str(error.exception))


if __name__=="__main__": unittest.main()
