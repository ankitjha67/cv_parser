import React from 'react';
import { Link } from 'react-router-dom';
import { Upload, Zap, Shield, TrendingUp } from 'lucide-react';

function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section - Tetris Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-0 border-collapse">
        {/* Main Hero */}
        <div 
          className="col-span-1 md:col-span-8 lg:col-span-9 row-span-2 bg-foreground text-background border border-border/40 p-8 md:p-16 min-h-[600px] flex flex-col justify-between hover:bg-foreground/95 transition-all duration-500"
          data-testid="hero-section"
        >
          <div>
            <p className="text-xs font-mono uppercase tracking-[0.2em] text-background/70 mb-6">Zero Hallucination AI</p>
            <h1 className="text-5xl md:text-7xl font-serif tracking-tight font-medium leading-[0.9] mb-8">
              Precision CV Matching.<br />Evidence-Based.<br />Luxury Execution.
            </h1>
            <p className="text-lg md:text-xl font-sans font-light leading-relaxed text-background/80 max-w-2xl">
              ATS-grade scoring, gap analysis, and truthful CV rewriting powered by deterministic ML and optional LLMs. Every claim traced to source. No fabrication. Pure alignment.
            </p>
          </div>
          
          <div className="flex gap-4 mt-12">
            <Link
              to="/upload"
              className="bg-background text-foreground px-8 py-6 text-sm font-mono tracking-widest uppercase hover:bg-background/90 transition-all duration-300 border border-background/10 shadow-lg"
              data-testid="cta-get-started"
            >
              Get Started
            </Link>
            <a
              href="#features"
              className="bg-transparent border border-background/30 text-background px-8 py-6 text-sm font-mono tracking-widest uppercase hover:border-background hover:bg-background/10 transition-all duration-300"
              data-testid="cta-learn-more"
            >
              Learn More
            </a>
          </div>
        </div>
        
        {/* Side CTA */}
        <div className="col-span-1 md:col-span-4 lg:col-span-3 row-span-1 flex items-center justify-center bg-accent text-accent-foreground border border-border/40 p-8 md:p-12 min-h-[300px] hover:bg-accent/90 transition-all duration-500">
          <div className="text-center">
            <Zap className="w-16 h-16 mx-auto mb-4" strokeWidth={1.5} />
            <h3 className="text-2xl font-serif mb-2">100% Factual</h3>
            <p className="text-sm font-mono uppercase tracking-widest">No Hallucinations</p>
          </div>
        </div>
        
        <div className="col-span-1 md:col-span-4 lg:col-span-3 row-span-1 flex items-center justify-center bg-card border border-border/40 p-8 md:p-12 min-h-[300px] hover:bg-muted/30 transition-all duration-500">
          <div className="text-center">
            <Shield className="w-16 h-16 mx-auto mb-4 text-primary" strokeWidth={1.5} />
            <h3 className="text-2xl font-serif mb-2">Privacy First</h3>
            <p className="text-sm font-mono uppercase tracking-widest text-muted-foreground">Local Mode Available</p>
          </div>
        </div>
      </div>
      
      {/* Features Section */}
      <div id="features" className="max-w-[1920px] mx-auto p-6 md:p-16 my-16">
        <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-4">How It Works</p>
        <h2 className="text-4xl md:text-6xl font-serif tracking-tight font-normal mb-16">Three Steps to Precision</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div 
            className="border border-border bg-card p-0 overflow-hidden group relative hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
            data-testid="feature-upload"
          >
            <div className="p-6 border-b border-border/50 bg-muted/10">
              <Upload className="w-10 h-10 text-primary mb-4" strokeWidth={1.5} />
              <h3 className="text-2xl font-serif">1. Upload CV & JDs</h3>
            </div>
            <div className="p-6">
              <p className="text-base font-sans leading-relaxed text-muted-foreground">
                Drop your resume (PDF/DOCX/TXT) and paste multiple job descriptions. Our deterministic parser extracts structured data with zero loss.
              </p>
            </div>
          </div>
          
          <div 
            className="border border-border bg-card p-0 overflow-hidden group relative hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
            data-testid="feature-analysis"
          >
            <div className="p-6 border-b border-border/50 bg-muted/10">
              <TrendingUp className="w-10 h-10 text-primary mb-4" strokeWidth={1.5} />
              <h3 className="text-2xl font-serif">2. ATS Analysis</h3>
            </div>
            <div className="p-6">
              <p className="text-base font-sans leading-relaxed text-muted-foreground">
                Get explainable scores (Skills 35%, Experience 30%, Tenure 15%, Education 10%, Keywords 10%) plus hard and soft gap analysis.
              </p>
            </div>
          </div>
          
          <div 
            className="border border-border bg-card p-0 overflow-hidden group relative hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
            data-testid="feature-rewrite"
          >
            <div className="p-6 border-b border-border/50 bg-muted/10">
              <Shield className="w-10 h-10 text-primary mb-4" strokeWidth={1.5} />
              <h3 className="text-2xl font-serif">3. Truthful Rewrite</h3>
            </div>
            <div className="p-6">
              <p className="text-base font-sans leading-relaxed text-muted-foreground">
                Tailored CV per JD with evidence traceability. Deterministic mode (no LLM) or choose OpenAI/Claude/Gemini. Every bullet verified.
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Footer CTA */}
      <div className="border-t border-border/40 bg-muted/20 p-12 md:p-24 text-center">
        <h2 className="text-3xl md:text-5xl font-serif tracking-tight mb-8">Ready to match with precision?</h2>
        <Link
          to="/upload"
          className="inline-block bg-primary text-primary-foreground px-12 py-6 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 shadow-lg shadow-primary/20 transition-all duration-300"
          data-testid="footer-cta"
        >
          Start Now
        </Link>
      </div>
    </div>
  );
}

export default LandingPage;
