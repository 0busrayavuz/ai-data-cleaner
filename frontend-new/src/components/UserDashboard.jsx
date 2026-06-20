import { useEffect, useState, useCallback } from 'react';
import { Activity, Database, Clock, Download, FileSearch, FileSpreadsheet, History, Plus, RefreshCw, Trash2, FolderPlus } from 'lucide-react';
import { fetchMyDatasets, downloadCleanedDataset, downloadAuditExport, fetchProjectTimeline, downloadQualityReport, deleteDataset, deleteProject, createProject } from '../services/api';
import './UserDashboard.css';

const UserDashboard = ({ userEmail, onNewAnalysis, onOpenDataset, onProjectsChanged }) => {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [filterProjectId, setFilterProjectId] = useState('');
  const [timeline, setTimeline] = useState(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const pid = filterProjectId === '' ? null : Number(filterProjectId);
      const data = await fetchMyDatasets(pid);
      setPayload(data);
      setError('');
    } catch (e) {
      setError(e.message || 'Veriler yüklenemedi.');
    } finally {
      setLoading(false);
    }
  }, [filterProjectId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDeleteDataset = async (id) => {
    if (!window.confirm('Bu veri setini silmek istediğinize emin misiniz?')) return;
    try {
      await deleteDataset(id);
      load();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleDeleteProject = async () => {
    if (!filterProjectId) return;
    if (!window.confirm('Bu projeyi silmek istediğinize emin misiniz? İçindeki veri setleri projesiz kalacaktır.')) return;
    try {
      await deleteProject(filterProjectId);
      setFilterProjectId('');
      load();
      onProjectsChanged?.();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleCreateProject = async () => {
    const name = window.prompt('Yeni proje adı:');
    if (!name || !name.trim()) return;
    try {
      const p = await createProject(name);
      setFilterProjectId(p.id);
      load();
      onProjectsChanged?.();
    } catch (e) {
      alert(e.message);
    }
  };

  useEffect(() => {
    if (!filterProjectId) {
      setTimeline(null);
      setTimelineError('');
      return;
    }
    let cancelled = false;
    setTimelineLoading(true);
    setTimelineError('');
    fetchProjectTimeline(Number(filterProjectId))
      .then((t) => {
        if (!cancelled) setTimeline(t);
      })
      .catch((e) => {
        if (!cancelled) setTimelineError(e.message || 'Zaman çizelgesi yüklenemedi.');
      })
      .finally(() => {
        if (!cancelled) setTimelineLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [filterProjectId]);

  const rows = payload?.datasets ?? [];
  const stats = payload?.stats ?? { total_rows_processed: 0, dataset_count: 0, cleaned_dataset_count: 0 };
  const projects = payload?.projects ?? [];

  const formatDate = (iso) => {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return '—';
      return d.toLocaleString('tr-TR');
    } catch {
      return iso;
    }
  };

  const formatNum = (value) => {
    if (value == null) return '0';
    const num = Number(value);
    if (Number.isNaN(num) || !Number.isFinite(num)) return '0';
    return num.toLocaleString('tr-TR');
  };

  const handleDownload = async (row) => {
    const stem = (row.original_filename || 'veri').replace(/\.[^/.]+$/, '');
    await downloadCleanedDataset(row.id, `cleaned_${stem}.csv`);
  };

  const handleAuditExport = async (row) => {
    await downloadAuditExport(row.id);
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div>
          <span className="dashboard-overline">Panel</span>
          <h2>Çalışma paneli</h2>
          <p className="dashboard-subtitle">
            Projelerinizi, veri setlerinizi ve işlem geçmişinizi tek noktadan yönetin.
          </p>
          {userEmail && <span className="dashboard-user">{userEmail}</span>}
        </div>
        <button type="button" className="btn-primary dashboard-new-analysis" onClick={onNewAnalysis}>
          <Plus size={18} aria-hidden /> Yeni analiz
        </button>
      </header>

      {error && (
        <p className="status-msg error" style={{ marginBottom: '1rem' }}>{error}</p>
      )}

      <div className="dashboard-filters glass-panel" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <label htmlFor="dash-project-filter" className="filter-label">
          Projeye göre filtrele
        </label>
        <select
          id="dash-project-filter"
          className="dashboard-project-select"
          value={filterProjectId}
          onChange={(e) => setFilterProjectId(e.target.value)}
        >
          <option value="">Tüm veri setleri</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
        <button type="button" className="action-btn icon-only" onClick={handleCreateProject} title="Yeni proje oluştur">
          <FolderPlus size={18} />
        </button>
        {filterProjectId && (
          <button type="button" className="action-btn icon-only danger" onClick={handleDeleteProject} title="Projeyi sil">
            <Trash2 size={18} />
          </button>
        )}
      </div>

      {filterProjectId && (
        <section className="timeline-section glass-panel">
          <div className="history-header">
            <h3><History size={20} style={{ verticalAlign: 'text-bottom', marginRight: 8 }} />Proje zaman çizelgesi</h3>
          </div>
          {timelineLoading && <p className="dashboard-subtitle">Yükleniyor…</p>}
          {timelineError && <p className="status-msg error">{timelineError}</p>}
          {!timelineLoading && timeline && timeline.events.length === 0 && (
            <p className="dashboard-subtitle">Bu projede henüz kayıtlı işlem yok.</p>
          )}
          {!timelineLoading && timeline && timeline.events.length > 0 && (
            <ul className="timeline-list">
              {timeline.events.map((ev, idx) => (
                <li key={`${ev.type}-${ev.at}-${idx}`} className={`timeline-item timeline-${ev.type}`}>
                  <span className="timeline-time">{formatDate(ev.at)}</span>
                  {ev.type === 'operation' && (
                    <span className="timeline-body">
                      <strong>{ev.dataset_file || `#${ev.dataset_id}`}</strong>
                      {' · '}{ev.module} / {ev.column} — <code>{ev.method}</code>
                    </span>
                  )}
                  {ev.type === 'quality_report' && (
                    <span className="timeline-body">
                      <strong>{ev.dataset_file || `#${ev.dataset_id}`}</strong>
                      {' · '}Kalite: eksik {ev.before_missing_pct}% → {ev.after_missing_pct}%
                      {ev.id && (
                        <span style={{ marginLeft: 12 }}>
                          <button
                            type="button"
                            className="text-btn highlight"
                            style={{ padding: '2px 8px', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: 4 }}
                            onClick={() => downloadQualityReport(ev.dataset_id, 'html', ev.id)}
                          >
                            <Download size={12} /> HTML Raporu
                          </button>
                          <button
                            type="button"
                            className="text-btn highlight"
                            style={{ padding: '2px 8px', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: 4, marginLeft: 6 }}
                            onClick={() => downloadQualityReport(ev.dataset_id, 'pdf', ev.id)}
                          >
                            <Download size={12} /> PDF Raporu
                          </button>
                        </span>
                      )}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {loading ? (
        <p className="dashboard-subtitle">Yükleniyor…</p>
      ) : (
        <>


          <section className="dashboard-history">
            <div className="history-header">
              <h3>Geçmiş yüklemeler</h3>
              <button type="button" className="text-btn highlight" onClick={load}>
                <RefreshCw size={15} /> Yenile
              </button>
            </div>

            <div className="history-table-container glass-panel">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Proje</th>
                    <th>Dosya adı</th>
                    <th>Tarih</th>
                    <th>Satır sayısı</th>
                    <th>Durum</th>
                    <th>İşlemler</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.length > 0 ? (
                    rows.map((item) => (
                      <tr key={item.id}>
                        <td>{item.project_name || '—'}</td>
                        <td className="file-name">
                          <Database size={16} className="file-icon" />
                          {item.original_filename}
                        </td>
                        <td>{formatDate(item.upload_time)}</td>
                        <td>{item.row_count != null ? formatNum(item.row_count) : '—'}</td>
                        <td>
                          {(() => {
                            const s = item.status;
                            // Active states always win — even if a previous run left cleaned_ready=true
                            if (s === 'processing')
                              return <span className="status-badge info"><i />İşleniyor</span>;
                            if (s === 'analyzing')
                              return <span className="status-badge info"><i />Analiz ediliyor</span>;
                            if (s === 'error')
                              return <span className="status-badge danger"><i />Hata</span>;
                            if (s === 'cleaned' || item.cleaned_ready)
                              return <span className="status-badge success"><i />Temizlendi</span>;
                            return <span className="status-badge warning"><i />Bekliyor</span>;
                          })()}
                        </td>
                        <td className="dashboard-actions-cell">
                          <button
                            type="button"
                            className="action-btn audit"
                            onClick={() => onOpenDataset?.(item.id)}
                          >
                            <FileSearch size={16} /> İncele
                          </button>
                          {/* Show download only when current status is genuinely cleaned */}
                          {(item.status === 'cleaned' || (item.cleaned_ready && item.status !== 'processing' && item.status !== 'analyzing' && item.status !== 'error')) && (
                            <button type="button" className="action-btn download" onClick={() => handleDownload(item)}>
                              <Download size={16} /> Temiz veriyi indir
                            </button>
                          )}
                          <button
                            type="button"
                            className="action-btn audit"
                            onClick={() => handleAuditExport(item)}
                            title="İşlem ve kalite günlüğünü CSV olarak indir"
                          >
                            <FileSpreadsheet size={16} /> Denetim
                          </button>
                          <button
                            type="button"
                            className="action-btn icon-only danger"
                            onClick={() => handleDeleteDataset(item.id)}
                            title="Veri setini sil"
                            style={{ marginLeft: 'auto' }}
                          >
                            <Trash2 size={16} />
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                        Bu filtrede veri seti yok. Ana sayfadan dosya yükleyin veya projeyi değiştirin.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default UserDashboard;
