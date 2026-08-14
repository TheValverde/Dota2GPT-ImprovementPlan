from __future__ import annotations

from typing import Any

from openai import OpenAI

from dota2_coach.analysis.coverage import (
    build_checklist,
    missing_moments,
    repair_instruction,
)
from dota2_coach.analysis.prompts import SYSTEM_PROMPT, user_prompt
from dota2_coach.analysis.schema import CoachReport
from dota2_coach.errors import OpenAINotConfiguredError


class MatchCoach:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise OpenAINotConfiguredError()
        self._model = model
        self._client = OpenAI(api_key=api_key)

    def analyze(self, match_brief: dict[str, Any]) -> CoachReport:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt(match_brief)},
        ]
        report = self._complete(messages)
        checklist = build_checklist(match_brief)
        missing = missing_moments(report, checklist)
        if not missing:
            return report
        messages.append({"role": "assistant", "content": report.model_dump_json()})
        messages.append({"role": "user", "content": repair_instruction(missing)})
        repaired = self._complete(messages)
        if len(missing_moments(repaired, checklist)) <= len(missing):
            return repaired
        return report

    def _complete(self, messages: list[dict[str, str]]) -> CoachReport:
        completion = self._client.chat.completions.parse(
            model=self._model,
            messages=messages,
            response_format=CoachReport,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("The model did not return a structured coaching report.")
        return parsed
