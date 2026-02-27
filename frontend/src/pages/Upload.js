import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Plus, Loader2, X, FileUp } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function UploadPage() {
  const navigate = useNavigate();
  const [cvFile, setCvFile] = useState(null);
  const [cvUploading, setCvUploading] = useState(false);
  const [cvUploaded, setCvUploaded] = useState(null);
  
  // JD text input method
  const [jdTitle, setJdTitle] = useState('');
  const [jdText, setJdText] = useState('');
  const [jdAdding, setJdAdding] = useState(false);
  
  // JD file upload method
  const [jdFiles, setJdFiles] = useState([]);
  const [jdUploading, setJdUploading] = useState(false);
  
  const [jdsAdded, setJdsAdded] = useState([]);
  const [uploadMethod, setUploadMethod] = useState('text'); // 'text' or 'file'

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
      localStorage.setItem('current_cv_id', response.data.cv_id);
    } catch (error) {
      console.error('CV upload failed:', error);
      alert('Failed to upload CV: ' + (error.response?.data?.detail || error.message));
    } finally {
      setCvUploading(false);
    }
  };

  const handleAddJdText = async () => {
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
    } catch (error) {
      console.error('JD add failed:', error);
      alert('Failed to add JD: ' + (error.response?.data?.detail || error.message));
    } finally {
      setJdAdding(false);
    }
  };

  const handleUploadJdFiles = async () => {
    if (jdFiles.length === 0) {
      alert('Please select at least one JD file');
      return;
    }

    setJdUploading(true);
    const successfulUploads = [];
    
    try {
      for (const file of jdFiles) {
        try {
          // Read file content
          const text = await file.text();
          
          // Extract title from filename (remove extension)
          const title = file.name.replace(/\.(txt|pdf|docx)$/i, '');
          
          const response = await axios.post(`${API}/jd/add`, {
            title: title,
            text: text
          });
          
          successfulUploads.push(response.data);
        } catch (error) {
          console.error(`Failed to upload ${file.name}:`, error);
        }
      }
      
      if (successfulUploads.length > 0) {
        setJdsAdded([...jdsAdded, ...successfulUploads]);
        setJdFiles([]);
        alert(`Successfully uploaded ${successfulUploads.length} JD(s)`);
      }
    } catch (error) {
      console.error('JD upload failed:', error);
      alert('Failed to upload JDs');
    } finally {
      setJdUploading(false);
    }
  };

  const handleRemoveJd = (index) => {
    setJdsAdded(jdsAdded.filter((_, i) => i !== index));
  };

  const canProceed = cvUploaded && jdsAdded.length > 0;

  const handleProceed = () => {
    // Store JD IDs in localStorage for dashboard
    localStorage.setItem('current_jd_ids', JSON.stringify(jdsAdded.map(jd => jd.jd_id)));
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 md:px-12">
      <div className="max-w-5xl mx-auto">
        <p className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/70 mb-4">Step 1</p>
        <h1 className="text-4xl md:text-6xl font-serif tracking-tight font-medium leading-[0.9] mb-4">
          Upload Your Documents
        </h1>
        <p className="text-lg font-sans font-light leading-relaxed text-muted-foreground mb-12 max-w-2xl">
          Upload your CV and add one or more job descriptions. You can paste JD text or upload multiple JD files.
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
                  <div className="mt-6 flex items-center justify-between bg-muted/20 p-4 border border-border">
                    <p className="text-sm font-mono">Selected: {cvFile.name}</p>
                    <button
                      onClick={handleCvUpload}
                      disabled={cvUploading}
                      className="bg-primary text-primary-foreground px-6 py-3 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all duration-300 disabled:opacity-50 flex items-center gap-2"
                      data-testid="cv-upload-button"
                    >
                      {cvUploading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          Upload CV
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-primary/10 border border-primary/20 p-6" data-testid="cv-uploaded-info">
                <p className="text-lg font-serif mb-2 text-primary">✓ CV Uploaded: {cvUploaded.name}</p>
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
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Plus className="w-6 h-6 text-primary" strokeWidth={1.5} />
                <h2 className="text-2xl font-serif">Job Descriptions</h2>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setUploadMethod('text')}
                  className={`px-4 py-2 text-xs font-mono uppercase tracking-widest transition-all ${
                    uploadMethod === 'text' 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-transparent border border-border hover:border-primary'
                  }`}
                  data-testid="jd-text-method-button"
                >
                  Paste Text
                </button>
                <button
                  onClick={() => setUploadMethod('file')}
                  className={`px-4 py-2 text-xs font-mono uppercase tracking-widest transition-all ${
                    uploadMethod === 'file' 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-transparent border border-border hover:border-primary'
                  }`}
                  data-testid="jd-file-method-button"
                >
                  Upload Files
                </button>
              </div>
            </div>
          </div>
          <div className="p-8">
            {uploadMethod === 'text' ? (
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
                  onClick={handleAddJdText}
                  disabled={jdAdding || !jdTitle || !jdText}
                  className="bg-primary text-primary-foreground px-8 py-4 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all duration-300 disabled:opacity-50 flex items-center gap-2"
                  data-testid="add-jd-button"
                >
                  {jdAdding ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4" />
                      Add JD
                    </>
                  )}
                </button>
              </div>
            ) : (
              <div>
                <label 
                  className="block border-2 border-dashed border-border hover:border-primary transition-colors p-12 text-center cursor-pointer mb-6"
                  data-testid="jd-files-input-label"
                >
                  <FileUp className="w-12 h-12 mx-auto mb-4 text-muted-foreground" strokeWidth={1.5} />
                  <p className="text-base font-sans mb-2">Drop JD files here or click to browse</p>
                  <p className="text-sm text-muted-foreground font-mono">Upload multiple TXT files at once</p>
                  <input
                    type="file"
                    accept=".txt"
                    multiple
                    onChange={(e) => setJdFiles(Array.from(e.target.files))}
                    className="hidden"
                    data-testid="jd-files-input"
                  />
                </label>
                
                {jdFiles.length > 0 && (
                  <div className="space-y-4">
                    <div className="bg-muted/20 p-4 border border-border">
                      <p className="text-sm font-mono mb-3">Selected {jdFiles.length} file(s):</p>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {jdFiles.map((file, idx) => (
                          <div key={idx} className="flex items-center justify-between text-sm font-sans py-1">
                            <span>{file.name}</span>
                            <button
                              onClick={() => setJdFiles(jdFiles.filter((_, i) => i !== idx))}
                              className="text-accent hover:text-accent/80"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                    <button
                      onClick={handleUploadJdFiles}
                      disabled={jdUploading}
                      className="bg-primary text-primary-foreground px-8 py-4 text-sm font-mono tracking-widest uppercase hover:bg-primary/90 transition-all duration-300 disabled:opacity-50 flex items-center gap-2"
                      data-testid="upload-jd-files-button"
                    >
                      {jdUploading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          Upload {jdFiles.length} JD(s)
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}

            {jdsAdded.length > 0 && (
              <div className="mt-8 pt-8 border-t border-border" data-testid="jds-added-list">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm font-mono uppercase tracking-widest text-muted-foreground">Added JDs ({jdsAdded.length})</p>
                </div>
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {jdsAdded.map((jd, idx) => (
                    <div key={idx} className="bg-muted/20 p-4 border border-border flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-serif text-lg mb-1">{jd.title}</p>
                        <p className="text-sm text-muted-foreground font-mono">{jd.message}</p>
                      </div>
                      <button
                        onClick={() => handleRemoveJd(idx)}
                        className="ml-4 text-accent hover:text-accent/80 transition-colors"
                        data-testid={`remove-jd-${idx}`}
                      >
                        <X className="w-5 h-5" />
                      </button>
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
            onClick={handleProceed}
            className="w-full bg-accent text-accent-foreground px-8 py-6 text-base font-mono tracking-widest uppercase hover:bg-accent/90 transition-all duration-300 shadow-lg flex items-center justify-center gap-3"
            data-testid="proceed-to-dashboard-button"
          >
            Proceed to Analysis Dashboard ({jdsAdded.length} JD{jdsAdded.length > 1 ? 's' : ''}) →
          </button>
        )}
      </div>
    </div>
  );
}

export default UploadPage;
