# live runs: the floors against a real model

the offline tests (`uv run pytest`) check the floor code with fake models. these tools run the floors against a live model and check what the workshop pages say should happen. both run on Amazon Nova 2 Lite as shipped, or on any model behind a runner that swaps it

| tool | what it runs | checks |
| --- | --- | --- |
| `scripts/floor-stack --floor 5` | rules agent :8000, character agent :8001, dice mcp :8002, narrator :8009, then the four Floor Boss questions (floor-5-3.md) | each question answered |
| `scripts/floor-stack --floor 7` | the same services with the strands-harness narrator; a question, a narrator restart, the resume and dance-off questions (floor-7.md) | resume names the Ship Canal and Groove 17, at least six dice rolls, session snapshot on disk |
| `STRANDS_LIVE=1 uv run pytest tests/live` | Floor 9 verifier on the floor-9.md Check claims plus one reversed rule, 3 tries each | majority correct verdict, citations only for supported claims |

`floor-stack` gives every process its own process group, so teardown is clean, and restores the run state the floors write into the repo (`characters.json`, `7_strands_harness/.agent/`). logs and summaries: `~/.local/state/floor-stack/`

## other models

`--ec2` routes every agent through `strands-ec2 --replace-bedrock` (heraldstack-infra `terraform/writing-gpu/bench`), which swaps the Nova model id, explicit `BedrockModel` instances and the harness's `bedrock/...` string for an Ollama model. the floor files stay untouched

```bash
scripts/floor-stack --floor 7 --ec2
STRANDS_LIVE=1 uv run --with ollama python "$(command -v strands-ec2)" --replace-bedrock -m pytest tests/live -q
```

## results: qwen3.8:27b on the writing-gpu a10g, 2026-11-18

| floor | result | note |
| --- | --- | --- |
| 1 strands basics | ran, in character | 17 s |
| 2 vended tools | ran, used http_request | 16 s |
| 2 bonus quest | not run unattended | HumanInTheLoop(ask="stdio") asks a person to approve each shell call by design |
| 3 custom tools | ran, rolled the sheet with the dice tool | 33 s |
| 4 mcp | ran, every roll through the mcp dice server | one narrated line contradicts drop-lowest (says a 6 was dropped from 5,5,5,6, reports 17); totals come from the tool |
| 5 a2a | 4/4 Floor Boss questions | 23 to 65 s each, 171 s with startup |
| 7 harness | 3/3 checks | resume across a restart works |
| 8 agentcore | not run | deploys to aws |
| 9 verifier | 2/3 | right verdict on every try; for the fogged claim it lists the sections it checked as citations, where the page expects none. the prompt's "the section names you quoted" reads two ways |

## found while running

- floor-7.md gave the snapshot path as `.agent/sessions/session/seattle-campaign/snapshot_latest.json`; current Strands keeps it under `scopes/agent/<agent id>/snapshots/`. the page now says so
- the Floor 5 run writes the registered party into `characters.json`, a tracked file; `floor-stack` restores it
