"""Provider-neutral retrieval and explanation seams for the offline demo.

The default adapter performs lexical retrieval over the local synthetic source
registry.  It returns citations rather than free-floating claims.  A future model
adapter can implement the same interface after retrieval evaluation passes.
"""

import re
from dataclasses import dataclass

from src.evidence import sources_for_circuit


WORD_RE = re.compile(r"[a-z0-9]+")


def _terms(text: str) -> set[str]:
    return set(WORD_RE.findall(text.lower()))


@dataclass(frozen=True)
class Citation:
    source_id: str
    source_type: str
    owner: str
    timestamp: str
    freshness_status: str
    excerpt: str


def retrieve_passages(query: str, circuit_id: str, as_of: str,
                      field_report: bool = False, limit: int = 4) -> list[dict]:
    """Retrieve relevant synthetic passages with stable citations.

    Scores are lexical overlap counts, useful for a reproducible prototype but not a
    claim of semantic search quality.  Zero-overlap sources are omitted.
    """
    query_terms = _terms(query)
    results = []
    for source in sources_for_circuit(circuit_id, as_of, field_report):
        source_terms = _terms(source["text"] + " " + source["source_type"])
        matched = sorted(query_terms & source_terms)
        if not matched:
            continue
        score = len(matched) / max(len(query_terms), 1)
        citation = Citation(source_id=source["source_id"], source_type=source["source_type"],
                            owner=source["owner"], timestamp=source["timestamp"],
                            freshness_status=source["freshness_status"], excerpt=source["text"])
        results.append({"source_id": source["source_id"], "score": round(score, 3),
                        "matched_terms": matched, "citation": citation,
                        "excerpt": source["text"]})
    return sorted(results, key=lambda row: (-row["score"], row["source_id"]))[:limit]


class OfflineExplanationAdapter:
    """Deterministic fallback with the same shape a future model adapter can provide."""

    mode = "offline-template"

    def explain(self, question: str, passages: list[dict]) -> dict:
        citations = [row["citation"].source_id for row in passages]
        if not passages:
            text = "No retrieved source supports an answer; keep the information request open."
        else:
            text = (f"Retrieved {len(passages)} synthetic source passage(s) for review. "
                    "The passages support evidence assembly only; unresolved facts remain unresolved.")
        return {"mode": self.mode, "question": question, "text": text, "citations": citations}


def explain_with_offline_fallback(question: str, passages: list[dict], adapter=None) -> dict:
    """Use an explicitly supplied adapter, or the deterministic offline fallback."""
    return (adapter or OfflineExplanationAdapter()).explain(question, passages)
