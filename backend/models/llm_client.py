import os
from typing import Dict, List, Optional
from openai import OpenAI
from anthropic import Anthropic
from google import genai


class LLMClient:
    """Client for calling multiple LLM APIs"""

    def __init__(self):
        print("Initializing LLM clients...")

        # OpenAI (GPT-5)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("✓ OpenAI initialized")

        # Anthropic (Claude)
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        print("✓ Anthropic initialized")

        # Google (Gemini)
        self.gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        print("✓ Google Gemini initialized")

        # DeepSeek: OpenAI-compatible API
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
        print("✓ DeepSeek initialized")

        print("All LLM clients ready!")

    # ---------------------------- GPT-5 ----------------------------
    def query_gpt5(self, prompt: str, max_tokens: int = 5000) -> str:
        try:
            response = self.openai_client.responses.create(
                model="gpt-5",
                input=[
                    {"role": "user", "content": prompt}
                ],
                max_output_tokens=max_tokens,
                tools=[
                    {"type": "web_search"}
                ],
            )

            return response.output_text

        except Exception as e:
            print(f"❌ GPT-5 Error: {e}")
            return f"Error querying GPT-5: {e}"
        
    # ---------------------------- Claude ----------------------------
    def query_claude(self, prompt: str, max_tokens: int = 5000) -> str:
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search"
                }]
            )

            return "".join(b.text for b in response.content if b.type == "text") or ""
        except Exception as e:
            print(f"❌ Claude Error: {e}")
            return f"Error querying Claude: {e}"

    # ---------------------------- Gemini ----------------------------
    def query_gemini(self, prompt: str, max_tokens: int = 5000) -> str:
        try:
            from google.genai import types

            search_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

            config = types.GenerateContentConfig(
                tools=[search_tool],
                max_output_tokens=max_tokens,
            )

            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )

            return response.text

        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            return f"Error querying Gemini: {e}"


    # ---------------------------- DeepSeek ----------------------------
    def query_deepseek(self, prompt: str, max_tokens: int = 5000) -> str:
        """
        Query DeepSeek using OpenAI-compatible API
        """
        try:
            # DeepSeek uses the standard chat completions format
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ DeepSeek Error: {e}")
            return f"Error querying DeepSeek: {e}"

    # ---------------------------- Routing ----------------------------
    def query_model(self, model_name: str, prompt: str) -> str:
        model_map = {
            "gpt5": self.query_gpt5,
            "claude": self.query_claude,
            "gemini": self.query_gemini,
            "deepseek": self.query_deepseek,
        }
        if model_name not in model_map:
            return f"Unknown model '{model_name}'"
        return model_map[model_name](prompt)

    # ---------------------------- Multi-run ----------------------------
    def query_all_models(self, models: List[str], prompt: str, num_runs: int = 1) -> Dict:
        results = {}
        for m in models:
            results[m] = []
            for i in range(num_runs):
                results[m].append({
                    "run": i + 1,
                    "response": self.query_model(m, prompt),
                })
        return results

    # ---------------------------- Unified interface ----------------------------
    async def generate_response(self, model_name: str, message: str, conversation_history=None):
        """
        Generate response - compatible with main.py
        """
        full_prompt = ""

        if conversation_history:
            for msg in conversation_history:
                full_prompt += f"{msg['role']}: {msg['content']}\n"
        full_prompt += f"user: {message}\n"

        return self.query_model(model_name.lower(), full_prompt)