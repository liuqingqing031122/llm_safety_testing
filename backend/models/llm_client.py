import os
from typing import Dict, List
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai

class LLMClient:
    """Client for calling multiple LLM APIs"""
    
    def __init__(self):
        """Initialize all LLM clients with API keys"""
        print("Initializing LLM clients...")
        
        # OpenAI
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        print("✓ OpenAI initialized")
        
        # Anthropic
        self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        print("✓ Anthropic initialized")
        
        # Google Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        print("✓ Google Gemini initialized")

        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
        print("✓ DeepSeek initialized")
        
        print("All LLM clients ready!")
        
    def query_gpt5(self, prompt: str, max_tokens: int = 2000) -> str:
        """Query GPT-5"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ GPT-5 Error: {e}")
            return f"Error querying GPT-5: {str(e)}"
    
    def query_claude(self, prompt: str, max_tokens: int = 2000) -> str:
        """Query Claude Sonnet 4.5"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Claude Error: {e}")
            return f"Error querying Claude: {str(e)}"
    
    def query_gemini(self, prompt: str, max_tokens: int = 2000) -> str:
        """Query Google Gemini 2.5 Flash"""
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens
            )
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            return f"Error querying Gemini: {str(e)}"
    
    def query_deepseek(self, prompt: str, max_tokens: int = 2000) -> str:
        """Query DeepSeek (OpenAI-compatible API)"""
        try:
            deepseek_client = OpenAI(
                api_key=os.getenv('DEEPSEEK_API_KEY'),
                base_url="https://api.deepseek.com/v1"
            )
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],

                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ DeepSeek Error: {e}")
            return f"Error querying DeepSeek: {str(e)}"
    
    def query_model(self, model_name: str, prompt: str) -> str:
        """Query a specific model by name"""
        model_map = {
            'gpt5': self.query_gpt5,
            'claude': self.query_claude,
            'gemini': self.query_gemini,
            'deepseek': self.query_deepseek
        }
        
        if model_name not in model_map:
            return f"Error: Unknown model '{model_name}'"
        
        return model_map[model_name](prompt)
    
    def query_all_models(self, models: List[str], prompt: str, num_runs: int = 1) -> Dict:
        """
        Query multiple models multiple times
        
        Args:
            models: List of model names to query
            prompt: The prompt to send
            num_runs: Number of times to run each model
            
        Returns:
            Dict with model names as keys and list of responses as values
        """
        results = {}
        total_calls = len(models) * num_runs
        current_call = 0
        
        print(f"\n{'='*60}")
        print(f"Starting multi-run testing:")
        print(f"  Models: {len(models)}")
        print(f"  Runs per model: {num_runs}")
        print(f"  Total API calls: {total_calls}")
        print(f"{'='*60}\n")
        
        for model in models:
            print(f"\n🔄 Testing {model.upper()}...")
            model_responses = []
            
            for run in range(num_runs):
                current_call += 1
                print(f"  Run {run + 1}/{num_runs} ({current_call}/{total_calls} total)... ", end='')
                
                response = self.query_model(model, prompt)
                model_responses.append({
                    "run": run + 1,
                    "response": response
                })
                
                print("✓")
            
            results[model] = model_responses
            print(f"✅ {model.upper()} complete ({num_runs} runs)")
        
        print(f"\n{'='*60}")
        print(f"✅ All testing complete! ({total_calls} total API calls)")
        print(f"{'='*60}\n")
        
        return results