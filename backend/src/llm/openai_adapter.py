from src.llm.base import LLMProvider
from src.schemas import CV, JD, Evidence
from src.parser import parse_cv, parse_jd
from typing import Dict, Optional
import os
import json
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

class OpenAIProvider(LLMProvider):
    """OpenAI provider using emergentintegrations."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5.2"):
        self.api_key = api_key or os.getenv('EMERGENT_LLM_KEY') or os.getenv('OPENAI_API_KEY')
        self.model = model
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
    
    def extract_cv(self, text: str) -> CV:
        """Use deterministic parser (more reliable than LLM for structured extraction)."""
        return parse_cv(text)
    
    def extract_jd(self, text: str) -> JD:
        """Use deterministic parser."""
        return parse_jd(text)
    
    def rewrite_bullet(self, bullet: str, jd_context: str, evidence: Evidence) -> str:
        """Use LLM to rewrite bullet with JD context."""
        prompt = f"""Rewrite this CV bullet point to align with the job description context.

RULES (CRITICAL - NEVER VIOLATE):
1. Use ONLY facts from the original bullet
2. Start with a strong past-tense action verb
3. Incorporate JD keywords ONLY if they truthfully apply
4. NEVER add metrics, numbers, tools, or achievements not in the original
5. Keep it concise (1-2 lines)

Original bullet:
{evidence.original_text}

Job context:
{jd_context[:200]}

Rewrite (return ONLY the rewritten bullet, nothing else):"""
        
        try:
            response = asyncio.run(self._call_llm(prompt))
            rewritten = response.strip()
            
            # Validate factuality
            if not self._quick_fact_check(rewritten, evidence.original_text):
                # Fallback to original if hallucination detected
                from src.rewriter import _rewrite_bullet
                return _rewrite_bullet(bullet)
            
            return rewritten
        except Exception as e:
            print(f"LLM rewrite failed: {e}")
            from src.rewriter import _rewrite_bullet
            return _rewrite_bullet(bullet)
    
    def fact_check(self, rewritten_bullet: str, evidence: Evidence) -> Dict:
        """Check factuality using LLM."""
        prompt = f"""Check if the rewritten bullet contains ONLY information from the original.

Original:
{evidence.original_text}

Rewritten:
{rewritten_bullet}

Return JSON only: {{"valid": true/false, "violations": ["list of any new facts added"]}}"""
        
        try:
            response = asyncio.run(self._call_llm(prompt))
            result = json.loads(response)
            return result
        except:
            # Fallback to deterministic check
            from src.rewriter import check_factuality
            is_valid = check_factuality(rewritten_bullet, evidence)
            return {"valid": is_valid, "violations": [] if is_valid else ["Potential issue"]}
    
    async def _call_llm(self, prompt: str) -> str:
        """Call OpenAI via emergentintegrations."""
        chat = LlmChat(
            api_key=self.api_key,
            session_id="cv_rewrite",
            system_message="You are a professional CV writer. Follow instructions exactly."
        ).with_model("openai", self.model)
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        return response
    
    def _quick_fact_check(self, rewritten: str, original: str) -> bool:
        """Quick sanity check for hallucinations."""
        import re
        # Check numbers
        orig_nums = set(re.findall(r'\d+', original))
        rewritten_nums = set(re.findall(r'\d+', rewritten))
        if rewritten_nums - orig_nums:
            return False
        return True
