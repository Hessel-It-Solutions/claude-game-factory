# Asset registry

Append-only. Subagents write rows into `production/waves/<wave>.assets.jsonl`; the producer merges them with `tools/gf/gf.sh assets add` and checks with `tools/gf/gf.sh assets check`.

Status: `draft`, `candidate`, `approved`, `rejected`, `replaced by <id>`. Only `approved` assets go into the game.

| asset_id | type | file | model | task_id | refs | credits | status | wave |
|---|---|---|---|---|---|---|---|---|
