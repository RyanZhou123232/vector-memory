# Vector Memory — HappyDB


## 1. What my app does and why I chose it

This vector database lets users search everyday experiences by meaning and receive an answer supported by the original entries
I chose this project because I want to explore a memory system for my Personal Agent, where users can find relevant information in their life, and vector db is perfect for refining my project's memory system.

## 2. What I store in the database
At this point, for the sake of testing, I use 500 short experiences from HappyDB. It is a public dataset provided by Megagon Labs. These entries come from 198 anonymous contributors and describe real moments that made them happy. Each short experience is normally stored as one searchable item, while longer entries are split into chunks of up to 220 tokens. I also store metadata such as the original record ID, anonymous contributor ID, data source, reflection period, and chunk information. The reflection period indicates whether a contributor was recalling the past 24 hours or three months; it is not the date of the event.

However, in the future I'll replace this information with my own life diary, also aiming to chat with my agent daily so it can build up its database about my life. 

Here is where the demo data comes from:
[HappyDB — Megagon Labs](https://github.com/megagonlabs/HappyDB)

## 3. How users add information and search

Users interact with the app through a terminal menu.
There are 5 options to interact with the database, depending on your needs. For adding information, it is option 2. It lets users add a new experience, which becomes searchable immediately and remains stored after restarting the app. For search we use option 1. Option 1 accepts a natural-language question. DeepSeek generates focused search phrases, Chroma retrieves related experiences, and DeepSeek combines the retrieved information into an answer with source quotes. Users can also choose option 5 to view retrieved passages directly or option 3 to check the number of stored records.

## 4. Two examples that demonstrate semantic search

Here I'll be showing two examples I ran through to show the search actually works, and it is indeed up to standard. 

### Example 1

**Query:** “Which everyday moments helped people feel that they belonged?”

**Retrieved record**: happydb_28049

**Original text:**

> Eating lunch with my mom and dad.

**Why this demonstrates semantic search:** The entry describes spending time with family, which relates to connection and belonging, even though it does not explicitly mention either concept. A keyword search for “belonged” would miss this entry, while semantic retrieval can identify the relationship between the question and the experience.

### Example 2

**Query:** “What low-key activities could give someone a breather after a draining day?”

**Retrieved record:** happydb_27983

**Original text:**

> Reading comics books whilst drinking cocoa drink.

**Why this demonstrates semantic search:** Reading comics with cocoa describes a quiet leisure activity that could fit the request for a break. The entry does not contain the query’s main words, such as “breather,” “draining,” or “low-key,” but it describes a relevant activity.

## 5. How I used AI


I used Codex to help code and debug the db, including setting up Chroma, importing the dataset, and testing the retrieval workflow. I discussed the design decisions with Codex and walked through the workflow to understand how the code works.
The app also uses DeepSeek API at runtime to break a user’s question into focused search phrases, synthesize the retrieved experiences into an answer, and review whether the cited sources support that answer. This helps the app handle questions with several requirements and produce useful responses grounded in the stored text.
My important prompts and development history are recorded separately in prompt_log.md.



---


## AI-generated technical setup guide

The technical reference below was prepared with AI assistance.

### Current app

The app stores real, anonymous HappyDB self-reported daily experiences and lets
users add their own notes. It retrieves related experiences by meaning, then uses
DeepSeek to synthesize a useful answer with exact source quotes.

Pipeline: question -> DeepSeek search phrases -> Chroma vector searches ->
deduplicate experience records -> DeepSeek synthesis -> quote validation and
separate support review -> display the answer and sources.

It does not rank personal contacts or treat contributors as the user's friends.
No names or event dates are fabricated. The reflection period 24h/3m describes
the original collection task and is not an event date.

### Install and run

Use Python 3.11. From this project folder in PowerShell:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe prepare_public_sample.py
    .\.venv\Scripts\python.exe app.py seed
    .\.venv\Scripts\python.exe app.py

On this machine the source and 500-record database are already prepared.
Double-click Open Memory.cmd to open the current menu.

On Windows with older C++ runtime libraries, setup_windows_runtime.ps1 prepares
Microsoft-signed runtime files locally under ignored .runtime/. It does not
replace Windows system files. Current Chroma 1.5.9 / ONNX Runtime 1.31.0 are used.

### Configuration

Copy .env.example to .env and set your own DEEPSEEK_API_KEY before using option 1
or the ask command. The .env file is ignored by Git. An optional
PERSONAL_AGENT_ENV_FILE setting can reference your own existing configuration;
it is not required. Local search/import/add do not need a hosted API key.

DeepSeek receives the question and retrieved candidate records for planning,
synthesis and review. Usually there are three model calls, with at most one
checked repair. Provider/network errors are shown; no unreviewed answer is
silently substituted.

### Commands

    .\.venv\Scripts\python.exe app.py stats
    .\.venv\Scripts\python.exe app.py search "small moments of connection"
    .\.venv\Scripts\python.exe app.py ask "Which everyday moments helped people feel that they belonged?"
    .\.venv\Scripts\python.exe app.py add --text "Write a new experience here."

The default database is chroma_store_happydb, collection
happydb_experiences_minilm_v1. It is anchored to app.py, so launching from another
directory does not create a second unintended database. The default input is
data/happydb/sample_500.jsonl.

Each record's text is embedded using Chroma's local all-MiniLM-L6-v2 model.
First use downloads the embedding model. Original identifiers and provenance
remain metadata. Long notes are split using the model's actual token offsets
into at most 220-token chunks, preserving all original characters. Re-importing
identical IDs skips them; conflicting content is rejected rather than overwritten.

### Data

HappyDB: https://github.com/megagonlabs/HappyDB

The authors collected recollections of real happy moments. This project preserves
the original text rather than generating interactions. The downloaded original
CSV has 101,094 rows. The initial sample contains 500 qualifying records; the full
CSV is kept locally for later expansion. The downloader verifies the inspected
Git blob checksum. See DATA_PROVENANCE.md and dataset_manifest.json.

No old generated contact data is imported. Old datasets/stores/reports were
removed. Retired source code alone is preserved in ignored .archive/.

### Verification

    .\.venv\Scripts\python.exe -m unittest test_memory -v
    .\.venv\Scripts\python.exe smoke_test.py
    .\.venv\Scripts\python.exe smoke_test.py --live

The live flag uses the configured DeepSeek account. The smoke test checks
persistent storage in a new process, repeat-import deduplication, a known real
source, user addition/search/restart in a separate temporary store, and two
experience questions plus a no-match question. It leaves the main corpus unchanged.
Measured outputs are under ignored .reports/.

Source validation ensures IDs and quotes are real retrieved data. A separate
model review checks support but can still make mistakes. These small smoke checks
do not establish general accuracy or causal conclusions from self-reported data.

### Code map

- app.py: database, import, runtime additions, chunking, CLI and display.
- retrieval.py: normalized semantic queries and multi-query deduplication.
- deepseek_memory.py: planning, source-grounded synthesis, validation and review.
- prepare_public_sample.py: reproducible public-data download and sampling.
- test_memory.py / smoke_test.py: focused validation and real-data checks.

### References

- https://github.com/megagonlabs/HappyDB
- Asai et al., HappyDB: A Corpus of 100,000 Crowdsourced Happy Moments, LREC 2018.
- https://docs.trychroma.com/reference/python
- https://api-docs.deepseek.com/guides/json_mode/

The final live check also covered a Chinese question. The planner generates
English search phrases for the English source corpus and the answer follows
the user's language. Run render_report.py to view .reports/happydb_test_report.html.
The earlier English test timings are preserved as measurements from those runs;
they are not a benchmark or an overall accuracy score.
