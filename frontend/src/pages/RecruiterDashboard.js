import React, { useState, useEffect, useCallback } from 'react';
import {
  Users, Briefcase, Calendar, Star, Loader2, RefreshCw,
  MessageSquare, Send, Trash2, Download, X, Clock
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getHeaders = (email) => email ? { Authorization: `Bearer ${email}` } : {};

const ScoreBadge = ({ score }) => {
  const color = score >= 80 ? 'bg-emerald-100 text-emerald-700'
    : score >= 60 ? 'bg-primary/10 text-primary'
    : score >= 40 ? 'bg-orange-100 text-orange-700'
    : 'bg-muted text-muted-foreground';
  return (
    <span className={`inline-block px-2.5 py-0.5 text-xs font-mono font-bold ${color}`}>
      {score != null ? score.toFixed(0) : '—'}
    </span>
  );
};

const StatusPill = ({ status }) => {
  const map = {
    applied: 'bg-blue-50 text-blue-700', screening: 'bg-yellow-50 text-yellow-700',
    interview: 'bg-purple-50 text-purple-700', offer: 'bg-green-50 text-green-700',
    accepted: 'bg-emerald-50 text-emerald-700', rejected: 'bg-red-50 text-red-700',
    withdrawn: 'bg-gray-50 text-gray-500', scheduled: 'bg-indigo-50 text-indigo-700',
    completed: 'bg-emerald-50 text-emerald-700', cancelled: 'bg-red-50 text-red-500'
  };
  return (
    <span className={`px-2 py-0.5 text-xs font-mono uppercase rounded-sm ${map[status] || 'bg-muted text-muted-foreground'}`}>
      {status}
    </span>
  );
};

// ── Interview Scheduler Modal ─────────────────────────────────────────────────
function SchedulerModal({ candidate, onClose, onScheduled, userEmail }) {
  const [form, setForm] = useState({
    scheduled_at: '', duration_minutes: 60,
    location: '', meeting_link: '', notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  const submit = async () => {
    if (!form.scheduled_at) { setErr('Please select a date and time.'); return; }
    setLoading(true); setErr('');
    try {
      await axios.post(`${API}/interviews`, {
        application_id: candidate.application_id || '',
        candidate_email: candidate.email || `${candidate.cv_id}@candidate.local`,
        candidate_name: candidate.name,
        position: candidate.jd_title || 'Position',
        company: 'Your Company',
        ...form,
        duration_minutes: Number(form.duration_minutes)
      }, { headers: getHeaders(userEmail) });
      onScheduled();
      onClose();
    } catch (e) {
      setErr(e.response?.data?.detail || 'Failed to schedule interview.');
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border w-full max-w-lg">
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-serif">Schedule Interview</h2>
          <button onClick={onClose}><X className="w-5 h-5" /></button>
        </div>
        <div className="p-6 space-y-4">
          <div className="bg-muted/20 p-3 border border-border text-sm font-sans">
            <strong>{candidate.name}</strong> — {candidate.jd_title || 'Candidate'}
          </div>
          <div>
            <label className="block text-xs font-mono uppercase tracking-widest mb-1.5 text-muted-foreground">Date & Time *</label>
            <input type="datetime-local" value={form.scheduled_at}
              onChange={e => setForm(f => ({ ...f, scheduled_at: e.target.value }))}
              className="w-full border border-input bg-background px-3 py-2 text-sm font-sans focus:border-primary outline-none" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono uppercase tracking-widest mb-1.5 text-muted-foreground">Duration (min)</label>
              <select value={form.duration_minutes}
                onChange={e => setForm(f => ({ ...f, duration_minutes: e.target.value }))}
                className="w-full border border-input bg-background px-3 py-2 text-sm font-sans focus:border-primary outline-none">
                {[30, 45, 60, 90, 120].map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-mono uppercase tracking-widest mb-1.5 text-muted-foreground">Location</label>
              <input type="text" placeholder="Office / Virtual" value={form.location}
                onChange={e => setForm(f => ({ ...f, location: e.target.value }))}
                className="w-full border border-input bg-background px-3 py-2 text-sm font-sans focus:border-primary outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-mono uppercase tracking-widest mb-1.5 text-muted-foreground">Meeting Link</label>
            <input type="url" placeholder="https://meet.google.com/..." value={form.meeting_link}
              onChange={e => setForm(f => ({ ...f, meeting_link: e.target.value }))}
              className="w-full border border-input bg-background px-3 py-2 text-sm font-sans focus:border-primary outline-none" />
          </div>
          <div>
            <label className="block text-xs font-mono uppercase tracking-widest mb-1.5 text-muted-foreground">Notes for Candidate</label>
            <textarea rows={2} placeholder="Additional instructions..."
              value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              className="w-full border border-input bg-background px-3 py-2 text-sm font-sans focus:border-primary outline-none resize-none" />
          </div>
          {err && <p className="text-red-500 text-sm font-sans">{err}</p>}
        </div>
        <div className="flex gap-3 p-6 border-t border-border">
          <button onClick={onClose}
            className="flex-1 border border-border px-4 py-3 text-sm font-mono uppercase hover:border-primary transition-colors">
            Cancel
          </button>
          <button onClick={submit} disabled={loading}
            className="flex-1 bg-primary text-primary-foreground px-4 py-3 text-sm font-mono uppercase hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calendar className="w-4 h-4" />}
            Schedule & Notify
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Comments Panel ────────────────────────────────────────────────────────────
function CommentsPanel({ candidateId, candidateName, userEmail, userName }) {
  const [comments, setComments] = useState([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);

  const loadComments = useCallback(async () => {
    if (!candidateId) return;
    try {
      const res = await axios.get(`${API}/applications/${candidateId}/comments`, { headers: getHeaders(userEmail) });
      setComments(res.data);
    } catch { setComments([]); }
  }, [candidateId, userEmail]);

  useEffect(() => { loadComments(); }, [loadComments]);

  const post = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      await axios.post(
        `${API}/applications/${candidateId}/comments`,
        { text: text.trim(), user_name: userName || userEmail?.split('@')[0] || 'Recruiter' },
        { headers: getHeaders(userEmail) }
      );
      setText('');
      loadComments();
    } catch { } finally { setLoading(false); }
  };

  const del = async (id) => {
    await axios.delete(`${API}/applications/${candidateId}/comments/${id}`, { headers: getHeaders(userEmail) });
    loadComments();
  };

  return (
    <div className="border-t border-border mt-4 pt-4">
      <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-1.5">
        <MessageSquare className="w-3.5 h-3.5" /> Team Notes — {candidateName}
      </p>
      <div className="space-y-2 mb-3 max-h-40 overflow-y-auto">
        {comments.length === 0 && (
          <p className="text-xs text-muted-foreground font-sans italic">No notes yet. Add the first one.</p>
        )}
        {comments.map(c => (
          <div key={c.id} className="bg-muted/20 p-2.5 text-xs font-sans flex items-start gap-2">
            <div className="flex-1">
              <span className="font-semibold text-primary">{c.user_name}</span>
              <span className="text-muted-foreground ml-2 text-[10px]">{new Date(c.created_at).toLocaleDateString()}</span>
              <p className="mt-1 text-foreground/80">{c.text}</p>
            </div>
            {c.user_email === userEmail && (
              <button onClick={() => del(c.id)}
                className="text-muted-foreground hover:text-red-500 transition-colors mt-0.5 flex-shrink-0">
                <Trash2 className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input value={text} onChange={e => setText(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && post()}
          placeholder="Add a note (Enter to send)..."
          className="flex-1 border border-input bg-background px-3 py-1.5 text-xs font-sans focus:border-primary outline-none" />
        <button onClick={post} disabled={loading || !text.trim()}
          className="bg-primary text-primary-foreground px-3 py-1.5 disabled:opacity-50 hover:bg-primary/90 transition-all">
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  );
}

// ── Candidate Card ────────────────────────────────────────────────────────────
function CandidateCard({ candidate, userEmail, userName, onSchedule }) {
  const [expanded, setExpanded] = useState(false);
  const [status, setStatus] = useState(candidate.status || 'applied');
  const [updating, setUpdating] = useState(false);

  const updateStatus = async (newStatus) => {
    setUpdating(true);
    try {
      await axios.patch(
        `${API}/applications/${candidate.application_id}/status`,
        { status: newStatus },
        { headers: getHeaders(userEmail) }
      );
      setStatus(newStatus);
    } catch { } finally { setUpdating(false); }
  };

  const commentKey = candidate.application_id || candidate.cv_id;

  return (
    <div className="border border-border bg-card hover:shadow-md transition-all duration-200">
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h3 className="font-serif text-lg leading-tight">{candidate.name}</h3>
              <ScoreBadge score={candidate.match_score} />
              <StatusPill status={status} />
            </div>
            <p className="text-xs text-muted-foreground font-mono truncate">{candidate.jd_title}</p>
            {candidate.skills?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {candidate.skills.slice(0, 6).map(s => (
                  <span key={s} className="px-1.5 py-0.5 bg-muted/40 text-[10px] font-mono text-muted-foreground">{s}</span>
                ))}
              </div>
            )}
          </div>
          <div className="flex gap-1.5 flex-shrink-0">
            <button onClick={() => onSchedule(candidate)} title="Schedule Interview"
              className="p-2 border border-border hover:border-primary hover:bg-primary/5 transition-colors">
              <Calendar className="w-4 h-4" />
            </button>
            <button onClick={() => setExpanded(e => !e)} title="Team Notes"
              className={`p-2 border transition-colors ${expanded ? 'border-primary bg-primary/5' : 'border-border hover:border-primary hover:bg-primary/5'}`}>
              <MessageSquare className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Pipeline stage selector */}
        <div className="flex gap-1 mt-4 flex-wrap">
          {['applied', 'screening', 'interview', 'offer', 'accepted', 'rejected'].map(s => (
            <button key={s} onClick={() => updateStatus(s)} disabled={updating}
              className={`px-2 py-0.5 text-[10px] font-mono uppercase transition-all disabled:opacity-50 ${
                status === s
                  ? 'bg-primary text-primary-foreground'
                  : 'border border-border hover:border-primary text-muted-foreground hover:text-foreground'
              }`}>
              {s}
            </button>
          ))}
        </div>
      </div>

      {expanded && (
        <div className="px-5 pb-5">
          <CommentsPanel
            candidateId={commentKey}
            candidateName={candidate.name}
            userEmail={userEmail}
            userName={userName}
          />
        </div>
      )}
    </div>
  );
}

// ── Interviews Tab ────────────────────────────────────────────────────────────
function InterviewsPanel({ userEmail }) {
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/interviews`, { headers: getHeaders(userEmail) })
      .then(r => setInterviews(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [userEmail]);

  const cancel = async (id) => {
    await axios.patch(`${API}/interviews/${id}`, { status: 'cancelled' }, { headers: getHeaders(userEmail) });
    setInterviews(prev => prev.map(i => i.id === id ? { ...i, status: 'cancelled' } : i));
  };

  if (loading) return (
    <div className="flex justify-center py-16"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
  );

  return (
    <div className="space-y-3">
      {interviews.length === 0 && (
        <div className="text-center py-16 text-muted-foreground font-sans text-sm">
          No interviews scheduled yet. Use the pipeline tab to schedule interviews.
        </div>
      )}
      {interviews.map(iv => (
        <div key={iv.id}
          className={`border p-5 transition-all ${iv.status === 'cancelled' ? 'border-border/30 opacity-40' : 'border-border hover:shadow-sm'}`}>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <h3 className="font-serif text-lg">{iv.position}</h3>
                <span className="text-muted-foreground font-sans text-sm">at {iv.company}</span>
                <StatusPill status={iv.status} />
              </div>
              <p className="text-sm font-sans text-muted-foreground">
                {iv.candidate_name} · {iv.candidate_email}
              </p>
              <div className="flex flex-wrap items-center gap-4 mt-3 text-xs font-sans text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5" />
                  {new Date(iv.scheduled_at).toLocaleString()}
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" /> {iv.duration_minutes} min
                </span>
                {iv.location && <span>📍 {iv.location}</span>}
                {iv.meeting_link && (
                  <a href={iv.meeting_link} target="_blank" rel="noreferrer"
                    className="text-primary underline hover:no-underline">
                    Join Meeting
                  </a>
                )}
              </div>
              {iv.notes && (
                <p className="text-xs text-muted-foreground font-sans mt-2 italic">📝 {iv.notes}</p>
              )}
            </div>
            {iv.status === 'scheduled' && (
              <div className="flex items-center gap-2 flex-shrink-0">
                <a href={`${API}/interviews/${iv.id}/calendar`} target="_blank" rel="noreferrer"
                  className="flex items-center gap-1.5 px-3 py-2 border border-border hover:border-primary transition-colors text-xs font-mono uppercase">
                  <Download className="w-3.5 h-3.5" /> .ics
                </a>
                <button onClick={() => cancel(iv.id)}
                  className="flex items-center gap-1.5 px-3 py-2 border border-border hover:border-red-400 hover:text-red-500 transition-colors text-xs font-mono uppercase text-muted-foreground">
                  <X className="w-3.5 h-3.5" /> Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function RecruiterDashboardPage() {
  const { user } = useAuth();
  const [kpis, setKpis] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [minScore, setMinScore] = useState(0);
  const [tab, setTab] = useState('pipeline');
  const [schedulerTarget, setSchedulerTarget] = useState(null);
  const [extraInterviews, setExtraInterviews] = useState(0);

  const userEmail = user?.email || localStorage.getItem('user_email');
  const userName = user?.name || userEmail?.split('@')[0]?.replace(/[._]/g, ' ') || 'Recruiter';

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [kpiRes, candRes] = await Promise.allSettled([
        axios.get(`${API}/recruiter/dashboard`, { headers: getHeaders(userEmail) }),
        axios.get(`${API}/recruiter/candidates?min_score=${minScore}`, { headers: getHeaders(userEmail) })
      ]);
      if (kpiRes.status === 'fulfilled') setKpis(kpiRes.value.data);
      if (candRes.status === 'fulfilled') setCandidates(candRes.value.data.candidates || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [userEmail, minScore]);

  useEffect(() => { load(); }, [load]);

  if (!userEmail) {
    return (
      <div className="min-h-screen pt-24 flex items-center justify-center">
        <div className="text-center">
          <Users className="w-16 h-16 mx-auto mb-6 text-muted-foreground/30" strokeWidth={1} />
          <h2 className="text-2xl font-serif mb-3">Recruiter Access Required</h2>
          <p className="text-sm text-muted-foreground font-sans">Sign in with a recruiter account to continue.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-[1600px] mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-2">Recruiter Console</p>
            <h1 className="text-5xl md:text-7xl font-serif font-medium leading-[0.9] tracking-tight">Talent Pipeline</h1>
          </div>
          <button onClick={load}
            className="flex items-center gap-2 px-4 py-2 border border-border hover:border-primary transition-colors text-sm font-mono uppercase">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>

        {/* KPIs */}
        {kpis && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            {[
              { icon: Users, label: 'Total Candidates', value: kpis.total_candidates },
              { icon: Briefcase, label: 'Active Positions', value: kpis.active_positions },
              { icon: Calendar, label: 'Interviews Scheduled', value: kpis.interviews_scheduled + extraInterviews },
              { icon: Star, label: 'Avg Match Score', value: kpis.avg_match_score }
            ].map(({ icon: Icon, label, value }) => (
              <div key={label} className="border border-border bg-card p-6">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground">{label}</p>
                  <Icon className="w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                </div>
                <p className="text-4xl font-mono font-medium text-primary">{value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-border mb-8">
          {[['pipeline', 'Candidate Pipeline'], ['interviews', 'Interview Schedule']].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-6 py-3 text-sm font-mono uppercase tracking-widest border-b-2 -mb-px transition-all ${
                tab === id ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}>
              {label}
            </button>
          ))}
        </div>

        {/* Pipeline Tab */}
        {tab === 'pipeline' && (
          <>
            <div className="flex items-center gap-3 mb-6 flex-wrap">
              <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">Filter by score:</p>
              {[0, 40, 60, 80].map(s => (
                <button key={s} onClick={() => setMinScore(s)}
                  className={`px-4 py-2 text-xs font-mono uppercase transition-all ${
                    minScore === s
                      ? 'bg-primary text-primary-foreground'
                      : 'border border-border hover:border-primary text-muted-foreground'
                  }`}>
                  {s === 0 ? 'All' : `${s}+`}
                </button>
              ))}
              <span className="text-xs text-muted-foreground font-sans ml-auto">
                {candidates.length} candidate{candidates.length !== 1 ? 's' : ''}
              </span>
            </div>

            {loading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="w-10 h-10 animate-spin text-primary" />
              </div>
            ) : candidates.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground font-sans">
                <Users className="w-12 h-12 mx-auto mb-4 opacity-30" strokeWidth={1} />
                No candidates with score ≥ {minScore}. Try a lower threshold.
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {candidates.map(c => (
                  <CandidateCard
                    key={`${c.cv_id}-${c.report_id}`}
                    candidate={c}
                    userEmail={userEmail}
                    userName={userName}
                    onSchedule={setSchedulerTarget}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {/* Interviews Tab */}
        {tab === 'interviews' && <InterviewsPanel userEmail={userEmail} />}
      </div>

      {/* Scheduler Modal */}
      {schedulerTarget && (
        <SchedulerModal
          candidate={schedulerTarget}
          userEmail={userEmail}
          onClose={() => setSchedulerTarget(null)}
          onScheduled={() => {
            setExtraInterviews(n => n + 1);
            setTab('interviews');
          }}
        />
      )}
    </div>
  );
}
