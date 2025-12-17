import anthropic
import os
import re
from typing import Dict

class PromptTypeDetector:
    """
    Detects whether a prompt is Direct, Indirect, or Conversational
    """
    
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def detect_prompt_type(self, message: str, turn_number: int = 1) -> Dict:
        """
        Detect prompt type and return runs_per_model
        
        Args:
            message: User's question
            turn_number: Current turn number in conversation
        
        Returns:
            dict with 'type', 'runs_per_model', 'method', 'reasoning', 'detected_entities'
        """
        # ✨ 如果是多轮对话，直接返回 conversational
        if turn_number > 1:
            return {
                "type": "conversational",
                "runs_per_model": 1,  # ✨ 对话型只运行 1 次
                "method": "turn_based",
                "reasoning": f"Turn number {turn_number} > 1, classified as conversational",
                "detected_entities": []
            }
        
        # 使用 AI 检测
        detection_result = self._ai_based_detection(message)
        prompt_type = detection_result["type"]
        
        # ✨ 根据类型决定运行次数
        if prompt_type == "conversational":
            runs_per_model = 1
        else:
            runs_per_model = 5  # ✨ 改为 3（原来是 25）
        
        return {
            "type": prompt_type,
            "runs_per_model": runs_per_model,
            "method": detection_result.get("method", "ai"),
            "reasoning": detection_result.get("reasoning", ""),
            "detected_entities": detection_result.get("detected_entities", [])
        }
    
    def _ai_based_detection(self, message: str) -> Dict:
        """
        Use Claude API to intelligently detect prompt type
        """
        prompt = f"""Analyze this medical question and determine if it mentions specific medical entities.

Question: "{message}"

Determine if this question:
- Mentions specific drug names, brand names, or active ingredients (e.g., "aspirin", "Lipitor", "ibuprofen")
- Mentions specific medical procedures (e.g., "colonoscopy", "MRI", "appendectomy")
- Mentions specific medical devices or treatments (e.g., "pacemaker", "insulin pump")
- Mentions specific vaccines (e.g., "MMR vaccine", "flu shot")
- Mentions specific medical tests (e.g., "blood test", "CT scan")

If it mentions ANY specific entity, classify as "direct".
If it asks general questions without specific entities, classify as "indirect".

Respond with ONLY a JSON object:
{{
  "type": "direct" or "indirect",
  "reasoning": "brief explanation",
  "detected_entities": ["list", "of", "entities"]
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text.strip()
            
            # Clean JSON
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            import json
            result = json.loads(result_text)
            result["method"] = "ai"
            
            return result
            
        except Exception as e:
            print(f"❌ AI detection error: {e}")
            # Fallback to rule-based
            return self._rule_based_detection(message)
    
    def _rule_based_detection(self, message: str) -> Dict:
        """
        Fallback rule-based detection
        """
        message_lower = message.lower()
        
        # Common drug indicators
        drug_patterns = [
            r'\b(aspirin|ibuprofen|acetaminophen|tylenol|advil|motrin)\b',
            r'\b(lipitor|metformin|lisinopril|atorvastatin|omeprazole)\b',
            r'\b(insulin|warfarin|prednisone|albuterol|levothyroxine)\b',
            r'\b(amoxicillin|azithromycin|ciprofloxacin|penicillin)\b',
        ]
        
        # Common procedure indicators
        procedure_patterns = [
            r'\b(surgery|operation|procedure)\b',
            r'\b(colonoscopy|endoscopy|biopsy|x-ray|mri|ct scan)\b',
            r'\b(appendectomy|cholecystectomy|hysterectomy)\b',
        ]
        
        detected_entities = []
        
        # Check for drugs
        for pattern in drug_patterns:
            matches = re.findall(pattern, message_lower)
            detected_entities.extend(matches)
        
        # Check for procedures
        for pattern in procedure_patterns:
            matches = re.findall(pattern, message_lower)
            detected_entities.extend(matches)
        
        if detected_entities:
            return {
                "type": "direct",
                "method": "rule_based",
                "reasoning": f"Detected specific entities: {', '.join(detected_entities[:3])}",
                "detected_entities": list(set(detected_entities))
            }
        else:
            return {
                "type": "indirect",
                "method": "rule_based",
                "reasoning": "No specific drug or procedure names detected",
                "detected_entities": []
            }