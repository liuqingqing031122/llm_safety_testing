import pytest
import json
from unittest.mock import AsyncMock, MagicMock

from backend.models.scoring import MedicalResponseScorer


@pytest.mark.asyncio
async def test_indirect_scoring_valid_json():

    scorer = MedicalResponseScorer()

    # mock reference loader
    scorer.reference_loader = MagicMock()
    scorer.reference_loader.check_withdrawn_drug.return_value = {
        "has_issues": False,
        "issues": []
    }

    # mock LLM response
    mock_llm_response = MagicMock()
    mock_llm_response.content = [
        MagicMock(text=json.dumps({
            "relevance": 0,
            "accuracy": 0,
            "information_currency": 0,
            "hallucination": 0,
            "harmful_advice": 0,
            "professional_guidance": 0,
            "communication_tone": 0,
            "reasoning": "All good"
        }))
    ]

    scorer.client = MagicMock()
    scorer.client.messages = MagicMock()
    scorer.client.messages.create = AsyncMock(return_value=mock_llm_response)

    result = await scorer.score_indirect_prompt_async(
        "What are common medication side effects?",
        "Side effects vary depending on the drug."
    )

    assert result["prompt_type"] == "indirect"
    assert result["weighted_score"] == 100
    assert "raw_scores" in result