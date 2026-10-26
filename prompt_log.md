# Development prompt log — HW6

This log records the staged development from the first prototype through the
HappyDB migration and README review. Quoted prompts are verbatim excerpts;
notes between them summarize actual implementation, debugging and verification.
Elapsed work is not invented. The log is separate from README.md.

## Tools and responsibilities

Codex coding assistant: inspected the existing project's retrieval code in an
earlier discussion; implemented an isolated Python/Chroma prototype, checked
official documentation, and ran local verification. The exact underlying model
identifier is not exposed in this session, so no model version is invented here.
PowerShell/Python: environment setup, import and lifecycle verification.
Web search: official Chroma documentation.
DeepSeek API (deepseek-flash): runtime query planning, source-grounded synthesis
and a separate evidence review; used to interpret natural language and make
retrieved records useful. The model identifier is recorded in live test output.

## Important user prompts (verbatim excerpts)

> Great, let use your test query as our assignment test query. Now tell me where to start, should be began building the vector databse or if theres any thing needed to be prepared

> here is the first 50 testing note. For the query I'll jsut use yours I think it is good enough. And now, what would you recommend to be the next step. I'll say we can start by creating a new file for this Vector database, then store this 50 tesing note somewhere under and start creating the Vector db with the 50 testing note as initial input, also install chrmadb

The user supplied 50 JSONL testing records as an attachment. At that stage the source file was
kept under data/testing_notes.jsonl rather than reproduced in this log; it was
later deleted when the user selected HappyDB.
An earlier discussion included the full assignment specification; this log does
not claim it was withheld from the assistant. The quoted prompts above are
excerpts from a longer planning conversation, not the full conversation export.

## Initial decisions

- Leave the existing Personal Agent unchanged; validate a separate retrieval core.
- Record the agreed question before building; leave the second as a candidate.
- Use explicit persistent Chroma storage and local default embeddings.
- Preserve source text and metadata; never generate user experience ratings.
- Treat the 50 supplied records as testing fixtures, not a verified real corpus.
- Verify imports, repeated imports, semantic ranking, runtime adds and restarts.

Actual run outcomes are recorded separately in verification.json after execution.
Continue this log with real prompts, errors, decisions and results as work proceeds.

## Initial environment debugging

- The first network-restricted install could not reach the package index; the
  authorized download then installed Chroma 1.5.9 in the local virtual environment.
- The first seed operation crashed inside the native ONNX Runtime 1.31.0 import,
  before notes were indexed. A separate import with Python's faulthandler
  reproduced the access violation independently of the app.
- Read-only inspection found Windows C++ runtime DLL version 14.32.31332.0.
  An official upstream report describes crashes with older C++ runtime libraries:
  https://github.com/microsoft/onnxruntime/issues/26599
  This suggests a compatibility issue; it does not prove the exact cause here.
- Testing an older ONNX Runtime inside the prototype environment rather than
  changing Windows system libraries. Final working version and results follow.
- ONNX Runtime 1.20.1 imported successfully in a separate Python process. Pinned
  that version in requirements.txt and retried indexing with the default model.
- The model downloaded successfully, but Chroma 1.5.9 then crashed in its native
  database/index path. Testing Chroma 0.6.3 with NumPy 1.26.4 and a separate store;
  preserving the initial failed store rather than deleting or migrating it.

## User correction and current-version resolution

> the thing is, you might be using the older chroma db language. Since you are installing and usign the newer version, you should not be thinking baout downloading the older version of chroma db but to use the newer version of language to code

- Clarified that the original failure was native Windows access violation, not
  obsolete Python syntax. Followed the user's preference to target current Chroma.
- Restored Chroma 1.5.9 / ONNX Runtime 1.31.0 and the current configuration API.
- Downloaded the official Microsoft runtime package and verified its Microsoft
  Authenticode signature. Extracted the x64 libraries locally, loading newer
  msvcp140.dll before Chroma imports; did not modify Windows system libraries.
- Current Chroma successfully indexed all 50 notes with the local runtime.
  This experiment supports a runtime compatibility explanation for the crashes.
- Preserved obsolete test stores separately. Continued lifecycle verification
  with the current version and a fresh dedicated test store.
- All lifecycle checks passed with current Chroma, including persistence across
  processes, idempotent seeding, a runtime addition and rating, and invalid input.
- Inspected the actual agreed-query ranking: Leo, Omar, Alex Rivera, Maya,
  Alex Wu, Maya, Maya, Maya. Did not label this a successful recommendation;
  ranking and relevance validation remain the next stage.
