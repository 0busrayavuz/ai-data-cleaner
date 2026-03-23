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
                <UploadCloud size={48} className="upload-icon" />
              </div>
              <h3>Drag & Drop your dataset here</h3>
              <p>Supports CSV, Excel (Up to 500MB)</p>
              <div className="btn-secondary">Browse Files</div>
            </>
          ) : (
            <>
              <CheckCircle size={48} className="success-icon" />
              <div className="file-info">
                <FileType size={20} className="file-type-icon" />
                <span className="file-name">{file.name}</span>
              </div>
              <p className="file-size">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
              <div className="btn-secondary">Change File</div>
            </>
          )}
        </label>
      </div>
    </div>
  );
};

export default FileUpload;
