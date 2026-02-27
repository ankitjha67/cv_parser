import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Plus, Loader2 } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function UploadPage() {
  const navigate = useNavigate();
  const [cvFile, setCvFile] = useState(null);
  const [cvUploading, setCvUploading] = useState(false);
  const [cvUploaded, setCvUploaded] = useState(null);
  const [jdTitle, setJdTitle] = useState('');
  const [jdText, setJdText] = useState('');
  const [jdAdding, setJdAdding] = useState(false);
  const [jdsAdded, setJdsAdded] = useState([]);

  const handleCvUpload = async () => {
    if (!cvFile) return;

    setCvUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', cvFile);

      const response = await axios.post(`${API}/cv/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setCvUploaded(response.data);
      alert(`CV uploaded successfully: ${response.data.name}`);
    } catch (error) {
      console.error('CV upload failed:', error);
      alert('Failed to upload CV: ' + (error.response?.data?.detail || error.message));
    } finally {
      setCvUploading(false);
    }
  };

  const handleAddJd = async () => {
    if (!jdTitle || !jdText) {
      alert('Please provide both JD title and text');
      return;
    }

    setJdAdding(true);
    try {
      const response = await axios.post(`${API}/jd/add`, {
        title: jdTitle,
        text: jdText
      });

      setJdsAdded([...jdsAdded, response.data]);
      setJdTitle('');
      setJdText('');
      alert(`JD added successfully: ${response.data.title}`);
    } catch (error) {
      console.error('JD add failed:', error);
      alert('Failed to add JD: ' + (error.response?.data?.detail || error.message));
    } finally {
      setJdAdding(false);
    }
  };

  const canProceed = cvUploaded && jdsAdded.length > 0;

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-5xl mx-auto">
        <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-4">Step 1</p>
        <h1 className="text-4xl md:text-6xl font-serif tracking-tight font-medium leading-[0.9] mb-4">
          Upload Your Documents
        </h1>
        <p className="text-lg font-sans font-light leading-relaxed text-muted-foreground mb-12 max-w-2xl">
          Start by uploading your CV and adding one or more job descriptions you'd like to match against.
        </p>

        {/* CV Upload */}
        <div 
          className="border border-border bg-card p-0 overflow-hidden mb-8"
          data-testid="cv-upload-section"
        >
          <div className="p-6 border-b border-border/50 bg-muted/10">
            <div className="flex items-center gap-4">
              <FileText className="w-6 h-6 text-primary" strokeWidth={1.5} />
              <h2 className="text-2xl font-serif">Your CV</h2>
            </div>
          </div>
          <div className="p-8">
            {!cvUploaded ? (
              <div>
                <label 
                  className="block border-2 border-dashed border-border hover:border-primary transition-colors p-12 text-center cursor-pointer"
                  data-testid="cv-file-input-label"
                >
                  <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" strokeWidth={1.5} />
                  <p className="text-base font-sans mb-2">Drop your CV here or click to browse</p>
                  <p className="text-sm text-muted-foreground font-mono">Supports PDF, DOCX, TXT</p>
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={(e) => setCvFile(e.target.files[0])}
                    className="hidden"
                    data-testid="cv-file-input"
                  />
                </label>
                {cvFile && (
                  <div className="mt-4">
                    <p className="text-sm font-mono mb-4">Selected: {cvFile.name}</p>
                    <button
                      onClick={handleCvUpload}
                      disabled={cvUploading}
                      className="bg-primary text-primary-foreground px-8 py-4 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all duration-300 disabled:opacity-50"
                      data-testid="cv-upload-button"
                    >
                      {cvUploading ? (
                        <span className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Uploading...
                        </span>
                      ) : (
                        'Upload CV'
                      )}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-muted/20 p-6 border border-border" data-testid="cv-uploaded-info">
                <p className="text-lg font-serif mb-2">✓ CV Uploaded: {cvUploaded.name}</p>
                <p className="text-sm text-muted-foreground font-mono">{cvUploaded.message}</p>
              </div>
            )}
          </div>
        </div>

        {/* JD Input */}
        <div 
          className="border border-border bg-card p-0 overflow-hidden mb-8"
          data-testid="jd-input-section"
        >
          <div className="p-6 border-b border-border/50 bg-muted/10">
            <div className="flex items-center gap-4">
              <Plus className="w-6 h-6 text-primary" strokeWidth={1.5} />
              <h2 className="text-2xl font-serif">Job Descriptions</h2>
            </div>
          </div>
          <div className="p-8">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-mono uppercase tracking-widest mb-2 text-muted-foreground">Job Title</label>
                <input
                  type="text"
                  value={jdTitle}
                  onChange={(e) => setJdTitle(e.target.value)}
                  placeholder="e.g., Senior Backend Engineer"
                  className="w-full border-0 border-b border-input bg-transparent px-0 py-4 text-lg focus-visible:ring-0 focus-visible:border-primary transition-colors placeholder:text-muted-foreground/50 font-serif italic"
                  data-testid="jd-title-input"
                />
              </div>
              <div>
                <label className="block text-sm font-mono uppercase tracking-widest mb-2 text-muted-foreground">JD Text</label>
                <textarea
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="Paste the full job description here..."
                  rows={10}
                  className="w-full border border-input bg-transparent p-4 text-base focus-visible:ring-0 focus-visible:border-primary transition-colors placeholder:text-muted-foreground/50 font-sans"
                  data-testid="jd-text-input"
                />
              </div>
              <button
                onClick={handleAddJd}
                disabled={jdAdding || !jdTitle || !jdText}
                className="bg-primary text-primary-foreground px-8 py-4 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all duration-300 disabled:opacity-50"
                data-testid="add-jd-button"
              >
                {jdAdding ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Adding...
                  </span>
                ) : (
                  'Add JD'
                )}
              </button>
            </div>

            {jdsAdded.length > 0 && (
              <div className="mt-8" data-testid="jds-added-list">
                <p className="text-sm font-mono uppercase tracking-widest mb-4 text-muted-foreground">Added JDs ({jdsAdded.length})</p>
                <div className="space-y-2">
                  {jdsAdded.map((jd, idx) => (
                    <div key={idx} className="bg-muted/20 p-4 border border-border">
                      <p className="font-serif text-lg">{jd.title}</p>
                      <p className="text-sm text-muted-foreground font-mono">{jd.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Proceed Button */}
        {canProceed && (
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full bg-accent text-accent-foreground px-8 py-6 text-base font-mono tracking-widest uppercase hover:bg-accent/90 transition-all duration-300 shadow-lg"
            data-testid="proceed-to-dashboard-button"
          >
            Proceed to Analysis Dashboard →
          </button>
        )}
      </div>
    </div>
  );
}

export default UploadPage;
