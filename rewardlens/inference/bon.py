"""Frozen Phase II V2 Best-of-N protocol helpers."""

from __future__ import annotations

import hashlib
from itertools import combinations
from typing import Any

SUBSET_SALT = "RewardLens-BoN-Subset-v1"
ORIENTATION_SALT = "RewardLens-PairOrientation-v1"
TIE_SALT = "RewardLens-BoN-Tie-v1"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _norm(text: Any) -> str:
    return str(text).strip().casefold()


def candidate_uid(candidate: dict[str, Any], original_index: int) -> str:
    """Use an immutable manifest id when present, otherwise index plus text."""
    for key in ("candidate_uid", "candidate_id", "id", "uid"):
        value = candidate.get(key)
        if value is not None and str(value) != "":
            return "id:" + str(value)
    return "index:%d|text:%s" % (original_index, str(candidate.get("text") or ""))


def _pool_id(pool: dict[str, Any]) -> str:
    value = pool.get("pool_id") or pool.get("item_id") or pool.get("question_id")
    if value is None or str(value) == "":
        raise ValueError("pool_id, item_id, or question_id is required")
    return str(value)


def pool_candidates(pool: dict[str, Any]) -> dict[str, Any]:
    candidates = pool.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 8:
        raise ValueError("Phase II V2 requires exactly 8 candidates")
    if int(pool.get("n_pool") or 8) != 8:
        raise ValueError("Phase II V2 requires n_pool=8")
    gold = _norm(pool.get("gold_answer") or pool.get("gold"))
    if not gold:
        raise ValueError("gold_answer or gold is required")
    records = []
    gold_indices = []
    texts = set()
    uids = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict) or not str(candidate.get("text") or "").strip():
            raise ValueError("candidate %d is invalid" % index)
        text = _norm(candidate["text"])
        if text in texts:
            raise ValueError("candidate text is duplicated")
        texts.add(text)
        uid = candidate_uid(candidate, index)
        if uid in uids:
            raise ValueError("candidate uid is duplicated")
        uids.add(uid)
        record = {"uid": uid, "index": index, "candidate": candidate}
        records.append(record)
        if text == gold:
            gold_indices.append(index)
    if len(gold_indices) != 1:
        raise ValueError("pool must contain exactly one gold candidate")
    gold_index = pool.get("gold_index")
    if gold_index is not None and int(gold_index) != gold_indices[0]:
        raise ValueError("gold_index does not identify the unique gold candidate")
    return {
        "pool_id": _pool_id(pool),
        "records": records,
        "gold_uid": records[gold_indices[0]]["uid"],
    }


def nested_candidate_sets(pool: dict[str, Any]) -> dict[int, list[str]]:
    parsed = pool_candidates(pool)
    pool_id = parsed["pool_id"]
    gold_uid = parsed["gold_uid"]
    distractors = [
        record["uid"]
        for record in parsed["records"]
        if record["uid"] != gold_uid
    ]
    distractors.sort(key=lambda uid: _sha(SUBSET_SALT + "|" + pool_id + "|" + uid))
    return {
        2: [gold_uid, *distractors[:1]],
        4: [gold_uid, *distractors[:3]],
        8: [gold_uid, *distractors],
    }


def oriented_pair(pool_id: str, uid_i: str, uid_j: str) -> tuple[str, str]:
    if uid_i == uid_j:
        raise ValueError("pair requires distinct candidates")
    left, right = sorted((str(uid_i), str(uid_j)))
    digest = _sha(ORIENTATION_SALT + "|" + str(pool_id) + "|" + left + "|" + right)
    return (left, right) if int(digest, 16) % 2 == 0 else (right, left)


