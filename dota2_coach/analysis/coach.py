from __future__ import annotations

from typing import Any

from openai import OpenAI

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
        completion = self._client.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(match_brief)},
            ],
            response_format=CoachReport,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("The model did not return a structured coaching report.")
        return parsed
