# Active real-data corpus

HappyDB data is under happydb/. The active file is happydb/sample_500.jsonl.
Each record preserves source_dataset, source_record_id, anonymous_author_id,
text, reflection_period and perspective. The complete downloaded original CSV
and source checksum manifest are beside the sample.

Run prepare_public_sample.py to download/recreate the sample, then app.py seed.
The app does not import names or dates from the old contact schema. Records are
anonymous third-party self-reports. User-added memories are separately labeled.
See ../DATA_PROVENANCE.md and ../dataset_manifest.json.
