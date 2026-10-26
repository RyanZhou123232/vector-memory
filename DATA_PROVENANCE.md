# Data provenance

The active corpus is a 500-record deterministic sample of HappyDB, published by
Megagon Labs: https://github.com/megagonlabs/HappyDB

The authors describe collecting short accounts of actual happy experiences from
MTurk contributors. These are self-reported experiences, not independently verified
events. The original CSV downloaded for this project contains 101,094 rows.
The active sample is the first 500 original records with 30–600 trimmed characters.
Original text, record ID, anonymous contributor ID and reflection period are kept.
No names, event dates or relationships to the current user are invented. Anonymous
contributor IDs are source identifiers, not contact recommendations.

Source file: data/happydb/original_hm.csv
Active sample: data/happydb/sample_500.jsonl
Source checksums and selection: data/happydb/source_manifest.json
Active database: chroma_store_happydb / happydb_experiences_minilm_v1

To reproduce, run prepare_public_sample.py, then app.py seed. The downloader
checks the inspected upstream Git blob hash before producing the sample.
Raw files and databases are not committed. Follow the upstream documentation and
cite Asai et al., HappyDB: A Corpus of 100,000 Crowdsourced Happy Moments, LREC 2018.
The upstream README was inspected; this project does not invent a license label.

User-added notes have a different source_dataset and perspective. Runtime notes
are stored persistently but are not attributed to HappyDB contributors.

The previous generated contact scenarios, their Chroma stores and reports
containing those scenarios have been deleted at the user's request. Only a local,
ignored ZIP of previous source code was kept before retiring obsolete code;
it contains no source datasets or database files. The development prompt log
preserves the sequence of decisions.
