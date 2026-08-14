from __future__ import annotations

from time import time
from typing import Any

from dota2_coach.opendota.client import OpenDotaClient

REPLAY_RETENTION_SECONDS = 10 * 86400


def job_id_from_payload(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict) or not payload:
        return None
    job = payload.get("job") if isinstance(payload.get("job"), dict) else {}
    value = job.get("jobId") or payload.get("jobId")
    return str(value) if value is not None else None


def replay_may_have_expired(start_time: Any) -> bool:
    if not start_time:
        return False
    return int(time()) - int(start_time) > REPLAY_RETENTION_SECONDS


def submit_parse(opendota: OpenDotaClient, match: dict[str, Any]) -> dict[str, Any]:
    match_id = int(match["match_id"])
    if match.get("version") is not None:
        return {
            "match_id": match_id,
            "parsed": True,
            "job_id": None,
            "message": "OpenDota already parsed this match.",
        }
    expired = replay_may_have_expired(match.get("start_time"))
    payload = opendota.request_parse(match_id) or {}
    if not payload:
        refreshed = opendota.get_match(match_id)
        if refreshed.get("version") is not None:
            return {
                "match_id": match_id,
                "parsed": True,
                "job_id": None,
                "message": "OpenDota already parsed this match.",
            }
        payload = {}
    job_id = job_id_from_payload(payload)
    message = "Parse job submitted."
    if expired:
        message = (
            "Parse job submitted, but Valve replays usually expire after about 10 days."
        )
    return {
        "match_id": match_id,
        "parsed": False,
        "job_id": job_id,
        "message": message,
        "replay_may_have_expired": expired,
    }
