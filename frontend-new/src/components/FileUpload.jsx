import { useCallback, useState } from 'react';
import {
  CheckCircle2,
  FileSpreadsheet,
  FolderKanban,
  Lock,
  Plus,
  ShieldCheck,
  UploadCloud,
} from 'lucide-react';
import './FileUpload.css';

const FileUpload = ({
  onFileSelect,
  canUpload = true,
  onNeedAuth,
  projects = [],
  selectedProjectId = null,
  onProjectChange,
  onCreateProject,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [newProjectName, setNewProjectName] = useState('');
  const [creatingProject, setCreatingProject] = useState(false);

  const acceptFile = useCallback((selectedFile) => {
    setFile(selectedFile);
    onFileSelect?.(selectedFile);
  }, [onFileSelect]);

  const handleDrag = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(event.type === 'dragenter' || event.type === 'dragover');
  }, []);

  const handleDrop = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);

    if (!canUpload) {
      onNeedAuth?.();
      return;
    }

    const selectedFile = event.dataTransfer.files?.[0];
    if (selectedFile) acceptFile(selectedFile);
  }, [acceptFile, canUpload, onNeedAuth]);

  const handleChange = (event) => {
    if (!canUpload) {
      event.target.value = '';
      onNeedAuth?.();
      return;
    }
    const selectedFile = event.target.files?.[0];
    if (selectedFile) acceptFile(selectedFile);
  };

  const handleCreateProject = async () => {
    const name = newProjectName.trim();
    if (!name || !onCreateProject) return;
    setCreatingProject(true);
    try {
      await onCreateProject(name);
      setNewProjectName('');
    } finally {
      setCreatingProject(false);
    }
  };

  return (
    <section id="upload-workspace" className="upload-section" aria-labelledby="upload-heading">
      <div className="upload-heading-row">
        <div>
          <span className="upload-overline">Yeni çalışma</span>
          <h3 id="upload-heading">Veri setinizi analiz için yükleyin.</h3>
        </div>
        <p>
          Dosyanız önce okunabilirlik ve yapı kontrolünden geçer. Analiz sonucunda
          hiçbir değişiklik kullanıcı onayı olmadan uygulanmaz.
        </p>
      </div>

      <div className="upload-workspace">
        <aside className="upload-sidebar">
          <div className="upload-sidebar-head">
            <span className="upload-sidebar-icon"><FolderKanban size={20} /></span>
            <div>
              <strong>Çalışma bilgisi</strong>
              <small>Dosyanızı bir proje altında gruplayın.</small>
            </div>
          </div>

          {canUpload ? (
            <>
              <label className="upload-field-label" htmlFor="upload-project-select">Proje</label>
              <select
                id="upload-project-select"
                className="project-select"
                value={selectedProjectId ?? ''}
                onChange={(event) => onProjectChange?.(
                  event.target.value === '' ? null : Number(event.target.value)
                )}
              >
                <option value="">Bağımsız veri seti</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>

              <div className="project-create-block">
                <label className="upload-field-label" htmlFor="new-project-name">Yeni proje</label>
                <div className="project-new-row">
                  <input
                    id="new-project-name"
                    type="text"
                    className="project-new-input"
                    placeholder="Örn. Satış verileri"
                    value={newProjectName}
                    onChange={(event) => setNewProjectName(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        event.preventDefault();
                        handleCreateProject();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn-project-create"
                    onClick={handleCreateProject}
                    disabled={creatingProject || !newProjectName.trim() || !onCreateProject}
                    aria-label="Yeni proje oluştur"
                  >
                    <Plus size={18} aria-hidden />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <button type="button" className="upload-login-card" onClick={onNeedAuth}>
              <Lock size={18} aria-hidden />
              <span><strong>Giriş yapmanız gerekiyor</strong><small>Dosya ve raporlar hesabınıza bağlanır.</small></span>
            </button>
          )}

          <div className="upload-security-note">
            <ShieldCheck size={17} aria-hidden />
            <span>İşlem geçmişi ve dosya sahipliği korunur.</span>
          </div>

          <div className="upload-scope-note">
            <strong>Analiz kapsamı</strong>
            <span>CSV, XLSX ve TXT tablo verileri için önerilir. Güvenli yükleme sınırı: maks. 20 MB.</span>
          </div>
        </aside>

        <div
          className={`dropzone ${isDragging ? 'drag-active' : ''} ${file ? 'has-file' : ''} ${!canUpload ? 'dropzone-disabled' : ''}`}
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
            accept=".csv,.xlsx,.txt"
            disabled={!canUpload}
          />
          <label
            htmlFor={canUpload ? 'file-upload' : undefined}
            className="dropzone-label"
            onClick={(event) => {
              if (!canUpload) {
                event.preventDefault();
                onNeedAuth?.();
              }
            }}
            onKeyDown={(event) => {
              if (!canUpload && (event.key === 'Enter' || event.key === ' ')) {
                event.preventDefault();
                onNeedAuth?.();
              }
            }}
            role={canUpload ? undefined : 'button'}
            tabIndex={canUpload ? undefined : 0}
          >
            {!file ? (
              <>
                <span className="dropzone-icon"><UploadCloud size={34} aria-hidden /></span>
                <span className="dropzone-kicker">Dosya yükleme</span>
                <h4>Dosyayı buraya bırakın</h4>
                <p>veya bilgisayarınızdan seçmek için tıklayın</p>
                <span className="dropzone-button">{canUpload ? 'Dosya seç' : 'Giriş yap'}</span>
                <div className="file-constraints">
                  <span>CSV</span><span>XLSX</span><span>TXT</span><small>Maks. 20 MB</small>
                </div>
              </>
            ) : (
              <div className="selected-file">
                <span className="selected-file-status"><CheckCircle2 size={19} /> Dosya alındı</span>
                <span className="selected-file-icon"><FileSpreadsheet size={36} /></span>
                <h4>{file.name}</h4>
                <p>{(file.size / (1024 * 1024)).toFixed(2)} MB · Analiz için hazırlanıyor</p>
                <span className="change-file-hint">Farklı dosya seçmek için tıklayın</span>
              </div>
            )}
          </label>
        </div>
      </div>
    </section>
  );
};

export default FileUpload;
