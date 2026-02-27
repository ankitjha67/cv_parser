import React from 'react';
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

function Navigation() {
  const location = useLocation();
  const { user } = useAuth();
  const isLanding = location.pathname === '/';

  if (isLanding) return null;

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
          <Link 
            to="/upload" 
            className="text-sm font-mono uppercase tracking-widest hover:text-primary transition-colors relative after:content-[''] after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[1px] after:bg-primary after:transition-all hover:after:w-full"
            data-testid="nav-upload"
          >
            Upload
          </Link>
          <Link 
            to="/dashboard" 
            className="text-sm font-mono uppercase tracking-widest hover:text-primary transition-colors relative after:content-[''] after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[1px] after:bg-primary after:transition-all hover:after:w-full"
            data-testid="nav-dashboard"
          >
            Dashboard
          </Link>
          <Link 
            to="/applications" 
            className="text-sm font-mono uppercase tracking-widest hover:text-primary transition-colors relative after:content-[''] after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[1px] after:bg-primary after:transition-all hover:after:w-full"
            data-testid="nav-applications"
          >
            Applications
          </Link>
          <Link 
            to="/settings" 
            className="text-sm font-mono uppercase tracking-widest hover:text-primary transition-colors relative after:content-[''] after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[1px] after:bg-primary after:transition-all hover:after:w-full"
            data-testid="nav-settings"
          >
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
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
