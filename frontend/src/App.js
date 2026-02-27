import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import '@/App.css';
import '@/index.css';

// Pages
import LandingPage from '@/pages/Landing';
import UploadPage from '@/pages/Upload';
import DashboardPage from '@/pages/Dashboard';
import SettingsPage from '@/pages/Settings';

function Navigation() {
  const location = useLocation();
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
          CV Matcher
        </Link>
        <div className="flex gap-8">
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
            to="/settings" 
            className="text-sm font-mono uppercase tracking-widest hover:text-primary transition-colors relative after:content-[''] after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-[1px] after:bg-primary after:transition-all hover:after:w-full"
            data-testid="nav-settings"
          >
            Settings
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
      
      <BrowserRouter>
        <Navigation />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