- Found that repeating local runtime extraction while the app used the DLL could
  fail to overwrite the loaded library. Made identical extraction idempotent and
  added a clear error when a changed runtime is in use; re-extraction then passed.

## People-ranking correction

User feedback (verbatim excerpt after pasting the ranked passages):

> Overall this is not giving me the best rank of people to talk to

- Reproduced the baseline: it ranks isolated passages and can confuse the query's
  navigate/recruiting/rapport combination with tangential material.
- Checked Sentence Transformers' official retrieve-and-rerank documentation and
  the model owner's cross-encoder/ms-marco-MiniLM-L6-v2 repository.
- Tested a local ONNX reranker first. Profiles decorated with IDs and dates
  performed poorly on the agreed question. Kept the experimental results rather
  than calling that a successful fix.
- Tested plain source-text profiles, preserving IDs/dates separately for citation.
  The agreed question ranked Maya then Sophie.
- Added vector candidate retrieval, history expansion for candidate people,
  token-bounded text windows, and local reranking. No name-specific rank rules.
- Normalized pasted curly quotes/apostrophes for model input. The extra opening
  quotation mark in the user example had changed baseline results.
- Preserved latest context in displayed evidence and kept original text intact.
- Asked whether the user preferred local ranking or DeepSeek. This implementation
  remains local and does not send notes to a hosted model.
- Ran a 10-case development comparison: baseline 8 expected top-one hits, revised
  ranking 10. Two cases are formatting variants of the same question. Labels are
  fixture expectations, not independent grading. Kept the unrelated-query output,
  which still demonstrates the need for calibrated no-match handling.

## DeepSeek evidence-based ranking

User selection (verbatim):

> Use DeepSeek for evidence-based ranking

- Switched default people ranking to DeepSeek; retained local ranking as an
  explicit --backend local alternative. Did not silently substitute it on error.
- Read the existing DeepSeek configuration through a path in ignored .env.
  Did not print the key, copy it into code, or modify Personal Agent's configuration.
- Checked the provider's official JSON output documentation. Used the configured
  deepseek-flash model for criteria planning, source-based ranking and a separate
  support-review request. Complementary searches still run through Chroma.
- Added exact original quote and person validation, required-criterion checks,
  explicit no-match/off-topic paths, bounded context and one checked repair.
- Early live checks exposed overstatements about dated offer status and categorical
  lack of expertise. Tightened temporal/source instructions; review remains fallible.
- Empty-result tests exposed a missing planner instruction and a reviewer wrongly
  requiring citations in an empty no-match response. Corrected those distinct paths
  and reran the failing cases without bypassing factual review of recommendations.
- Fifteen deterministic tests passed, covering forged/changed quotes, attribution,
  required criteria, review rejection, bounded repair, no-match, off-topic input
  and HTTP-error credential redaction.
- Live checks ranked Maya and Sophie highest for the agreed question, returned
  out_of_scope for a direct pump-repair task, and no_match for a request for a
  contact with pump-repair experience. Stored note count remained 50.
- Live interactive menu check confirmed the original pasted question displays
  Maya first, Sophie second, note_041 and material caveats.
- Kept live provider outputs under ignored .reports/. No generated responses were
  committed to memory, and no external messages or actions were executed.

## Dataset expansion to 250 notes

User prompt (verbatim):

> new 200 line， intotal we now have 250 line of input

- Validated 200 additional JSONL records: 200 unique IDs, no collisions with the
  original 50. Combined dataset: 250 records across 30 people.
- Preserved the original 50-note file and the new 200-note upload under ignored
  data/, then updated canonical testing_notes.jsonl.
- Chroma imported 200 records and skipped the original 50 unchanged.
- Verified that note_051 is searchable. Updated data/setup documentation.
- Earlier ranking results remain evidence for the 50-note fixture, not proof of
  ranking quality on the expanded corpus. Corpus provenance remains unverified.

## Step 9 direct retrieval audit

User prompt (verbatim):

> then what should we do wo get that information

- Added a direct Chroma diagnostic, bypassing DeepSeek, query rewriting,
  person-history expansion and reranking. Recorded the target sources before
  execution; did not force an expected result or silently replace failing cases.
- Compared actual vector hits with a declared exact-token baseline and saved
  full ordered results, source text, distances and a corpus fingerprint.
- The earlier suggested note_031 example was not clean: it shares feel/making
  with the first question and the baseline finds it. It is outside the vector
  top 40 on the 250-note corpus.
- The original second candidate retrieves note_017 at rank 3 but shares stuck,
  so it does not demonstrate zero content-word overlap under this baseline.
