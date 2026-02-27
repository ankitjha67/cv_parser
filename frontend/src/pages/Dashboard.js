import React, { useState, useEffect } from 'react';
import { Target, Download, Loader2, AlertCircle, CheckCircle2, Zap, RefreshCw } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function DashboardPage() {
  const [cvs, setCvs] = useState([]);
  const [jds, setJds] = useState([]);
  const [selectedCv, setSelectedCv] = useState(null);
  const [loading, setLoading] = useState(true);
  const [matchReports, setMatchReports] = useState({});
  const [tailoredCvs, setTailoredCvs] = useState({});
  const [processingJds, setProcessingJds] = useState(new Set());
  const [provider, setProvider] = useState('deterministic');
  const [batchProcessing, setBatchProcessing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cvsRes, jdsRes] = await Promise.all([
        axios.get(`${API}/cvs`),
        axios.get(`${API}/jds`)
      ]);
      
      setCvs(cvsRes.data.cvs || []);
      setJds(jdsRes.data.jds || []);
      
      // Get current CV from localStorage or use first
      const currentCvId = localStorage.getItem('current_cv_id');
      if (currentCvId && cvsRes.data.cvs.find(cv => cv.id === currentCvId)) {
        setSelectedCv(currentCvId);
      } else if (cvsRes.data.cvs.length > 0) {
        setSelectedCv(cvsRes.data.cvs[0].id);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      alert('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMatchSingle = async (jdId) => {
    if (!selectedCv || !jdId) return;

    setProcessingJds(prev => new Set(prev).add(jdId));
    try {
      const response = await axios.post(`${API}/match`, {
        cv_id: selectedCv,
        jd_id: jdId
      });
      
      setMatchReports(prev => ({
        ...prev,
        [jdId]: response.data.report
      }));
    } catch (error) {
      console.error('Matching failed:', error);
      alert('Matching failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setProcessingJds(prev => {
        const newSet = new Set(prev);
        newSet.delete(jdId);
        return newSet;
      });
    }
  };

  const handleMatchAll = async () => {
    if (!selectedCv || jds.length === 0) {
      alert('Please select a CV and ensure JDs are loaded');
      return;
    }

    setBatchProcessing(true);
    const newReports = {};
    
    try {
      for (const jd of jds) {
        try {
          const response = await axios.post(`${API}/match`, {
            cv_id: selectedCv,
            jd_id: jd.id
          });
          newReports[jd.id] = response.data.report;
        } catch (error) {
          console.error(`Failed to match JD ${jd.id}:`, error);
        }
      }
      
      setMatchReports(prev => ({ ...prev, ...newReports }));
      alert(`Matched against ${Object.keys(newReports).length} JD(s) successfully!`);
    } catch (error) {
      console.error('Batch matching failed:', error);
    } finally {
      setBatchProcessing(false);
    }
  };

  const handleRewrite = async (jdId) => {
    const report = matchReports[jdId];
    if (!report) return;

    setProcessingJds(prev => new Set(prev).add(`rewrite_${jdId}`));
    try {
      const response = await axios.post(`${API}/rewrite`, {
        match_report_id: report.id,
        provider: provider
      });
      
      const tailoredRes = await axios.get(`${API}/tailored/${response.data.tailored_cv_id}`);
      setTailoredCvs(prev => ({
        ...prev,
        [jdId]: tailoredRes.data
      }));
    } catch (error) {
      console.error('Rewrite failed:', error);
      alert('Rewrite failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setProcessingJds(prev => {
        const newSet = new Set(prev);
        newSet.delete(`rewrite_${jdId}`);
        return newSet;
      });
    }
  };

  const handleRewriteAll = async () => {
    if (Object.keys(matchReports).length === 0) {
      alert('Please run matching first');
      return;
    }

    setBatchProcessing(true);
    const newTailored = {};
    
    try {
      for (const [jdId, report] of Object.entries(matchReports)) {
        try {
          const response = await axios.post(`${API}/rewrite`, {
            match_report_id: report.id,
            provider: provider
          });
          
          const tailoredRes = await axios.get(`${API}/tailored/${response.data.tailored_cv_id}`);
          newTailored[jdId] = tailoredRes.data;
        } catch (error) {
          console.error(`Failed to rewrite for JD ${jdId}:`, error);
        }
      }
      
      setTailoredCvs(prev => ({ ...prev, ...newTailored }));
      alert(`Generated ${Object.keys(newTailored).length} tailored CV(s)!`);
    } catch (error) {
      console.error('Batch rewrite failed:', error);
    } finally {
      setBatchProcessing(false);
    }
  };

  const handleDownload = async (jdId) => {
    const tailored = tailoredCvs[jdId];
    if (!tailored) return;
    
    try {
      const response = await axios.get(`${API}/tailored/${tailored.id}/download`, {
        responseType: 'blob'
      });
      
      const jd = jds.find(j => j.id === jdId);
      const filename = `tailored_cv_${jd?.title.replace(/\s+/g, '_') || jdId}.txt`;
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed');
    }
  };

  const handleDownloadAll = async () => {
    if (Object.keys(tailoredCvs).length === 0) {
      alert('No tailored CVs available');
      return;
    }

    for (const jdId of Object.keys(tailoredCvs)) {
      await handleDownload(jdId);
      await new Promise(resolve => setTimeout(resolve, 500)); // Delay between downloads
    }
  };

  const selectedCvData = cvs.find(cv => cv.id === selectedCv);
  const sortedJds = [...jds].sort((a, b) => {
    const scoreA = matchReports[a.id]?.total_score || 0;
    const scoreB = matchReports[b.id]?.total_score || 0;
    return scoreB - scoreA;
  });

  if (loading) {
    return (
      <div className="min-h-screen pt-24 pb-16 px-6 md:px-12 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-primary" />
          <p className="text-lg font-serif">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (cvs.length === 0 || jds.length === 0) {
    return (
      <div className="min-h-screen pt-24 pb-16 px-6 md:px-12 flex items-center justify-center">
        <div className="text-center max-w-2xl">
          <Target className="w-16 h-16 mx-auto mb-6 text-muted-foreground/50" strokeWidth={1.5} />
          <h2 className="text-3xl font-serif mb-4">No Documents Found</h2>
          <p className="text-lg text-muted-foreground mb-8">
            Please upload a CV and add job descriptions to begin analysis.
          </p>
          <a
            href="/upload"
            className="inline-block bg-primary text-primary-foreground px-8 py-4 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all"
          >
            Go to Upload
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-[1920px] mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-2">Analysis Dashboard</p>
            <h1 className="text-4xl md:text-6xl font-serif tracking-tight font-medium leading-[0.9]">
              Multi-JD Matching
            </h1>
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 border border-border hover:border-primary transition-colors text-sm font-mono uppercase"
            data-testid="refresh-button"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Control Panel */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-8">
          {/* CV Selection */}
          <div className="md:col-span-4 border border-border bg-card p-6">
            <label className="block text-xs font-mono uppercase tracking-widest mb-3 text-muted-foreground">Selected CV</label>
            <select
              value={selectedCv || ''}
              onChange={(e) => {
                setSelectedCv(e.target.value);
                setMatchReports({});
                setTailoredCvs({});
              }}
              className="w-full border border-input bg-background p-3 text-sm font-sans focus:border-primary focus:ring-0 transition-colors mb-4"
              data-testid="cv-select"
            >
              {cvs.map(cv => (
                <option key={cv.id} value={cv.id}>{cv.name} ({cv.skills_count} skills)</option>
              ))}
            </select>
            {selectedCvData && (
              <div className="text-xs font-mono text-muted-foreground space-y-1">
                <p>{selectedCvData.experiences_count} experiences</p>
                <p>{selectedCvData.skills_count} skills</p>
              </div>
            )}
          </div>

          {/* Provider Selection */}
          <div className="md:col-span-4 border border-border bg-card p-6">
            <label className="block text-xs font-mono uppercase tracking-widest mb-3 text-muted-foreground">Rewrite Provider</label>
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
            <p className="text-xs text-muted-foreground font-sans mt-3 leading-relaxed">
              {provider === 'deterministic' ? 'Pure Python, 100% offline' : 'Uses Emergent LLM key'}
            </p>
          </div>

          {/* Batch Actions */}
          <div className="md:col-span-4 border border-border bg-card p-6 flex flex-col justify-between">
            <label className="block text-xs font-mono uppercase tracking-widest mb-3 text-muted-foreground">Batch Actions</label>
            <div className="space-y-3">
              <button
                onClick={handleMatchAll}
                disabled={batchProcessing || !selectedCv}
                className="w-full bg-primary text-primary-foreground px-4 py-3 text-xs font-mono tracking-widest uppercase hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                data-testid="match-all-button"
              >
                {batchProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Match All JDs
                  </>
                )}
              </button>
              <button
                onClick={handleRewriteAll}
                disabled={batchProcessing || Object.keys(matchReports).length === 0}
                className="w-full bg-accent text-accent-foreground px-4 py-3 text-xs font-mono tracking-widest uppercase hover:bg-accent/90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                data-testid="rewrite-all-button"
              >
                Generate All CVs
              </button>
            </div>
          </div>
        </div>

        {/* Results Grid */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-serif">Results ({jds.length} JD{jds.length > 1 ? 's' : ''})</h2>
            {Object.keys(tailoredCvs).length > 0 && (
              <button
                onClick={handleDownloadAll}
                className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground text-sm font-mono uppercase tracking-widest hover:bg-primary/90 transition-all"
                data-testid="download-all-button"
              >
                <Download className="w-4 h-4" />
                Download All ({Object.keys(tailoredCvs).length})
              </button>
            )}
          </div>

          {sortedJds.map((jd) => {
            const report = matchReports[jd.id];
            const tailored = tailoredCvs[jd.id];
            const isProcessing = processingJds.has(jd.id);
            const isRewriting = processingJds.has(`rewrite_${jd.id}`);

            return (
              <div 
                key={jd.id} 
                className="border border-border bg-card overflow-hidden hover:shadow-lg transition-all duration-300"
                data-testid={`jd-result-${jd.id}`}
              >
                <div className="grid grid-cols-1 md:grid-cols-12">
                  {/* JD Info */}
                  <div className="md:col-span-4 p-6 border-r border-border bg-muted/10">
                    <h3 className="text-xl font-serif mb-2">{jd.title}</h3>
                    {jd.company && <p className="text-sm text-muted-foreground font-mono mb-3">{jd.company}</p>}
                    <div className="text-xs font-mono text-muted-foreground space-y-1">
                      <p>{jd.requirements_count} requirements</p>
                    </div>
                    
                    {!report && (
                      <button
                        onClick={() => handleMatchSingle(jd.id)}
                        disabled={isProcessing}
                        className="mt-4 w-full bg-primary text-primary-foreground px-4 py-3 text-xs font-mono tracking-widest uppercase hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                        data-testid={`match-button-${jd.id}`}
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Matching...
                          </>
                        ) : (
                          <>
                            <Target className="w-4 h-4" />
                            Run Match
                          </>
                        )}
                      </button>
                    )}
                  </div>

                  {/* Match Results */}
                  <div className="md:col-span-8 p-6">
                    {report ? (
                      <div className="space-y-6">
                        {/* Score */}
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-1">ATS Score</p>
                            <div className="flex items-baseline gap-3">
                              <span className="text-5xl font-mono font-medium text-primary" data-testid={`score-${jd.id}`}>
                                {report.total_score}
                              </span>
                              <span className="text-lg text-muted-foreground font-mono">/100</span>
                            </div>
                          </div>
                          
                          {!tailored ? (
                            <button
                              onClick={() => handleRewrite(jd.id)}
                              disabled={isRewriting}
                              className="bg-accent text-accent-foreground px-6 py-3 text-sm font-mono tracking-widest uppercase hover:bg-accent/90 transition-all disabled:opacity-50 flex items-center gap-2"
                              data-testid={`rewrite-button-${jd.id}`}
                            >
                              {isRewriting ? (
                                <>
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                  Generating...
                                </>
                              ) : (
                                'Generate CV'
                              )}
                            </button>
                          ) : (
                            <div className="flex items-center gap-3">
                              <div className="flex items-center gap-2 text-primary">
                                <CheckCircle2 className="w-5 h-5" />
                                <span className="text-sm font-mono">Ready</span>
                              </div>
                              <button
                                onClick={() => handleDownload(jd.id)}
                                className="bg-primary text-primary-foreground px-6 py-3 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all flex items-center gap-2"
                                data-testid={`download-button-${jd.id}`}
                              >
                                <Download className="w-4 h-4" />
                                Download
                              </button>
                            </div>
                          )}
                        </div>

                        {/* Category Scores */}
                        <div className="grid grid-cols-2 gap-3">
                          {Object.entries(report.category_scores).slice(0, 4).map(([category, score]) => (
                            <div key={category} className="bg-muted/20 p-3 border border-border">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-xs font-mono uppercase">{category}</span>
                                <span className="text-sm font-mono font-medium">{score.toFixed(1)}</span>
                              </div>
                              <div className="score-meter h-1">
                                <div className="score-meter-fill" style={{ width: `${score}%` }} />
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Gaps (collapsed) */}
                        {(report.hard_gaps?.length > 0 || report.soft_gaps?.length > 0) && (
                          <details className="border border-border bg-muted/10 p-4">
                            <summary className="cursor-pointer text-sm font-mono uppercase tracking-widest flex items-center gap-2">
                              <AlertCircle className="w-4 h-4" />
                              View Gaps ({(report.hard_gaps?.length || 0) + (report.soft_gaps?.length || 0)})
                            </summary>
                            <div className="mt-4 space-y-3 text-sm">
                              {report.hard_gaps?.length > 0 && (
                                <div>
                                  <p className="font-mono uppercase text-xs text-accent mb-2">Hard Gaps</p>
                                  <ul className="space-y-1">
                                    {report.hard_gaps.slice(0, 3).map((gap, idx) => (
                                      <li key={idx} className="text-muted-foreground border-l-2 border-accent pl-3">{gap}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {report.soft_gaps?.length > 0 && (
                                <div>
                                  <p className="font-mono uppercase text-xs text-primary mb-2">Soft Gaps</p>
                                  <ul className="space-y-1">
                                    {report.soft_gaps.slice(0, 3).map((gap, idx) => (
                                      <li key={idx} className="text-muted-foreground border-l-2 border-primary/50 pl-3">{gap}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </details>
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground font-mono text-sm">Click "Run Match" to analyze</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
