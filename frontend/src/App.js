import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import '@/App.css';
import '@/index.css';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';

// Pages
import LandingPage from '@/pages/Landing';
import UploadPage from '@/pages/Upload';
import DashboardPage from '@/pages/Dashboard';
import ApplicationsPage from '@/pages/Applications';
import InterviewPrepPage from '@/pages/InterviewPrep';
import RecruiterDashboardPage from '@/pages/RecruiterDashboard';
import SettingsPage from '@/pages/Settings';
import AnalyticsPage from '@/pages/Analytics';

const NAV_LINK_CLS =
  "text-sm font-mono uppercase tracking-widest hover:text-primary transition-colors relative " +
  "after:content-[''] after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[1px] " +
  "after:bg-primary after:transition-all hover:after:w-full";

function NotificationBell() {
  const { user } = useAuth();
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!user?.email) return;
    const fetchCount = () => {
      fetch(`/api/notifications/unread-count?email=${encodeURIComponent(user.email)}`)
        .then(r => r.ok ? r.json() : { count: 0 })
        .then(d => setCount(d.count || 0))
        .catch(() => {});
    };
    fetchCount();
    const id = setInterval(fetchCount, 30000);
    return () => clearInterval(id);
  }, [user]);

  return (
    <Link to="/applications" className="relative flex items-center" title="Notifications" aria-label="Notifications">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
        strokeLinecap="round" strokeLinejoin="round" className="hover:text-primary transition-colors">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
      {count > 0 && (
        <span className="absolute -top-1.5 -right-1.5 bg-accent text-white text-[9px] font-bold rounded-full min-w-[16px] h-4 flex items-center justify-center px-1 leading-none">
          {count > 99 ? '99+' : count}
        </span>
      )}
    </Link>
  );
}

function Navigation() {
  const location = useLocation();
  const { user } = useAuth();
  const isLanding = location.pathname === '/';

  if (isLanding) return null;

  const isRecruiter = user?.role === 'recruiter' || user?.role === 'admin';

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 backdrop-blur-md bg-background/80 supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-[1920px] mx-auto px-6 md:px-12 py-6 flex items-center justify-between">
        <Link
          to="/"
          className="text-2xl font-serif font-semibold tracking-tight hover:text-primary transition-colors"
          data-testid="logo-link"
        >
          CV Matcher <span className="text-xs font-mono text-accent ml-2">PREMIUM</span>
        </Link>
        <div className="flex gap-8 items-center">
          <Link to="/upload" className={NAV_LINK_CLS} data-testid="nav-upload">Upload</Link>
          <Link to="/dashboard" className={NAV_LINK_CLS} data-testid="nav-dashboard">Dashboard</Link>
          <Link to="/applications" className={NAV_LINK_CLS} data-testid="nav-applications">Applications</Link>
          <Link to="/analytics" className={NAV_LINK_CLS} data-testid="nav-analytics">Analytics</Link>
          {isRecruiter && (
            <Link to="/recruiter" className={NAV_LINK_CLS} data-testid="nav-recruiter">Recruiter</Link>
          )}
          <NotificationBell />
          <Link to="/settings" className={NAV_LINK_CLS} data-testid="nav-settings">
            {user ? user.name.split(' ')[0] : 'Settings'}
          </Link>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <div className="App">
      {/* Noise overlay */}
      <div className="noise-overlay" />

      <AuthProvider>
        <BrowserRouter>
          <Navigation />
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/interview-prep" element={<InterviewPrepPage />} />
            <Route path="/recruiter" element={<RecruiterDashboardPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
