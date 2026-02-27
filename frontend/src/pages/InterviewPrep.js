import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Brain, Lightbulb, Target, Loader2, BookOpen, TrendingUp } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DIFFICULTY_COLORS = {
  easy: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  hard: 'bg-red-100 text-red-800 border-red-200'
};

const CATEGORY_ICONS = {
  behavioral: '👥',
  technical: '💻',
  situational: '🎯'
};

function InterviewPrepPage() {
  const { getAuthHeader } = useAuth();
  const [searchParams] = useSearchParams();
  const reportId = searchParams.get('report_id');
  
  const [prep, setPrep] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    if (reportId) {
      checkExistingPrep();
    }
  }, [reportId]);

  const checkExistingPrep = async () => {
    // In a real app, we'd have an endpoint to get prep by report_id
    // For now, we'll just wait for user to generate
  };

  const handleGenerate = async () => {
    if (!reportId) {
      alert('No match report selected');
      return;
    }

    setGenerating(true);
    try {
      const response = await axios.post(
        `${API}/interview-prep`,
        {
          match_report_id: reportId,
          provider: 'openai'
        },
        { headers: getAuthHeader() }
      );
      setPrep(response.data);
    } catch (error) {
      console.error('Failed to generate prep:', error);
      alert('Failed to generate interview prep');
    } finally {
      setGenerating(false);
    }
  };

  const filteredQuestions = prep?.questions.filter(q => {
    const difficultyMatch = selectedDifficulty === 'all' || q.difficulty === selectedDifficulty;
    const categoryMatch = selectedCategory === 'all' || q.category === selectedCategory;
    return difficultyMatch && categoryMatch;
  }) || [];

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-2">AI-Powered</p>
          <h1 className="text-4xl md:text-6xl font-serif tracking-tight font-medium leading-[0.9] mb-4">
            Interview Preparation
          </h1>
          <p className="text-lg font-sans font-light leading-relaxed text-muted-foreground max-w-2xl">
            Tailored questions, sample answers, and strategies based on your CV-JD match analysis.
          </p>
        </div>

        {!prep && !loading && (
          <div className="border border-border bg-card p-12 text-center">
            <Brain className="w-16 h-16 mx-auto mb-6 text-primary" strokeWidth={1.5} />
            <h2 className="text-2xl font-serif mb-4">Generate Your Interview Prep</h2>
            <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
              Get AI-powered interview questions with sample answers categorized by difficulty (Easy, Medium, Hard) and type (Behavioral, Technical, Situational).
            </p>
            <button
              onClick={handleGenerate}
              disabled={generating || !reportId}
              className="bg-primary text-primary-foreground px-8 py-4 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center gap-2 mx-auto"
              data-testid="generate-prep-button"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Brain className="w-5 h-5" />
                  Generate Interview Prep
                </>
              )}
            </button>
            {!reportId && (
              <p className="text-sm text-accent mt-4">Please select a match report from the dashboard first.</p>
            )}
          </div>
        )}

        {prep && (
          <div className="space-y-8">
            {/* Header with filters */}
            <div className="border border-border bg-card p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-serif mb-1">{prep.jd_title}</h2>
                  <p className="text-sm text-muted-foreground font-mono">
                    {prep.questions.length} questions • {prep.gap_based_suggestions.length} gap strategies
                  </p>
                </div>
                <div className="flex gap-3">
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => setSelectedDifficulty(e.target.value)}
                    className="border border-input bg-background px-4 py-2 text-sm font-mono uppercase"
                    data-testid="difficulty-filter"
                  >
                    <option value="all">All Difficulties</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="border border-input bg-background px-4 py-2 text-sm font-mono uppercase"
                    data-testid="category-filter"
                  >
                    <option value="all">All Types</option>
                    <option value="behavioral">Behavioral</option>
                    <option value="technical">Technical</option>
                    <option value="situational">Situational</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Questions Section */}
            <div>
              <div className="flex items-center gap-3 mb-6">
                <BookOpen className="w-6 h-6 text-primary" />
                <h2 className="text-3xl font-serif">Interview Questions</h2>
              </div>
              <div className="space-y-6">
                {filteredQuestions.map((question, idx) => (
                  <div
                    key={idx}
                    className="border border-border bg-card overflow-hidden hover:shadow-lg transition-all"
                    data-testid={`question-${idx}`}
                  >
                    <div className="p-6 border-b border-border/50 bg-muted/10">
                      <div className="flex items-start justify-between gap-4 mb-3">
                        <h3 className="text-xl font-serif flex-1">
                          {CATEGORY_ICONS[question.category]} {question.question}
                        </h3>
                        <div className="flex gap-2">
                          <span className={`px-3 py-1 text-xs font-mono uppercase border ${DIFFICULTY_COLORS[question.difficulty]}`}>
                            {question.difficulty}
                          </span>
                          <span className="px-3 py-1 text-xs font-mono uppercase border border-border bg-muted/20">
                            {question.category}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="p-6 space-y-4">
                      <div>
                        <p className="text-xs font-mono uppercase tracking-widest text-primary mb-2">Sample Answer</p>
                        <p className="text-base font-sans leading-relaxed text-foreground">
                          {question.sample_answer}
                        </p>
                      </div>
                      {question.tips && question.tips.length > 0 && (
                        <div>
                          <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-2">
                            <Lightbulb className="w-4 h-4" /> Tips
                          </p>
                          <ul className="space-y-2">
                            {question.tips.map((tip, tipIdx) => (
                              <li key={tipIdx} className="text-sm text-muted-foreground border-l-2 border-primary/50 pl-4">
                                {tip}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Gap-Based Strategies */}
            {prep.gap_based_suggestions && prep.gap_based_suggestions.length > 0 && (
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <Target className="w-6 h-6 text-accent" />
                  <h2 className="text-3xl font-serif">Gap-Based Strategies</h2>
                </div>
                <div className="space-y-4">
                  {prep.gap_based_suggestions.map((suggestion, idx) => (
                    <div
                      key={idx}
                      className="border border-accent/30 bg-accent/5 p-6"
                      data-testid={`gap-strategy-${idx}`}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <p className="text-xs font-mono uppercase tracking-widest text-accent mb-2">Gap Identified</p>
                          <p className="text-lg font-serif text-accent">{suggestion.gap}</p>
                        </div>
                        <span className={`px-3 py-1 text-xs font-mono uppercase border ${DIFFICULTY_COLORS[suggestion.difficulty]}`}>
                          {suggestion.difficulty}
                        </span>
                      </div>
                      <div className="space-y-4">
                        <div>
                          <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2">Likely Question</p>
                          <p className="text-base font-sans">{suggestion.question}</p>
                        </div>
                        <div>
                          <p className="text-xs font-mono uppercase tracking-widest text-primary mb-2">Suggested Approach</p>
                          <p className="text-base font-sans leading-relaxed">{suggestion.suggested_answer_approach}</p>
                        </div>
                        <div>
                          <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4" /> Learning Resources
                          </p>
                          <ul className="space-y-1">
                            {suggestion.resources.map((resource, rIdx) => (
                              <li key={rIdx} className="text-sm text-muted-foreground ml-4">• {resource}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default InterviewPrepPage;
