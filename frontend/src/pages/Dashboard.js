import React, { useState, useEffect } from 'react';
import { Target, Download, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function DashboardPage() {
  const [cvs, setCvs] = useState([]);
  const [jds, setJds] = useState([]);
  const [selectedCv, setSelectedCv] = useState(null);
  const [selectedJd, setSelectedJd] = useState(null);
  const [matching, setMatching] = useState(false);
  const [matchReport, setMatchReport] = useState(null);
  const [rewriting, setRewriting] = useState(false);
  const [tailoredCv, setTailoredCv] = useState(null);
  const [provider, setProvider] = useState('deterministic');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [cvsRes, jdsRes] = await Promise.all([
        axios.get(`${API}/cvs`),
        axios.get(`${API}/jds`)
      ]);
      setCvs(cvsRes.data.cvs);
      setJds(jdsRes.data.jds);
      
      if (cvsRes.data.cvs.length > 0) setSelectedCv(cvsRes.data.cvs[0].id);
      if (jdsRes.data.jds.length > 0) setSelectedJd(jdsRes.data.jds[0].id);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const handleMatch = async () => {
    if (!selectedCv || !selectedJd) {
      alert('Please select both CV and JD');
      return;
    }

    setMatching(true);
    try {
      const response = await axios.post(`${API}/match`, {
        cv_id: selectedCv,
        jd_id: selectedJd
      });
      setMatchReport(response.data.report);
      setTailoredCv(null);
    } catch (error) {
      console.error('Matching failed:', error);
      alert('Matching failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setMatching(false);
    }
  };

  const handleRewrite = async () => {
    if (!matchReport) return;

    setRewriting(true);
    try {
      const response = await axios.post(`${API}/rewrite`, {
        match_report_id: matchReport.id,
        provider: provider
      });
      
      const tailoredRes = await axios.get(`${API}/tailored/${response.data.tailored_cv_id}`);
      setTailoredCv(tailoredRes.data);
      alert('Tailored CV generated successfully!');
    } catch (error) {
      console.error('Rewrite failed:', error);
      alert('Rewrite failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setRewriting(false);
    }
  };

  const handleDownload = async () => {
    if (!tailoredCv) return;
    
    try {
      const response = await axios.get(`${API}/tailored/${tailoredCv.id}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `tailored_cv_${Date.now()}.txt`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed');
    }
  };

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-[1920px] mx-auto">
        <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-4">Analysis</p>
        <h1 className="text-4xl md:text-6xl font-serif tracking-tight font-medium leading-[0.9] mb-12">
          Match Dashboard
        </h1>

        {/* Bento Grid Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 md:gap-6">
          {/* Selection Panel */}
          <div 
            className="md:col-span-4 lg:col-span-1 border border-border bg-card overflow-hidden"
            data-testid="selection-panel"
          >
            <div className="p-6 border-b border-border/50 bg-muted/10">
              <h2 className="text-xl font-serif">Select Documents</h2>
            </div>
            <div className="p-6 space-y-6">
              <div>
                <label className="block text-xs font-mono uppercase tracking-widest mb-2 text-muted-foreground">CV</label>
                <select
                  value={selectedCv || ''}
                  onChange={(e) => setSelectedCv(e.target.value)}
                  className="w-full border border-input bg-background p-3 text-sm font-sans focus:border-primary focus:ring-0 transition-colors"
                  data-testid="cv-select"
                >
                  {cvs.map(cv => (
                    <option key={cv.id} value={cv.id}>{cv.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-widest mb-2 text-muted-foreground">Job Description</label>
                <select
                  value={selectedJd || ''}
                  onChange={(e) => setSelectedJd(e.target.value)}
                  className="w-full border border-input bg-background p-3 text-sm font-sans focus:border-primary focus:ring-0 transition-colors"
                  data-testid="jd-select"
                >
                  {jds.map(jd => (
                    <option key={jd.id} value={jd.id}>{jd.title}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleMatch}
                disabled={matching || !selectedCv || !selectedJd}
                className="w-full bg-primary text-primary-foreground px-6 py-4 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all duration-300 disabled:opacity-50"
                data-testid="run-match-button"
              >
                {matching ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Target className="w-4 h-4" />
                    Run Match
                  </span>
                )}
              </button>
            </div>
          </div>

          {/* Score Card */}
          {matchReport && (
            <div 
              className="md:col-span-2 lg:col-span-1 border border-border bg-card overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              data-testid="score-card"
            >
              <div className="p-6 border-b border-border/50 bg-muted/10">
                <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">ATS Score</p>
              </div>
              <div className="p-8 text-center">
                <div className="text-7xl font-mono font-medium text-primary mb-4" data-testid="total-score">
                  {matchReport.total_score}
                </div>
                <p className="text-sm font-mono uppercase tracking-widest text-muted-foreground">Out of 100</p>
                <div className="mt-6 score-meter">
                  <div 
                    className="score-meter-fill" 
                    style={{ width: `${matchReport.total_score}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Category Breakdown */}
          {matchReport && (
            <div 
              className="md:col-span-2 lg:col-span-2 border border-border bg-card overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              data-testid="category-breakdown"
            >
              <div className="p-6 border-b border-border/50 bg-muted/10">
                <h2 className="text-xl font-serif">Category Breakdown</h2>
              </div>
              <div className="p-6 space-y-4">
                {Object.entries(matchReport.category_scores).map(([category, score]) => (
                  <div key={category}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-mono uppercase tracking-widest">{category}</span>
                      <span className="text-lg font-mono font-medium">{score.toFixed(1)}</span>
                    </div>
                    <div className="score-meter">
                      <div 
                        className="score-meter-fill" 
                        style={{ width: `${(score / (category === 'skills' ? 35 : category === 'experience' ? 30 : category === 'tenure' ? 15 : 10)) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gaps Analysis */}
          {matchReport && (matchReport.hard_gaps.length > 0 || matchReport.soft_gaps.length > 0) && (
            <div 
              className="md:col-span-4 lg:col-span-2 border border-border bg-card overflow-hidden"
              data-testid="gaps-analysis"
            >
              <div className="p-6 border-b border-border/50 bg-muted/10">
                <h2 className="text-xl font-serif">Gap Analysis</h2>
              </div>
              <div className="p-6 space-y-6 max-h-96 overflow-y-auto">
                {matchReport.hard_gaps.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <AlertCircle className="w-4 h-4 text-accent" />
                      <h3 className="text-sm font-mono uppercase tracking-widest text-accent">Hard Gaps ({matchReport.hard_gaps.length})</h3>
                    </div>
                    <ul className="space-y-2">
                      {matchReport.hard_gaps.slice(0, 5).map((gap, idx) => (
                        <li key={idx} className="text-sm font-sans text-muted-foreground border-l-2 border-accent pl-4">
                          {gap}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {matchReport.soft_gaps.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <AlertCircle className="w-4 h-4 text-primary" />
                      <h3 className="text-sm font-mono uppercase tracking-widest text-primary">Soft Gaps ({matchReport.soft_gaps.length})</h3>
                    </div>
                    <ul className="space-y-2">
                      {matchReport.soft_gaps.slice(0, 5).map((gap, idx) => (
                        <li key={idx} className="text-sm font-sans text-muted-foreground border-l-2 border-primary/50 pl-4">
                          {gap}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Rewrite Panel */}
          {matchReport && (
            <div 
              className="md:col-span-4 lg:col-span-2 border border-border bg-card overflow-hidden"
              data-testid="rewrite-panel"
            >
              <div className="p-6 border-b border-border/50 bg-muted/10">
                <h2 className="text-xl font-serif">Generate Tailored CV</h2>
              </div>
              <div className="p-6 space-y-6">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-widest mb-2 text-muted-foreground">Provider</label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="w-full border border-input bg-background p-3 text-sm font-sans focus:border-primary focus:ring-0 transition-colors"
                    data-testid="provider-select"
                  >
                    <option value="deterministic">Deterministic (No LLM)</option>
                    <option value="openai">OpenAI GPT</option>
                    <option value="anthropic">Anthropic Claude</option>
                    <option value="gemini">Google Gemini</option>
                    <option value="huggingface">HuggingFace</option>
                  </select>
                </div>
                <button
                  onClick={handleRewrite}
                  disabled={rewriting}
                  className="w-full bg-accent text-accent-foreground px-6 py-4 text-sm font-mono tracking-widest uppercase hover:bg-accent/90 transition-all duration-300 disabled:opacity-50"
                  data-testid="generate-cv-button"
                >
                  {rewriting ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Generating...
                    </span>
                  ) : (
                    'Generate Tailored CV'
                  )}
                </button>

                {tailoredCv && (
                  <div className="bg-muted/20 p-4 border border-border" data-testid="tailored-cv-info">
                    <div className="flex items-center gap-2 mb-3">
                      <CheckCircle2 className="w-5 h-5 text-primary" />
                      <p className="font-serif text-lg">Tailored CV Ready</p>
                    </div>
                    <p className="text-sm text-muted-foreground font-mono mb-4">
                      {tailoredCv.modifications.length} modifications made
                    </p>
                    <button
                      onClick={handleDownload}
                      className="w-full bg-primary text-primary-foreground px-6 py-3 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all duration-300 flex items-center justify-center gap-2"
                      data-testid="download-cv-button"
                    >
                      <Download className="w-4 h-4" />
                      Download CV
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {!matchReport && (
          <div className="text-center py-24">
            <Target className="w-16 h-16 mx-auto mb-6 text-muted-foreground/50" strokeWidth={1.5} />
            <p className="text-xl font-serif text-muted-foreground">Select documents and run match to begin analysis</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default DashboardPage;
