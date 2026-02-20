import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from backend.models.scoring import MedicalResponseScorer


import pytest
import json
from unittest.mock import AsyncMock, MagicMock

from backend.models.scoring import MedicalResponseScorer


@pytest.mark.asyncio
async def test_direct_scoring_valid_json():

    scorer = MedicalResponseScorer()

    # mock reference loader
    scorer.reference_loader = MagicMock()
    scorer.reference_loader.check_withdrawn_drug.return_value = {
        "has_issues": False,
        "issues": []
    }

    # mock LLM API response
    mock_llm_response = MagicMock()
    mock_llm_response.content = [
        MagicMock(text=json.dumps({
            "safety_status_identification": 0,
            "regulatory_awareness": 0,
            "information_currency": 0,
            "hallucination": 0,
            "harmful_advice": 0,
            "source_responsibility": 0,
            "communication_tone": 0,
            "reasoning": "All good"
        }))
    ]

    scorer.client = MagicMock()
    scorer.client.messages = MagicMock()
    scorer.client.messages.create = AsyncMock(return_value=mock_llm_response)

    result = await scorer.score_direct_prompt_async(
        "Is aspirin safe?",
        "Aspirin is safe when used properly."
    )

    assert result["weighted_score"] == 100
    assert result["prompt_type"] == "direct"
    assert "raw_scores" in result


@pytest.mark.asyncio
async def test_direct_scoring_missing_keys():

    scorer = MedicalResponseScorer()

    scorer.reference_loader = MagicMock()
    scorer.reference_loader.check_withdrawn_drug.return_value = {
        "has_issues": False,
        "issues": []
    }

    # intentionally missing several keys
    mock_llm_response = MagicMock()
    mock_llm_response.content = [
        MagicMock(text=json.dumps({
            "safety_status_identification": 0,
            "reasoning": "Partial result"
        }))
    ]

    scorer.client = MagicMock()
    scorer.client.messages = MagicMock()
    scorer.client.messages.create = AsyncMock(return_value=mock_llm_response)

    result = await scorer.score_direct_prompt_async(
        "Is aspirin safe?",
        "Test"
    )

    # verify missing keys were auto-filled
    assert "regulatory_awareness" in result["raw_scores"]
    assert result["prompt_type"] == "direct"