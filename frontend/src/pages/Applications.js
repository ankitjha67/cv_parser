import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Calendar, Loader2, TrendingUp, Award, Target } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_COLORS = {
  'applied': 'bg-blue-100 text-blue-800 border-blue-200',
  'screening': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  'interview': 'bg-purple-100 text-purple-800 border-purple-200',
  'offer': 'bg-green-100 text-green-800 border-green-200',
  'accepted': 'bg-primary/20 text-primary border-primary/30',
  'rejected': 'bg-red-100 text-red-800 border-red-200',
  'withdrawn': 'bg-gray-100 text-gray-800 border-gray-200'
};

function ApplicationsPage() {
  const { user, getAuthHeader } = useAuth();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingApp, setEditingApp] = useState(null);
  const [successRates, setSuccessRates] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    company_name: '',
    position: '',
    status: 'applied',
    notes: ''
  });

  useEffect(() => {
    if (user) {
      loadApplications();
      loadSuccessRates();
    } else {
      setLoading(false);
    }
  }, [user]);

  const loadApplications = async () => {
    try {
      const response = await axios.get(`${API}/applications`, {
        headers: getAuthHeader()
      });
      setApplications(response.data || []);
    } catch (error) {
      console.error('Failed to load applications:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSuccessRates = async () => {
    try {
      const response = await axios.get(`${API}/analytics/success-rates`, {
        headers: getAuthHeader()
      });
      setSuccessRates(response.data);
    } catch (error) {
      console.error('Failed to load success rates:', error);
    }
  };

  const handleAdd = async () => {
    if (!formData.company_name || !formData.position) {
      alert('Please fill required fields');
      return;
    }

    try {
      await axios.post(`${API}/applications`, formData, {
        headers: getAuthHeader()
      });
      setShowAddModal(false);
      setFormData({ company_name: '', position: '', status: 'applied', notes: '' });
      loadApplications();
    } catch (error) {
      console.error('Failed to add application:', error);
      alert('Failed to add application');
    }
  };

  const handleUpdate = async (appId, updates) => {
    try {
      await axios.put(`${API}/applications/${appId}`, updates, {
        headers: getAuthHeader()
      });
      loadApplications();
      setEditingApp(null);
    } catch (error) {
      console.error('Failed to update application:', error);
      alert('Failed to update');
    }
  };

  const handleDelete = async (appId) => {
    if (!window.confirm('Delete this application?')) return;
    
    try {
      await axios.delete(`${API}/applications/${appId}`, {
        headers: getAuthHeader()
      });
      loadApplications();
    } catch (error) {
      console.error('Failed to delete application:', error);
      alert('Failed to delete');
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen pt-24 pb-16 px-6 md:px-12 flex items-center justify-center">
        <div className="text-center max-w-2xl">
          <Target className="w-16 h-16 mx-auto mb-6 text-muted-foreground/50" strokeWidth={1.5} />
          <h2 className="text-3xl font-serif mb-4">Sign In Required</h2>
          <p className="text-lg text-muted-foreground mb-8">
            Please go to Settings to sign in or register an account to track your applications.
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

  const stats = {
    total: applications.length,
    interviews: applications.filter(a => a.status === 'interview').length,
    offers: applications.filter(a => a.status === 'offer' || a.status === 'accepted').length,
    avgScore: applications.filter(a => a.match_score).length > 0
      ? (applications.filter(a => a.match_score).reduce((sum, a) => sum + a.match_score, 0) / applications.filter(a => a.match_score).length).toFixed(1)
      : 'N/A'
  };

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-[1920px] mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-2">Application Tracker</p>
            <h1 className="text-4xl md:text-6xl font-serif tracking-tight font-medium leading-[0.9]">
              My Applications
            </h1>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-6 py-4 text-sm font-mono uppercase tracking-widest hover:bg-primary/90 transition-all"
            data-testid="add-application-button"
          >
            <Plus className="w-5 h-5" />
            Add Application
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="border border-border bg-card p-6">
            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2">Total Applications</p>
            <p className="text-5xl font-mono font-medium text-primary">{stats.total}</p>
          </div>
          <div className="border border-border bg-card p-6">
            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2">Interviews</p>
            <p className="text-5xl font-mono font-medium text-purple-600">{stats.interviews}</p>
          </div>
          <div className="border border-border bg-card p-6">
            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2">Offers</p>
            <p className="text-5xl font-mono font-medium text-green-600">{stats.offers}</p>
          </div>
          <div className="border border-border bg-card p-6">
            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2">Avg Match Score</p>
            <p className="text-5xl font-mono font-medium text-accent">{stats.avgScore}</p>
          </div>
        </div>

        {/* Success Rates by Score */}
        {successRates && Object.keys(successRates).length > 0 && (
          <div className="border border-border bg-card p-8 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <TrendingUp className="w-6 h-6 text-primary" />
              <h2 className="text-2xl font-serif">Success Rates by Match Score</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {Object.entries(successRates).map(([range, data]) => (
                <div key={range} className="bg-muted/20 p-4 border border-border">
                  <p className="text-sm font-mono uppercase tracking-widest mb-2">Score {range}</p>
                  <p className="text-3xl font-mono font-medium text-primary mb-1">
                    {data.success_rate.toFixed(1)}%
                  </p>
                  <p className="text-xs text-muted-foreground font-mono">
                    {data.offers}/{data.total} offers
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Applications List */}
        <div className="space-y-4">
          {applications.length === 0 ? (
            <div className="text-center py-24 border border-border bg-card">
              <Target className="w-16 h-16 mx-auto mb-6 text-muted-foreground/50" strokeWidth={1.5} />
              <p className="text-xl font-serif text-muted-foreground">No applications yet</p>
              <p className="text-sm text-muted-foreground mt-2">Click "Add Application" to start tracking</p>
            </div>
          ) : (
            applications.map((app) => (
              <div
                key={app.id}
                className="border border-border bg-card overflow-hidden hover:shadow-lg transition-all"
                data-testid={`application-${app.id}`}
              >
                <div className="grid grid-cols-1 md:grid-cols-12 p-6 gap-6">
                  <div className="md:col-span-6">
                    <h3 className="text-xl font-serif mb-2">{app.position}</h3>
                    <p className="text-lg text-muted-foreground font-sans mb-3">{app.company_name}</p>
                    <div className="flex gap-2 items-center text-xs font-mono text-muted-foreground">
                      <Calendar className="w-4 h-4" />
                      Applied: {new Date(app.application_date).toLocaleDateString()}
                    </div>
                    {app.notes && (
                      <p className="mt-3 text-sm text-muted-foreground">{app.notes}</p>
                    )}
                  </div>
                  <div className="md:col-span-3 flex flex-col justify-center">
                    {app.match_score !== null && (
                      <div className="mb-3">
                        <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-1">Match Score</p>
                        <p className="text-4xl font-mono font-medium text-primary">{app.match_score.toFixed(1)}</p>
                      </div>
                    )}
                    <select
                      value={app.status}
                      onChange={(e) => handleUpdate(app.id, { status: e.target.value })}
                      className={`border px-4 py-2 text-sm font-mono uppercase ${STATUS_COLORS[app.status]}`}
                      data-testid={`status-select-${app.id}`}
                    >
                      <option value="applied">Applied</option>
                      <option value="screening">Screening</option>
                      <option value="interview">Interview</option>
                      <option value="offer">Offer</option>
                      <option value="accepted">Accepted</option>
                      <option value="rejected">Rejected</option>
                      <option value="withdrawn">Withdrawn</option>
                    </select>
                  </div>
                  <div className="md:col-span-3 flex items-center justify-end gap-3">
                    <button
                      onClick={() => setEditingApp(app)}
                      className="p-3 border border-border hover:border-primary transition-colors"
                      data-testid={`edit-button-${app.id}`}
                    >
                      <Edit2 className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(app.id)}
                      className="p-3 border border-border hover:border-accent transition-colors text-accent"
                      data-testid={`delete-button-${app.id}`}
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Add Application Modal */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-6">
            <div className="bg-background border border-border max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-border bg-muted/10">
                <h2 className="text-2xl font-serif">Add New Application</h2>
              </div>
              <div className="p-8 space-y-6">
                <div>
                  <label className="block text-sm font-mono uppercase tracking-widest mb-2">Company Name *</label>
                  <input
                    type="text"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary font-serif italic"
                    data-testid="modal-company-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono uppercase tracking-widest mb-2">Position *</label>
                  <input
                    type="text"
                    value={formData.position}
                    onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                    className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary font-serif italic"
                    data-testid="modal-position-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono uppercase tracking-widest mb-2">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full border border-input bg-background p-3 text-sm font-sans"
                  >
                    <option value="applied">Applied</option>
                    <option value="screening">Screening</option>
                    <option value="interview">Interview</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-mono uppercase tracking-widest mb-2">Notes</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={4}
                    className="w-full border border-input bg-transparent p-4 text-base font-sans"
                  />
                </div>
                <div className="flex gap-4">
                  <button
                    onClick={handleAdd}
                    className="flex-1 bg-primary text-primary-foreground px-6 py-4 text-sm font-mono uppercase tracking-widest hover:bg-primary/90"
                    data-testid="modal-add-button"
                  >
                    Add Application
                  </button>
                  <button
                    onClick={() => setShowAddModal(false)}
                    className="flex-1 bg-transparent border border-border px-6 py-4 text-sm font-mono uppercase tracking-widest hover:border-primary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ApplicationsPage;
