import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { TrendingUp, Award, Target, Briefcase, Loader2, RefreshCw } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const COLORS = ['#1A4D3D', '#E85D30', '#6B9E8A', '#C4703A', '#2D7A5E', '#F0A070'];

const StatCard = ({ icon: Icon, label, value, sub, color = 'text-primary' }) => (
  <div className="border border-border bg-card p-6">
    <div className="flex items-start justify-between mb-4">
      <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground">{label}</p>
      <Icon className={`w-5 h-5 ${color}`} strokeWidth={1.5} />
    </div>
    <p className={`text-4xl font-mono font-medium ${color}`}>{value}</p>
    {sub && <p className="text-xs text-muted-foreground mt-2 font-sans">{sub}</p>}
  </div>
);

const SectionHeader = ({ title, sub }) => (
  <div className="mb-6">
    <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-1">{sub}</p>
    <h2 className="text-2xl font-serif">{title}</h2>
  </div>
);

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-card border border-border px-4 py-3 text-sm font-sans shadow-lg">
      <p className="font-mono text-xs uppercase mb-2 text-muted-foreground">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }} className="font-medium">
          {p.name}: {typeof p.value === 'number' && p.name.toLowerCase().includes('rate') ? `${p.value}%` : p.value}
        </p>
      ))}
    </div>
  );
};

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const auth = localStorage.getItem('user_email');
  const headers = auth ? { Authorization: `Bearer ${auth}` } : {};

  const load = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/analytics/dashboard`, { headers });
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className="min-h-screen pt-24 flex items-center justify-center">
      <Loader2 className="w-10 h-10 animate-spin text-primary" />
    </div>
  );

  if (!data || data.error) return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12 flex items-center justify-center">
      <div className="text-center">
        <Target className="w-16 h-16 mx-auto mb-6 text-muted-foreground/30" strokeWidth={1} />
        <h2 className="text-2xl font-serif mb-3">Sign In to View Analytics</h2>
        <p className="text-muted-foreground font-sans">Your personal analytics dashboard requires authentication.</p>
      </div>
    </div>
  );

  const statusColors = {
    applied: '#6B9E8A', screening: '#E85D30', interview: '#1A4D3D',
    offer: '#C4703A', accepted: '#2D7A5E', rejected: '#999', withdrawn: '#bbb'
  };

  const pieData = Object.entries(data.status_breakdown || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1), value, fill: statusColors[name] || '#999'
  }));

  const conversionRate = data.total_applications > 0
    ? ((data.total_interviews / data.total_applications) * 100).toFixed(1)
    : 0;

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-[1600px] mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-2">Personal Intelligence</p>
            <h1 className="text-5xl md:text-7xl font-serif font-medium leading-[0.9] tracking-tight">Analytics</h1>
          </div>
          <button onClick={load} className="flex items-center gap-2 px-4 py-2 border border-border hover:border-primary transition-colors text-sm font-mono uppercase">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <StatCard icon={Briefcase} label="Total Applications" value={data.total_applications} sub="All time" />
          <StatCard icon={Target} label="Interviews" value={data.total_interviews} sub={`${conversionRate}% conversion rate`} color="text-accent" />
          <StatCard icon={Award} label="Offers Received" value={data.total_offers} sub={data.total_interviews > 0 ? `${((data.total_offers / data.total_interviews) * 100).toFixed(0)}% of interviews` : '—'} color="text-emerald-600" />
          <StatCard icon={TrendingUp} label="Avg Match Score" value={data.avg_match_score > 0 ? `${data.avg_match_score}` : '—'} sub="Across all applications" />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

          {/* Score Distribution */}
          <div className="border border-border bg-card p-6">
            <SectionHeader title="Score Distribution" sub="ATS Match Analysis" />
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.score_distribution} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="range" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                <YAxis tick={{ fontSize: 11, fontFamily: 'monospace' }} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" fill="#1A4D3D" name="Applications" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Success Rate by Score */}
          <div className="border border-border bg-card p-6">
            <SectionHeader title="Interview Rate by Score" sub="Score Impact Analysis" />
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.success_by_score} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="range" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                <YAxis tick={{ fontSize: 11, fontFamily: 'monospace' }} unit="%" domain={[0, 100]} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="rate" fill="#E85D30" name="Interview Rate" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Applications Over Time */}
          <div className="border border-border bg-card p-6">
            <SectionHeader title="Application Activity" sub="Timeline" />
            {data.applications_over_time?.length > 1 ? (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={data.applications_over_time} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: 'monospace' }}
                    tickFormatter={v => v.slice(5)} />
                  <YAxis tick={{ fontSize: 11, fontFamily: 'monospace' }} allowDecimals={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="count" stroke="#1A4D3D" strokeWidth={2}
                    dot={{ r: 3, fill: '#1A4D3D' }} name="Applications" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[260px] flex items-center justify-center text-muted-foreground font-sans text-sm">
                Not enough data yet — add more applications to see the timeline.
              </div>
            )}
          </div>

          {/* Status Breakdown Pie */}
          <div className="border border-border bg-card p-6">
            <SectionHeader title="Pipeline Breakdown" sub="Status Distribution" />
            {pieData.length > 0 ? (
              <div className="flex items-center gap-6">
                <ResponsiveContainer width="55%" height={260}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                      dataKey="value" paddingAngle={2}>
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v, n) => [v, n]} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex-1 space-y-2">
                  {pieData.map((d, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: d.fill }} />
                        <span className="font-sans text-muted-foreground">{d.name}</span>
                      </div>
                      <span className="font-mono font-medium">{d.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-[260px] flex items-center justify-center text-muted-foreground font-sans text-sm">
                No applications yet.
              </div>
            )}
          </div>
        </div>

        {/* Top Companies Table */}
        {data.top_companies?.length > 0 && (
          <div className="border border-border bg-card p-6">
            <SectionHeader title="Top Companies Applied To" sub="Company Intelligence" />
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">Company</th>
                    <th className="text-right py-3 px-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">Applications</th>
                    <th className="text-right py-3 px-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">Avg Score</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">Score Bar</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_companies.map((c, i) => (
                    <tr key={i} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                      <td className="py-3 px-4 font-sans font-medium">{c.company}</td>
                      <td className="py-3 px-4 text-right font-mono">{c.count}</td>
                      <td className="py-3 px-4 text-right font-mono">
                        <span className={c.avg_score >= 70 ? 'text-emerald-600' : c.avg_score >= 50 ? 'text-accent' : 'text-muted-foreground'}>
                          {c.avg_score > 0 ? `${c.avg_score}` : '—'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="w-full bg-muted/30 h-1.5 rounded-full">
                          <div className="h-1.5 rounded-full bg-primary transition-all"
                            style={{ width: `${c.avg_score}%` }} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Industry Benchmarks note */}
        <div className="mt-6 border border-border/50 bg-muted/10 p-6 text-center">
          <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2">Industry Benchmarks</p>
          <p className="text-sm font-sans text-muted-foreground">
            Competitive benchmarks appear on the Dashboard after matching your CV against job descriptions.
          </p>
        </div>

      </div>
    </div>
  );
}
