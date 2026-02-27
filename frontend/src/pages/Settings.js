import React, { useState } from 'react';
import { Key, Save, Info, User, LogIn, LogOut } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

function SettingsPage() {
  const { user, login, logout } = useAuth();
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [saved, setSaved] = useState(false);
  
  // Auth form
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');

  const handleSave = () => {
    localStorage.setItem('openai_key', openaiKey);
    localStorage.setItem('anthropic_key', anthropicKey);
    localStorage.setItem('gemini_key', geminiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleLogin = async () => {
    if (!email || !name) {
      alert('Please enter both email and name');
      return;
    }
    const success = await login(email, name);
    if (success) {
      setEmail('');
      setName('');
    } else {
      alert('Login failed');
    }
  };

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-3xl mx-auto">
        <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-4">Configuration</p>
        <h1 className="text-4xl md:text-6xl font-serif tracking-tight font-medium leading-[0.9] mb-4">
          Settings
        </h1>
        <p className="text-lg font-sans font-light leading-relaxed text-muted-foreground mb-12 max-w-2xl">
          Manage your account and configure API keys for LLM providers.
        </p>

        {/* Account Section */}
        <div className="border border-border bg-card overflow-hidden mb-8">
          <div className="p-6 border-b border-border/50 bg-muted/10">
            <div className="flex items-center gap-4">
              <User className="w-6 h-6 text-primary" strokeWidth={1.5} />
              <h2 className="text-2xl font-serif">Account</h2>
            </div>
          </div>
          <div className="p-8">
            {user ? (
              <div>
                <div className="bg-primary/10 border border-primary/20 p-6 mb-6">
                  <p className="text-lg font-serif mb-2">Signed in as</p>
                  <p className="text-2xl font-mono text-primary">{user.email}</p>
                  <p className="text-muted-foreground mt-1">{user.name}</p>
                </div>
                <button
                  onClick={logout}
                  className="bg-accent text-accent-foreground px-8 py-4 text-sm font-mono tracking-widest uppercase hover:bg-accent/90 transition-all flex items-center gap-2"
                  data-testid="logout-button"
                >
                  <LogOut className="w-5 h-5" />
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-mono uppercase tracking-widest mb-2 text-muted-foreground">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary transition-colors placeholder:text-muted-foreground/50 font-mono"
                    data-testid="email-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-mono uppercase tracking-widest mb-2 text-muted-foreground">Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary transition-colors placeholder:text-muted-foreground/50 font-mono"
                    data-testid="name-input"
                  />
                </div>
                <button
                  onClick={handleLogin}
                  className="bg-primary text-primary-foreground px-8 py-4 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all flex items-center gap-2"
                  data-testid="login-button"
                >
                  <LogIn className="w-5 h-5" />
                  Sign In / Register
                </button>
                <p className="text-xs text-muted-foreground">
                  * No password required. Simple email-based authentication for demo purposes.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-primary/10 border border-primary/20 p-6 mb-8 flex gap-4" data-testid="info-box">
          <Info className="w-6 h-6 text-primary flex-shrink-0" strokeWidth={1.5} />
          <div>
            <p className="text-sm font-sans leading-relaxed mb-2">
              <strong className="font-mono">Emergent LLM Key:</strong> A universal key is pre-configured via environment variable for OpenAI, Anthropic, and Gemini.
            </p>
            <p className="text-sm font-sans leading-relaxed">
              <strong className="font-mono">Local LLMs:</strong> You can also use Ollama or other local models by configuring the API URL below.
            </p>
          </div>
        </div>

        {/* API Keys */}
        <div className="border border-border bg-card overflow-hidden mb-8">
          <div className="p-6 border-b border-border/50 bg-muted/10">
            <div className="flex items-center gap-4">
              <Key className="w-6 h-6 text-primary" strokeWidth={1.5} />
              <h2 className="text-2xl font-serif">API Keys & Local LLMs</h2>
            </div>
          </div>
          <div className="p-8 space-y-8">
            <div>
              <label className="block text-sm font-mono uppercase tracking-widest mb-2 text-muted-foreground">OpenAI API Key</label>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary transition-colors placeholder:text-muted-foreground/50 font-mono"
                data-testid="openai-key-input"
              />
            </div>
            <div>
              <label className="block text-sm font-mono uppercase tracking-widest mb-2 text-muted-foreground">Anthropic API Key</label>
              <input
                type="password"
                value={anthropicKey}
                onChange={(e) => setAnthropicKey(e.target.value)}
                placeholder="sk-ant-..."
                className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary transition-colors placeholder:text-muted-foreground/50 font-mono"
                data-testid="anthropic-key-input"
              />
            </div>
            <div>
              <label className="block text-sm font-mono uppercase tracking-widest mb-2 text-muted-foreground">Google Gemini API Key</label>
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="AIza..."
                className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary transition-colors placeholder:text-muted-foreground/50 font-mono"
                data-testid="gemini-key-input"
              />
            </div>
            
            {/* Ollama Configuration */}
            <div className="pt-6 border-t border-border">
              <label className="block text-sm font-mono uppercase tracking-widest mb-2 text-primary">Ollama API URL (Local LLM)</label>
              <input
                type="text"
                value={localStorage.getItem('ollama_url') || ''}
                onChange={(e) => localStorage.setItem('ollama_url', e.target.value)}
                placeholder="http://localhost:11434"
                className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary transition-colors placeholder:text-muted-foreground/50 font-mono"
                data-testid="ollama-url-input"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Run Ollama locally to use models like llama2, mistral, codellama without API costs.
              </p>
            </div>
            
            {/* Custom LLM Endpoint */}
            <div>
              <label className="block text-sm font-mono uppercase tracking-widest mb-2 text-primary">Custom LLM Endpoint</label>
              <input
                type="text"
                value={localStorage.getItem('custom_llm_url') || ''}
                onChange={(e) => localStorage.setItem('custom_llm_url', e.target.value)}
                placeholder="http://your-llm-server:8080/api"
                className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary transition-colors placeholder:text-muted-foreground/50 font-mono"
                data-testid="custom-llm-url-input"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Connect to any OpenAI-compatible API endpoint (LM Studio, LocalAI, etc.)
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="w-full bg-primary text-primary-foreground px-8 py-6 text-base font-mono tracking-widest uppercase hover:bg-primary/90 transition-all duration-300 flex items-center justify-center gap-3"
          data-testid="save-settings-button"
        >
          <Save className="w-5 h-5" />
          {saved ? 'Saved Successfully!' : 'Save Settings'}
        </button>

        {/* Provider Info */}
        <div className="mt-12 border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border/50 bg-muted/10">
            <h2 className="text-xl font-serif">Provider Information</h2>
          </div>
          <div className="p-8 space-y-4 text-sm font-sans leading-relaxed text-muted-foreground">
            <p><strong className="text-foreground">Deterministic:</strong> No API key needed. Pure Python with regex, TF-IDF, and verb templates. 100% offline.</p>
            <p><strong className="text-foreground">OpenAI:</strong> Uses emergentintegrations with models like gpt-5.2, gpt-4o. Requires EMERGENT_LLM_KEY or your own key.</p>
            <p><strong className="text-foreground">Anthropic:</strong> Claude Sonnet 4.5, Opus 4.5. Requires EMERGENT_LLM_KEY or your own key.</p>
            <p><strong className="text-foreground">Gemini:</strong> Google Gemini 2.5 Pro, 3 Flash. Requires EMERGENT_LLM_KEY or your own key.</p>
            <p><strong className="text-foreground">HuggingFace:</strong> Local transformers (gpt2, etc.). No key needed, but currently uses deterministic fallback.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
