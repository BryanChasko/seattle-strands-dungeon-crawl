"""Live checks for the Floor 9 verifier: the "Check" scenarios from dungeon/workshop/floor-9.md, run
against a real model instead of the offline fakes in tests/test_floor9_verifier.py.

Opt-in only (they call a model and take seconds to minutes). Skipped unless STRANDS_LIVE=1.

  STRANDS_LIVE=1 uv run pytest tests/live -q                       # Amazon Nova 2 Lite, as the floor ships
  STRANDS_LIVE=1 strands-ec2 --replace-bedrock -m pytest tests/live -q   # any model behind a runner that swaps it

Each scenario runs several times: a verifier has to be right on most tries, not once.
"""

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("STRANDS_LIVE") != "1", reason="live model checks: set STRANDS_LIVE=1")

ROOT = Path(__file__).resolve().parents[2]
HANDBOOK = ROOT / "dungeon" / "workshop" / "world" / "crawl-handbook"
TRIES = int(os.environ.get("STRANDS_LIVE_TRIES", "3"))


def passage(section: str) -> str:
    """The handbook section as one quoted passage, labelled with its section name."""
    body = (HANDBOOK / f"{section}.md").read_text().split("\n", 1)[1].strip()
    first = body.split("\n\n")[0:2]
    return f"[{section}] " + " ".join(p.replace("\n", " ") for p in first)


def run(claim: str, sections: list) -> list:
    from verifier import verify_claim

    return [verify_claim(claim, [passage(s) for s in sections]) for _ in range(TRIES)]


def majority(xs) -> bool:
    xs = [bool(x) for x in xs]
    return sum(xs) * 2 > len(xs)


def test_true_ruling_is_supported_with_final_beat_cited():
    verdicts = run("The Final Beat goes to the total closest to 20 without going over.", ["04-final-beat", "03-dance-offs"])
    assert majority(v.supported for v in verdicts), verdicts
    assert majority(any("04-final-beat" in str(c) for c in v.citations) for v in verdicts), verdicts


def test_fogged_ruling_is_unsupported_without_citations():
    verdicts = run("Ties go to the louder dancer.", ["04-final-beat", "03-dance-offs"])
    assert majority(not v.supported for v in verdicts), verdicts
    assert majority(not v.citations for v in verdicts), verdicts


def test_reversed_rule_is_unsupported():
    # not in the guide: the Final Beat's defining reversal, stated backwards
    verdicts = run("In the Final Beat the highest total always wins, even over 20.", ["04-final-beat"])
    assert majority(not v.supported for v in verdicts), verdicts
