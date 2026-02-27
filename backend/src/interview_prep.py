from typing import List
from src.schemas import MatchReport, InterviewPrep, InterviewPrepSuggestion
import asyncio
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage

async def generate_interview_prep(
    match_report: MatchReport,
    jd_title: str,
    user_email: str,
    provider: str = "openai",
    api_key: str = None
) -> InterviewPrep:
    """
    Generate AI-powered interview prep based on gap analysis.
    """
    api_key = api_key or os.getenv('EMERGENT_LLM_KEY')
    
    # Build context
    hard_gaps_text = "\n".join(f"- {gap}" for gap in match_report.hard_gaps[:5])
    soft_gaps_text = "\n".join(f"- {gap}" for gap in match_report.soft_gaps[:5])
    
    prompt = f"""You are an expert career coach preparing a candidate for a job interview.

Job Title: {jd_title}
Candidate's ATS Score: {match_report.total_score}/100

Hard Gaps (missing requirements):
{hard_gaps_text or 'None'}

Soft Gaps (unclear/not highlighted):
{soft_gaps_text or 'None'}

Generate interview preparation advice in JSON format with:

1. "behavioral_questions": [list of 5 behavioral questions likely to be asked]
2. "technical_questions": [list of 5 technical questions based on the role]
3. "gap_strategies": [list of 3-5 objects with: {{"gap": "<gap>", "question": "<likely question>", "answer_approach": "<how to address>", "resources": ["<learning resource 1>", "<resource 2>"]}}]

Focus on:
- Questions that probe the identified gaps
- Honest ways to address gaps without lying
- Emphasizing transferable skills
- Learning resources (courses, docs, books)

Return ONLY valid JSON, no markdown."""
    
    try:
        # Call LLM
        chat = LlmChat(
            api_key=api_key,
            session_id=f"interview_prep_{match_report.id}",
            system_message="You are a professional career coach and interview expert."
        )
        
        if provider == "openai":
            chat = chat.with_model("openai", "gpt-5.2")
        elif provider == "anthropic":
            chat = chat.with_model("anthropic", "claude-4-sonnet-20250514")
        elif provider == "gemini":
            chat = chat.with_model("gemini", "gemini-2.5-pro")
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        # Parse JSON response
        import json
        data = json.loads(response)
        
        # Build gap-based suggestions
        gap_suggestions = []
        for item in data.get('gap_strategies', [])[:5]:
            gap_suggestions.append(InterviewPrepSuggestion(
                gap=item.get('gap', 'Unknown'),
                question=item.get('question', ''),
                suggested_answer_approach=item.get('answer_approach', ''),
                resources=item.get('resources', [])
            ))
        
        return InterviewPrep(
            user_email=user_email,
            match_report_id=match_report.id,
            jd_title=jd_title,
            behavioral_questions=data.get('behavioral_questions', [])[:5],
            technical_questions=data.get('technical_questions', [])[:5],
            gap_based_suggestions=gap_suggestions
        )
    
    except Exception as e:
        print(f"LLM interview prep failed: {e}")
        # Fallback to deterministic
        return _generate_deterministic_prep(match_report, jd_title, user_email)

def _generate_deterministic_prep(
    match_report: MatchReport,
    jd_title: str,
    user_email: str
) -> InterviewPrep:
    """Fallback deterministic interview prep."""
    
    # Generic behavioral questions
    behavioral = [
        "Tell me about a time when you faced a challenging project and how you handled it.",
        "Describe a situation where you had to work with a difficult team member.",
        "Give an example of how you prioritize multiple deadlines.",
        "Tell me about a time you failed and what you learned from it.",
        "Describe your most significant professional achievement."
    ]
    
    # Generic technical questions (can be enhanced)
    technical = [
        f"What interests you about the {jd_title} role?",
        "Walk me through your approach to solving complex technical problems.",
        "How do you stay updated with the latest technologies in your field?",
        "Describe your experience with the technologies mentioned in the job description.",
        "What's your experience with [specific tool/framework from JD]?"
    ]
    
    # Gap-based strategies
    gap_suggestions = []
    for gap in (match_report.hard_gaps + match_report.soft_gaps)[:5]:
        gap_suggestions.append(InterviewPrepSuggestion(
            gap=gap,
            question=f"Can you tell me about your experience with this: {gap}?",
            suggested_answer_approach="Be honest about your current level. Emphasize willingness to learn, related experience, and any self-study you've done.",
            resources=["Official documentation", "Online courses (Udemy, Coursera)", "Practice projects"]
        ))
    
    return InterviewPrep(
        user_email=user_email,
        match_report_id=match_report.id,
        jd_title=jd_title,
        behavioral_questions=behavioral,
        technical_questions=technical,
        gap_based_suggestions=gap_suggestions
    )