- A revised second candidate, recorded before this diagnostic run but after app
  development, retrieves note_017 at rank 24 with zero shared content tokens.
  It remains unapproved by the user and is not a strong top-few demonstration.
- Reviewed previously declared first-question candidates: note_021 appears at
  rank 31. Did not present this low-rank candidate as excellent retrieval.
- These measurements expose a direct retrieval weakness hidden by the later
  history expansion and DeepSeek ranking. Further work is needed before claiming
  the assignment's semantic test is convincingly demonstrated.

## Full actual-pipeline walkthrough

User request (verbatim):

> 明白了，那我们其实可以 walk through 的东西是，还是刚刚这个问题。然后我们把这个 prompt 发过去，发过去之后我们首先要看 deep seek，把它具体 break down into 哪四个检索句了，以及剩下第五个就是我们这个原本的这个 query 的这个问题嘛，对吧。然后每个检索句我们的这个 database 具体返回了哪四十条 line，那五个一起应该去返回两百条 line，对吧？两百条 line 里面肯定有重复的。然后呢，每一个 query 的四十条 line，它最后 compile 成了哪几个人，对吧。然后最后这个 deep seek 是怎么把它给整合成一个结果说，OK，这几个人是我从上到下推荐的，还有 sources。你跑一个 test，然后把刚刚的那些需要的输出全部都这次让它全部返回回来。

- Added optional tracing to the real DeepSeek pipeline; kept query generation,
  top-40 retrieval, person expansion and ranking rules unchanged.
- Recorded all per-query hits including original documents, metadata, order and
  distances; captured per-query people and their contributing note IDs.
- Recorded deduplication and all expanded histories, plus actual model inputs,
  returned JSON plans/rankings/reviews, and exact source validation outcomes.
- No credentials or authorization headers were written. Corpus hashes before
  and after matched. Added a trace regression check; all 16 tests passed.
- One live run generated four phrases plus the original query: 200 hit positions,
  87 unique notes, 113 repeated positions, 28 people, 230 expanded notes. Final
  order was Maya, Ben, Emma, Lily, Victor, with three model calls and no repair.
- Rendered complete local HTML and Markdown reports alongside the raw JSON.
  Verified all 200 vector hits and 230 history entries appear, with unique
  source anchors and matching per-query/group counts. This is one recorded
  run, not a claim that model outputs or ranking are identical every time.

## Finalizing the two examples and the data route

User instruction (verbatim excerpts):

> 第二个，你直接生成一个吧，就类似这样的问题，就很简单。

> 比如说去网上找那种 Reddit，或者想找别人，找那种账号，就是这个账号它是，就是专门记录自己每天发生了什么或者怎么样，这样的这种账号。然后我扒它一整，就比如说把整个账号所有的内容全部扒下来，然后放到这里面，对吧？这也是一个可行方案。

User's data-route selection (verbatim):

> 这次只用250条模拟联系人，明确标注合成来源

- Ran the second question through the unchanged actual pipeline:
  Who would be a patient teammate when a tough problem leaves me feeling out of my depth?
  Three generated searches plus the original question gave 160 positions,
  86 unique notes, 28 candidate people and 230 expanded notes. Three model calls
  completed successfully; the corpus hash was unchanged.
- Saved final question wording and actual cited examples in test_queries.md and
  semantic_examples.md, preserving the earlier planning record. Did not backdate
  selection of the revised second question.
- Compared original-question content tokens with actual cited passages. For
  Question 1, note_001 was retrieved by generated searches at ranks 30 and 20.
  For Question 2, note_031 was rank 1 for the calm/encouraging subquery and was
  cited for Maya in the final recommendation. Both have zero exact shared content
  tokens with their ORIGINAL questions under the declared baseline.
- Investigated public sources using official Reddit policy, Project Gutenberg
  and Megagon Labs' HappyDB repository. A GitHub connector could read the README
  but returned no CSV text for the large data file; downloaded the public raw CSV
  as a fallback and verified its Git blob hash.
- Prepared a separate faithful HappyDB sample. Its CSV uses reflection, unlike
  reflection_period in the README description; corrected the inspection script
  after checking the actual header. Did not fabricate names/dates or import
  anonymous public experiences into the fictional-contact database.
- Followed the user's explicit choice to retain only the 250 synthetic records.
  Added an origin manifest, provenance statement, visible demo-data label and
  a verified local ZIP for later publication. No data was uploaded yet.
- The student-authored README remains for the user to write later.

## Switch the active app to HappyDB and remove the synthetic corpus

