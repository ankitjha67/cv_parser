from typing import List
from src.schemas import MatchReport, InterviewPrep, InterviewQuestion, InterviewPrepSuggestion
import asyncio
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
import random

async def generate_interview_prep(
    match_report: MatchReport,
    jd_title: str,
    user_email: str,
    provider: str = "openai",
    api_key: str = None
) -> InterviewPrep:
    """
    Generate AI-powered interview prep with difficulty levels.
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

Generate comprehensive interview preparation in JSON format with:

1. "questions": [array of 12 questions with:
   - "question": "<question text>"
   - "sample_answer": "<detailed sample answer 2-3 sentences>"
   - "difficulty": "easy" | "medium" | "hard"
   - "category": "behavioral" | "technical" | "situational"
   - "tips": [array of 2-3 tips]
]

2. "gap_strategies": [array of 3-5 objects for each gap with:
   - "gap": "<gap description>"
   - "question": "<likely interview question>"
   - "suggested_answer_approach": "<honest approach>"
   - "difficulty": "easy" | "medium" | "hard"
   - "resources": [2-3 learning resources]
]

Distribute difficulty:
- 4 easy questions (foundational, cultural fit)
- 5 medium questions (job-specific, moderate complexity)
- 3 hard questions (challenging scenarios, technical depth)

Categories:
- 5 behavioral (past experiences, soft skills)
- 5 technical (job-specific skills, tools)
- 2 situational (hypothetical scenarios)

Sample answers should be STAR format where applicable. Tips should be actionable.

Return ONLY valid JSON, no markdown."""
    
    try:
        # Call LLM
        chat = LlmChat(
            api_key=api_key,
            session_id=f"interview_prep_{match_report.id}",
            system_message="You are a professional career coach and interview expert. Provide detailed, helpful responses."
        )
        
        if provider == "openai":
            chat = chat.with_model("openai", "gpt-5.2")
        elif provider == "anthropic":
            chat = chat.with_model("anthropic", "claude-4-sonnet-20250514")
        elif provider == "gemini":
            chat = chat.with_model("gemini", "gemini-2.5-pro")
        elif provider == "ollama":
            # Ollama uses local endpoint
            return _generate_deterministic_prep(match_report, jd_title, user_email)
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        # Parse JSON response
        import json
        data = json.loads(response)
        
        # Build questions
        questions = []
        for item in data.get('questions', [])[:12]:
            questions.append(InterviewQuestion(
                question=item.get('question', ''),
                sample_answer=item.get('sample_answer', ''),
                difficulty=item.get('difficulty', 'medium'),
                category=item.get('category', 'behavioral'),
                tips=item.get('tips', [])
            ))
        
        # Build gap-based suggestions
        gap_suggestions = []
        for item in data.get('gap_strategies', [])[:5]:
            gap_suggestions.append(InterviewPrepSuggestion(
                gap=item.get('gap', 'Unknown'),
                question=item.get('question', ''),
                suggested_answer_approach=item.get('suggested_answer_approach', ''),
                difficulty=item.get('difficulty', 'medium'),
                resources=item.get('resources', [])
            ))
        
        return InterviewPrep(
            user_email=user_email,
            match_report_id=match_report.id,
            jd_title=jd_title,
            questions=questions,
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
    """Fallback deterministic interview prep with difficulty levels."""
    
    questions = []
    
    # Easy behavioral questions (4)
    easy_behavioral = [
        {
            "question": "Tell me about yourself and your background.",
            "sample_answer": "I'm a software engineer with X years of experience in backend development. I've worked on scalable systems at ABC Corp, where I built APIs serving millions of users. I'm passionate about clean code and mentoring junior developers.",
            "tips": ["Keep it under 2 minutes", "Focus on relevant experience", "End with why you're interested in this role"]
        },
        {
            "question": "Why are you interested in this position?",
            "sample_answer": "I'm drawn to this role because it combines my technical skills with the opportunity to work on [specific technology/project]. Your company's focus on [value] aligns with my career goals, and I'm excited about the challenges mentioned in the job description.",
            "tips": ["Research the company beforehand", "Connect your skills to the role", "Show genuine enthusiasm"]
        },
        {
            "question": "What are your greatest strengths?",
            "sample_answer": "My greatest strength is problem-solving under pressure. At my previous role, I debugged a critical production issue affecting 50k users within 2 hours. I stay calm, break down complex problems, and communicate clearly with stakeholders.",
            "tips": ["Choose strengths relevant to the job", "Provide specific examples", "Show impact with numbers if possible"]
        },
        {
            "question": "Where do you see yourself in 5 years?",
            "sample_answer": "In 5 years, I see myself as a senior engineer or tech lead, mentoring junior developers and architecting large-scale systems. I want to deepen my expertise in [relevant technology] and contribute to strategic technical decisions.",
            "tips": ["Show ambition but be realistic", "Align with company growth", "Mention continuous learning"]
        }
    ]
    
    # Medium technical questions (5)
    medium_technical = [
        {
            "question": f"What experience do you have with the key technologies mentioned in the {jd_title} role?",
            "sample_answer": "I have extensive experience with [technology from JD]. At my current role, I used it to build [specific project], which improved performance by [metric]. I'm comfortable with its ecosystem and have also explored [related technology].",
            "tips": ["Be specific about your experience level", "Mention concrete projects", "Admit gaps but show willingness to learn"]
        },
        {
            "question": "Describe your approach to debugging a complex production issue.",
            "sample_answer": "I follow a systematic approach: 1) Gather information (logs, metrics, user reports), 2) Form hypotheses based on data, 3) Test hypotheses with minimal disruption, 4) Implement fix with rollback plan, 5) Post-mortem to prevent recurrence. Communication with stakeholders is continuous throughout.",
            "tips": ["Show structured thinking", "Mention tools you use", "Emphasize communication"]
        },
        {
            "question": "How do you ensure code quality in your projects?",
            "sample_answer": "I practice test-driven development, write comprehensive unit and integration tests, and use code reviews as learning opportunities. I also use linters, static analysis tools, and follow team coding standards. For critical changes, I implement feature flags for gradual rollout.",
            "tips": ["Mention specific practices", "Show you value collaboration", "Talk about continuous improvement"]
        },
        {
            "question": "Explain a time you had to learn a new technology quickly.",
            "sample_answer": "When we decided to migrate to Kubernetes, I had no prior experience. I took an online course, set up a local cluster, migrated a small service first, and documented the process. Within 3 weeks, I successfully migrated 5 microservices and trained my team.",
            "tips": ["Use STAR format", "Show self-driven learning", "Emphasize practical application"]
        },
        {
            "question": "How do you handle disagreements with team members?",
            "sample_answer": "I believe in data-driven discussions. When disagreeing on a technical approach, I present my reasoning with pros/cons, listen to alternative viewpoints, and often create small prototypes to compare. If still unresolved, I escalate to the team lead. The goal is the best outcome, not winning the argument.",
            "tips": ["Show emotional intelligence", "Emphasize collaboration", "Mention conflict resolution"]
        }
    ]
    
    # Hard technical/situational questions (3)
    hard_questions = [
        {
            "question": "Design a scalable system for [specific use case related to role].",
            "sample_answer": "I would start by clarifying requirements: expected scale, latency constraints, and consistency needs. Then I'd design: 1) Load balancer for traffic distribution, 2) Stateless API servers for horizontal scaling, 3) Distributed cache (Redis) for hot data, 4) Database with read replicas, 5) Message queue for async processing. I'd use monitoring to identify bottlenecks and optimize iteratively.",
            "tips": ["Ask clarifying questions first", "Think aloud", "Consider trade-offs", "Mention scalability and reliability"]
        },
        {
            "question": "Tell me about a time you made a significant technical mistake. How did you handle it?",
            "sample_answer": "I once deployed a database migration that locked a critical table during peak hours, causing 15 minutes of downtime. I immediately rolled back, communicated with stakeholders, and scheduled the migration for off-peak hours with proper testing. I also implemented pre-deployment checklists and staging environment validation to prevent similar issues.",
            "tips": ["Be honest and show accountability", "Focus on lessons learned", "Demonstrate growth", "Show you implemented safeguards"]
        },
        {
            "question": "How would you handle a situation where your team is missing a critical deadline?",
            "sample_answer": "I would: 1) Assess what's actually critical vs nice-to-have, 2) Communicate transparently with stakeholders about the situation and revised timeline, 3) Negotiate scope reduction or deadline extension, 4) Rally the team with a clear plan, breaking work into smaller milestones, 5) Post-mortem after delivery to identify root causes and prevent recurrence.",
            "tips": ["Show leadership", "Emphasize communication", "Be pragmatic about trade-offs", "Learn from the situation"]
        }
    ]
    
    # Build questions list
    for q in easy_behavioral:
        questions.append(InterviewQuestion(
            question=q['question'],
            sample_answer=q['sample_answer'],
            difficulty='easy',
            category='behavioral',
            tips=q['tips']
        ))
    
    for q in medium_technical:
        questions.append(InterviewQuestion(
            question=q['question'],
            sample_answer=q['sample_answer'],
            difficulty='medium',
            category='technical' if 'technology' in q['question'].lower() or 'code' in q['question'].lower() else 'behavioral',
            tips=q['tips']
        ))
    
    for q in hard_questions:
        questions.append(InterviewQuestion(
            question=q['question'],
            sample_answer=q['sample_answer'],
            difficulty='hard',
            category='technical' if 'design' in q['question'].lower() else 'situational',
            tips=q['tips']
        ))
    
    # Gap-based strategies
    gap_suggestions = []
    for gap in (match_report.hard_gaps + match_report.soft_gaps)[:5]:
        difficulty = 'hard' if gap in match_report.hard_gaps else 'medium'
        gap_suggestions.append(InterviewPrepSuggestion(
            gap=gap,
            question=f"Can you describe your experience with {gap.split(':')[0] if ':' in gap else gap}?",
            suggested_answer_approach="Be honest about your current level. Frame it positively: 'While I haven't worked extensively with X, I have experience with similar technology Y. I'm a fast learner and have already started exploring X through [online course/project/documentation].' Show enthusiasm to learn and highlight transferable skills.",
            difficulty=difficulty,
            resources=[
                "Official documentation",
                "Online courses (Udemy, Coursera, Pluralsight)",
                "Hands-on practice project",
                "YouTube tutorials",
                "Community forums (Stack Overflow, Reddit)"
            ]
        ))
    
    return InterviewPrep(
        user_email=user_email,
        match_report_id=match_report.id,
        jd_title=jd_title,
        questions=questions,
        gap_based_suggestions=gap_suggestions
    )
