import React, { useState, useEffect } from 'react';
import { Users, Briefcase, Calendar, TrendingUp, Loader2, Award, Search } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function RecruiterDashboardPage() {
  const { user, getAuthHeader } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [minScore, setMinScore] = useState(60);

  useEffect(() => {
    if (user) {
      loadDashboard();
      loadCandidates();
    }
  }, [user]);

  const loadDashboard = async () => {
    try {
      const response = await axios.get(`${API}/recruiter/dashboard`, {
        headers: getAuthHeader()
      });
      setDashboard(response.data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCandidates = async () => {
    try {
      const response = await axios.get(`${API}/recruiter/candidates?min_score=${minScore}`, {
        headers: getAuthHeader()
      });
      setCandidates(response.data.candidates || []);
    } catch (error) {
      console.error('Failed to load candidates:', error);
    }
  };

  const handleScoreFilterChange = (newMinScore) => {
    setMinScore(newMinScore);
    loadCandidates();
  };

  if (!user || user.role !== 'recruiter') {
    return (
      <div className="min-h-screen pt-24 pb-16 px-6 md:px-12 flex items-center justify-center">
        <div className="text-center max-w-2xl">
          <Users className="w-16 h-16 mx-auto mb-6 text-muted-foreground/50" strokeWidth={1.5} />
          <h2 className="text-3xl font-serif mb-4">Recruiter Access Only</h2>
          <p className="text-lg text-muted-foreground mb-8">
            This page is only accessible to users with recruiter role. Please contact admin to upgrade your account.
          </p>
          <a
            href="/settings"
            className="inline-block bg-primary text-primary-foreground px-8 py-4 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all"
          >
            Go to Settings
          </a>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen pt-24 pb-16 px-6 md:px-12 flex items-center justify-center">
        <Loader2 className="w-12 h-12 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-[1920px] mx-auto">
        <div className="mb-8">
          <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-2">Recruiter Portal</p>
          <h1 className="text-4xl md:text-6xl font-serif tracking-tight font-medium leading-[0.9]">
            Team Dashboard
          </h1>
        </div>

        {/* KPI Cards */}
        {dashboard && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="border border-border bg-card p-6" data-testid="total-candidates-card">
              <div className="flex items-center gap-3 mb-3">
                <Users className="w-6 h-6 text-primary" />
                <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">Total Candidates</p>
              </div>
              <p className="text-5xl font-mono font-medium text-primary">{dashboard.total_candidates}</p>
            </div>
            <div className="border border-border bg-card p-6">
              <div className="flex items-center gap-3 mb-3">
                <Briefcase className="w-6 h-6 text-purple-600" />
                <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">Active Positions</p>
              </div>
              <p className="text-5xl font-mono font-medium text-purple-600">{dashboard.active_positions}</p>
            </div>
            <div className="border border-border bg-card p-6">
              <div className="flex items-center gap-3 mb-3">
                <Calendar className="w-6 h-6 text-green-600" />
                <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">Interviews Scheduled</p>
              </div>
              <p className="text-5xl font-mono font-medium text-green-600">{dashboard.interviews_scheduled}</p>
            </div>
            <div className="border border-border bg-card p-6">
              <div className="flex items-center gap-3 mb-3">
                <TrendingUp className="w-6 h-6 text-accent" />
                <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">Avg Match Score</p>
              </div>
              <p className="text-5xl font-mono font-medium text-accent">{dashboard.avg_match_score}</p>
            </div>
          </div>
        )}

        {/* Top Candidates */}
        {dashboard && dashboard.top_candidates && dashboard.top_candidates.length > 0 && (
          <div className="border border-border bg-card p-8 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <Award className="w-6 h-6 text-accent" />
              <h2 className="text-2xl font-serif">Top Candidates</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dashboard.top_candidates.map((candidate, idx) => (
                <div key={idx} className="bg-muted/20 p-4 border border-border hover:shadow-lg transition-all">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-lg font-serif">{candidate.name}</p>
                      <p className="text-sm text-muted-foreground font-mono">{candidate.jd_title}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-mono font-medium text-primary">{candidate.score}</p>
                      <p className="text-xs text-muted-foreground">Match</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Candidates */}
        <div className="border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border/50 bg-muted/10">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-serif">All Candidates</h2>
              <div className="flex items-center gap-4">
                <label className="text-sm font-mono uppercase tracking-widest text-muted-foreground">Min Score:</label>
                <select
                  value={minScore}
                  onChange={(e) => handleScoreFilterChange(Number(e.target.value))}
                  className="border border-input bg-background px-4 py-2 text-sm font-mono"
                  data-testid="min-score-filter"
                >
                  <option value="0">All (0+)</option>
                  <option value="40">40+</option>
                  <option value="60">60+</option>
                  <option value="80">80+</option>
                </select>
              </div>
            </div>
          </div>
          <div className="p-6">
            {candidates.length === 0 ? (
              <div className="text-center py-12">
                <Search className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
                <p className="text-muted-foreground">No candidates found matching the criteria</p>
              </div>
            ) : (
              <div className="space-y-3">
                {candidates.map((candidate, idx) => (
                  <div
                    key={idx}
                    className="border border-border bg-muted/10 p-4 hover:bg-muted/20 transition-colors"
                    data-testid={`candidate-${idx}`}
                  >
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                      <div className="md:col-span-4">
                        <p className="text-lg font-serif mb-1">{candidate.name}</p>
                        <p className="text-sm text-muted-foreground font-mono">{candidate.jd_title}</p>
                      </div>
                      <div className="md:col-span-5">
                        <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2">Top Skills</p>
                        <div className="flex flex-wrap gap-2">
                          {candidate.skills.slice(0, 5).map((skill, sIdx) => (
                            <span key={sIdx} className="px-2 py-1 bg-primary/10 text-primary text-xs font-mono border border-primary/20">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="md:col-span-2 text-center">
                        <p className="text-3xl font-mono font-medium text-primary">{candidate.match_score}</p>
                        <p className="text-xs text-muted-foreground">Match Score</p>
                      </div>
                      <div className="md:col-span-1">
                        <button
                          onClick={() => window.open(`/cv/${candidate.cv_id}`, '_blank')}
                          className="w-full bg-primary text-primary-foreground px-4 py-2 text-xs font-mono uppercase hover:bg-primary/90"
                        >
                          View CV
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default RecruiterDashboardPage;