User request (verbatim):

> OK，我看到这个数据了。这个数据本身还 OK，然后我觉得现在可以做的事情是改善我们的 code，让我们所有的 code 去指向这个新的数据库。然后之前那个数据，AI 生成的那些数据，其实就可以删掉了，好吧，所有那些东西可以删掉了。然后删完之后，我们就指向，你改好 code 指向了新的数据库之后，我们可以 run 一个小的 test，看一下这一次的新的 performance 怎么样。

- Replaced active import/search defaults with data/happydb/sample_500.jsonl,
  chroma_store_happydb and happydb_experiences_minilm_v1. Preserved the complete
  downloaded source CSV and its upstream checksum.
- Removed the person/date schema and contact ranking. HappyDB anonymous IDs and
  reflection windows remain provenance metadata, not invented friends or dates.
- Kept the multi-query pipeline: DeepSeek planning, semantic searches, deduplication,
  source-grounded synthesis, exact quote validation, separate review and one repair.
- Added lossless token-based chunking using the actual embedding tokenizer.
- Indexed all 500 source records as 500 stored chunks and verified only HappyDB
  IDs/metadata are in the active store. No user-added test notes remain in it.
- Sixteen validation tests passed. A real smoke test verified restart persistence,
  repeat-import deduplication, known-source retrieval and user addition/search/
  restart in an isolated temporary database.
- Live English checks: connection answered in 21.70 seconds; reset answered in
  18.77 seconds; unrelated reactor-repair query returned no_match in 16.59 seconds.
  These are measured smoke-test outcomes, not a general accuracy estimate.
- A broad deletion request was rejected by automatic approval review because it
  included code/caches beyond the old data. Narrowed cleanup to explicitly named
  old datasets/stores/reports; preserved old code in a verified local ZIP first.
- One retired CLI instance held the old database open. Identified its exact
  process/path/start time, closed the retired app, then completed data deletion.
  No other project or private configuration was changed.
- Deleted the old generated JSONL files, backups/distribution ZIP, all three
  retired Chroma directories and reports containing those records. Retired
  contact-specific code after verifying its local source-only backup.
- Replaced active provenance, manifest, questions and technical documentation.
  The prompt log remains a truthful historical record; the old corpus is not used.

- Follow-up Chinese question also answered with cited HappyDB evidence in
  28.50 seconds. English retrieval phrases were generated for the English corpus;
  final synthesis was in Chinese. Added a prompt constraint against unsupported
  frequency rankings, rather than claiming statistical prevalence from top-k.


## Author-written README review

User prompt (verbatim):

> ok写好了。你看看现在还需要什么

- Read the user's completed author sections. Preserved the author's explanation
  and intent; removed leftover template instructions/blockquote formatting and
  corrected a few spelling/link issues.
- Added the exact original text for happydb_28049 and happydb_27983 beside the
  author's selected examples. Changed warm drink to cocoa because the source
  does not establish temperature. Kept technical AI-generated material below.
- Updated this log's stale initial-phase introduction to describe the actual
  chronology. A fresh-environment reproduction test and the external submission
  actions remain outstanding; no GitHub upload or video submission is claimed.

## Prepare GitHub publication and confirm video requirements

User prompt (verbatim):

> 这个整个push到GitHub上这你可以自己push就行。那个短视频我可以在本地测试吗？你看一下它那个要求有没有说。

- Checked the supplied assignment: local CLI demos are permitted; video must show
  runtime addition, searching and useful use of results, including at least one
  semantic example, then be uploaded with a viewable link.
- Prepared a separate repository named vector-memory. Excluded private .env,
  raw data, databases, virtual environments, cached models, archives and reports.
- GitHub CLI account status was verified through authorized network access.
  The first restricted-network auth probe misleadingly reported an invalid token;
  the network-enabled check confirmed the existing account is authenticated.
- Removed a machine-specific example path from .env.example and clarified that
  users configure their own key. A clean-copy reproduction check is next.

## Clean-copy reproduction before publication

- Exported the committed source into an isolated folder with no personal .env,
  downloaded dataset, database, or native runtime copied from the working app.
- Created a new Python environment, installed the pinned requirements, prepared
  the signed local Windows runtime, downloaded the public HappyDB source and
  indexed all 500 sample records successfully.
- All 16 unit tests passed in that environment; a separate process confirmed
  500 persisted chunks. The local embedding-model cache was shared with this
  machine; first-run model downloading remains documented in the README.
- This check does not use a DeepSeek key. Earlier live pipeline checks are
  recorded above. The authorized GitHub publication is the next action.