def pair_count(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    return n * (n - 1) // 2


def copeland_select(
    *,
    pool_id: str,
    candidate_uids: list[str],
    pair_outcomes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate one complete unordered-pair graph under the frozen V2 rule."""
    if len(candidate_uids) != len(set(candidate_uids)):
        raise ValueError("candidate uids must be unique")
    expected = {frozenset(pair) for pair in combinations(candidate_uids, 2)}
    seen = set()
    scores = {uid: 0.0 for uid in candidate_uids}
    abstentions = 0
    ties = 0
    for row in pair_outcomes:
        left = str(row.get("left_uid"))
        right = str(row.get("right_uid"))
        key = frozenset((left, right))
        if len(key) != 2 or key not in expected or key in seen:
            raise ValueError("pair graph is not one complete unordered graph")
        seen.add(key)
        outcome = str(row.get("outcome"))
        if outcome == "left":
            scores[left] += 1.0
        elif outcome == "right":
            scores[right] += 1.0
        elif outcome in {"tie", "abstain"}:
            scores[left] += 0.5
            scores[right] += 0.5
            ties += 1
            abstentions += int(outcome == "abstain")
        else:
            raise ValueError("invalid pair outcome: %s" % outcome)
    if seen != expected:
        raise ValueError("pair graph is incomplete")
    maximum = max(scores.values()) if scores else None
    tied = [uid for uid in candidate_uids if scores[uid] == maximum]
    selected = min(tied, key=lambda uid: _sha(TIE_SALT + "|" + str(pool_id) + "|" + uid))
    return {
        "selected_uid": selected,
        "scores": scores,
        "n_pairs": len(pair_outcomes),
        "ties": ties,
        "semantic_abstentions": abstentions,
        "tie_break_applied": len(tied) > 1,
    }


def derive_subset_selections(
    pool: dict[str, Any],
    pair_outcomes: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    """Select C2/C4/C8 winners from one complete N=8 preference graph."""
    parsed = pool_candidates(pool)
    pool_id = parsed["pool_id"]
    gold_uid = parsed["gold_uid"]
    subsets = nested_candidate_sets(pool)
    results = {}
    for n in (2, 4, 8):
        allowed = set(subsets[n])
        induced = [
            row
            for row in pair_outcomes
            if str(row.get("left_uid")) in allowed
            and str(row.get("right_uid")) in allowed
        ]
        result = copeland_select(
            pool_id=pool_id,
            candidate_uids=subsets[n],
            pair_outcomes=induced,
        )
        result["gold_uid"] = gold_uid
        result["success"] = result["selected_uid"] == gold_uid
        results[n] = result
    return results


def pair_outcome(left_uid: str, right_uid: str, parsed_preference: str | None) -> dict[str, str]:
    """Map one A/B response into the frozen graph abstraction."""
    outcome = "left" if parsed_preference == "A" else "right" if parsed_preference == "B" else "abstain"
    return {"left_uid": str(left_uid), "right_uid": str(right_uid), "outcome": outcome}


def evaluate_pairwise_graph(
    pool: dict[str, Any],
    adapter,
    *,
    image_path: str,
    completed_pair_keys: set[str] | None = None,
    on_row=None,
) -> list[dict[str, Any]]:
    """Evaluate the frozen 28-pair graph once for a non-scalar judge adapter."""
    from inference.parsers.ab_parser import parse_ab

    parsed = pool_candidates(pool)
    pool_id = parsed["pool_id"]
    by_uid = {record["uid"]: record["candidate"] for record in parsed["records"]}
    rows = []
    completed_pair_keys = completed_pair_keys or set()
    for uid_i, uid_j in combinations(by_uid, 2):
        left_uid, right_uid = oriented_pair(pool_id, uid_i, uid_j)
        pair_key = pool_id + "|" + left_uid + "|" + right_uid
        if pair_key in completed_pair_keys:
            continue
        prepared = adapter.prepare_inputs(
            image_path=image_path,
            question=pool.get("question"),
            candidate_a=by_uid[left_uid]["text"],
            candidate_b=by_uid[right_uid]["text"],
        )
        result = adapter.judge(prepared)
        if isinstance(result, dict):
            raw = result.get("raw_output")
            preference = result.get("parsed_preference")
            score_a = result.get("score_a")
            score_b = result.get("score_b")
        else:
            raw = str(result)
            preference = None
            score_a = None
            score_b = None
        if preference not in {"A", "B"}:
            preference = parse_ab(raw)
        outcome = pair_outcome(left_uid, right_uid, preference)
        rows.append(
            {
                "pair_key": pair_key,
                "left_uid": left_uid,
                "right_uid": right_uid,
                "candidate_a_uid": left_uid,
                "candidate_b_uid": right_uid,
                "raw_output": raw,
                "parsed_preference": preference,
                "score_a": score_a,
                "score_b": score_b,
                "outcome": outcome["outcome"],
                "status": "ok" if preference in {"A", "B"} else "semantic_abstention",
            }
        )
        if on_row is not None:
            on_row(rows[-1])
    return rows


def scalar_pair_graph(pool: dict[str, Any], scores_by_uid: dict[str, float]) -> list[dict[str, Any]]:
    """Convert native scalar rewards into the same complete pairwise graph."""
    parsed = pool_candidates(pool)
    pool_id = parsed["pool_id"]
    uids = [record["uid"] for record in parsed["records"]]
    if set(scores_by_uid) != set(uids):
        raise ValueError("scalar scores must cover exactly the N=8 candidates")
    rows = []
    for uid_i, uid_j in combinations(uids, 2):
        left_uid, right_uid = oriented_pair(pool_id, uid_i, uid_j)
        left_score = float(scores_by_uid[left_uid])
        right_score = float(scores_by_uid[right_uid])
        outcome = "left" if left_score > right_score else "right" if right_score > left_score else "tie"
        rows.append(
            {
                "left_uid": left_uid,
                "right_uid": right_uid,
                "candidate_a_uid": left_uid,
                "candidate_b_uid": right_uid,
                "score_a": left_score,
                "score_b": right_score,
                "outcome": outcome,
                "status": "ok",
            }
        )
    return rows
