from backend.models.prompt_detector import PromptTypeDetector
from unittest.mock import MagicMock


def test_detect_conversational_turn_based():
    detector = PromptTypeDetector()

    result = detector.detect_prompt_type(
        "What about run 2?",
        turn_number=2
    )

    assert result["type"] == "conversational"
    assert result["runs_per_model"] == 1
    assert result["method"] == "turn_based"


def test_detect_direct_ai_branch():
    detector = PromptTypeDetector()

    # mock AI detection
    detector._ai_based_detection = MagicMock(return_value={
        "type": "direct",
        "method": "ai",
        "reasoning": "Detected aspirin",
        "detected_entities": ["aspirin"]
    })

    result = detector.detect_prompt_type(
        "Is aspirin safe?",
        turn_number=1
    )

    assert result["type"] == "direct"
    assert result["runs_per_model"] == 5


def test_detect_indirect_ai_branch():
    detector = PromptTypeDetector()

    detector._ai_based_detection = MagicMock(return_value={
        "type": "indirect",
        "method": "ai",
        "reasoning": "General question",
        "detected_entities": []
    })

    result = detector.detect_prompt_type(
        "What are common medication side effects?",
        turn_number=1
    )

    assert result["type"] == "indirect"
    assert result["runs_per_model"] == 5