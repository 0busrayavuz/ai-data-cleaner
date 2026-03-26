import React, { useCallback, useState } from 'react';
import { UploadCloud, FileType, CheckCircle } from 'lucide-react';
import './FileUpload.css';

const FileUpload = ({ onFileSelect }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selectedFile = e.dataTransfer.files[0];
      setFile(selectedFile);
      if (onFileSelect) onFileSelect(selectedFile);
    }
  }, [onFileSelect]);

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (onFileSelect) onFileSelect(selectedFile);
    }
  };

  return (
    <div className="upload-container">
      <div 
        className={`dropzone glass-panel ${isDragging ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          id="file-upload" 
          className="file-input" 
          onChange={handleChange} 
          accept=".csv,.xlsx,.xls"
        />
        <label htmlFor="file-upload" className="dropzone-label">
          {!file ? (
            <>
              <div className="icon-pulse">
                <UploadCloud size={64} className="upload-icon floating-icon" />
              </div>
              <h3 style={{ fontSize: '1.8rem', fontWeight: '700', marginBottom: '16px', color: 'var(--text-primary)' }}>
                Yüklenecek Dosyayı Sürükleyin
              </h3>
              <p style={{ fontSize: '1.05rem', color: 'var(--text-secondary)', marginBottom: '32px' }}>
                CSV veya Excel formatları desteklenir (Maksimum 500MB)
              </p>
              <div className="btn-primary" style={{ padding: '16px 36px', fontSize: '1.1rem' }}>Dosya Seçin</div>
            </>
          ) : (
            <>
              <CheckCircle size={64} className="success-icon floating-icon" />
              <div className="file-info" style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                <FileType size={24} className="file-type-icon" />
                <span className="file-name" style={{ color: '#064e3b', fontWeight: '600' }}>{file.name}</span>
              </div>
              <p className="file-size" style={{ color: '#047857', fontWeight: '500', fontSize: '1rem' }}>{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
            </>
          )}
        </label>
      </div>
    </div>
  );
};

export default FileUpload;
