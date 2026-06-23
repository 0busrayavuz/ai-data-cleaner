import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  Database,
  FileSearch,
  GitCompareArrows,
  Sparkles,
  TriangleAlert,
  WandSparkles,
} from 'lucide-react';
import AnalysisResults from './workspace/AnalysisResults';
import ProfileView from './workspace/ProfileView';
import ComparisonView from './workspace/ComparisonView';
import { formatValue } from './workspace/utils';
import {
  analyzeData,
  applyClean,
  fetchDatasetWorkspace,
  fetchMyDatasets,
  getDatasetStatus,
} from '../services/api';
import './DatasetWorkspace.css';

const VIEW_META = {
  profile: {
    eyebrow: 'Ham veri ön izlemesi',
    title: 'Orijinal Veri Profili',
    description: 'Yüklediğiniz ham (işlem öncesi) verinin sütun yapısını, orijinal eksik oranlarını ve dağılımlarını inceleyin.',
    icon: FileSearch,
  },
  studio: {
    eyebrow: 'Karar ve uygulama',
    title: 'Temizlik Stüdyosu',
    description: 'Sorunları yöntemleriyle birlikte değerlendirin ve kontrollü biçimde uygulayın.',
    icon: WandSparkles,
  },
  comparison: {
    eyebrow: 'Etki analizi',
    title: 'Önce / Sonra',
    description: 'Temizliğin veri kalitesi ve sütun istatistikleri üzerindeki etkisini görün.',
    icon: GitCompareArrows,
  },
};

const VIEW_TABS = [
  { id: 'profile', label: 'Veri Profili', icon: FileSearch },
  { id: 'studio', label: 'Temizlik Stüdyosu', icon: WandSparkles },
  { id: 'comparison', label: 'Önce / Sonra', icon: GitCompareArrows },
];

const DATASET_STATUS_LABELS = {
  uploaded: 'Yüklendi',
  analyzing: 'Analiz ediliyor',
  ready: 'Analiz hazır',
  processing: 'Temizleniyor',
  cleaned: 'Temizlendi',
  error: 'Hata',
};



/* ── Helpers ─────────────────────────────────────────────────────────────── */
function getWorkspaceSourceInfo(view, workspace) {
  if (view === 'studio') {
    return {
      title: 'Kaynak: ham veri analizi',
      description:
        'Öneriler yüklenen ham dosya üzerinden gerçek analiz sonucu üretilir; kullanıcı onayı olmadan veri değiştirilmez.',
    };
  }
  if (view === 'comparison') {
    return workspace?.comparison
      ? {
          title: 'Kaynak: ham veri + son temizlenmiş çıktı',
          description:
            'Karşılaştırma, yüklenen ham dosya ile diskteki son temizlenmiş CSV çıktısından hesaplanır.',
        }
      : {
          title: 'Kaynak bekleniyor',
          description:
            "Karşılaştırma ekranı için önce Temizlik Stüdyosu'nda en az bir işlem uygulanmalıdır.",
        };
  }
  return {
    title: 'Kaynak: yüklenen ham dosya',
    description:
      'Profil metrikleri, dağılımlar ve ön izleme doğrudan yüklenen orijinal veri setinden hesaplanır.',
  };
}



function formatDatasetStatus(status) {
  return DATASET_STATUS_LABELS[status] || status || 'Bilinmiyor';
}

/* ── Loading dots ────────────────────────────────────────────────────────── */
function LoadingDots({ label }) {
  return (
    <div className="workspace-loading glass-panel">
      <div className="workspace-loading-dots">
        <span /><span /><span />
      </div>
      <span>{label}</span>
    </div>
  );
}

/* ── Main component ──────────────────────────────────────────────────────── */
function DatasetWorkspace({
  view,
  selectedDatasetId,
  onDatasetChange,
  onNavigate,
  templates = [],
  onTemplatesChanged,
}) {
  const [datasets, setDatasets] = useState([]);
  const [workspace, setWorkspace] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedColumn, setSelectedColumn] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchMyDatasets()
      .then((payload) => {
        if (cancelled) return;
        const rows = payload.datasets || [];
        setDatasets(rows);
        const selectedExists = rows.some((row) => row.id === Number(selectedDatasetId));
        if (!selectedExists && rows.length > 0) {
          onDatasetChange(rows[0].id);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Veri setleri yüklenemedi.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [onDatasetChange, refreshKey, selectedDatasetId]);

  useEffect(() => {
    if (!selectedDatasetId) { setWorkspace(null); return; }
    let cancelled = false;
    setLoading(true);
    setError('');
    fetchDatasetWorkspace(selectedDatasetId)
      .then((payload) => {
        if (cancelled) return;
        setWorkspace(payload);
        const firstColumn = payload.profile?.columns?.[0]?.name || '';
        setSelectedColumn((current) =>
          payload.profile?.columns?.some((column) => column.name === current)
            ? current
            : firstColumn,
        );
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Çalışma alanı yüklenemedi.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [selectedDatasetId, refreshKey]);

  useEffect(() => {
    if (view !== 'studio' || !selectedDatasetId) return undefined;
    let cancelled = false;

    const loadAnalysis = async () => {
      setAnalysisLoading(true);
      setError('');
      try {
        let result = await analyzeData(selectedDatasetId);
        const deadline = Date.now() + 120_000;
        while (result.status === 'analyzing' && Date.now() < deadline) {
          await new Promise((resolve) => setTimeout(resolve, 1200));
          const status = await getDatasetStatus(selectedDatasetId);
          if (status.status === 'error') throw new Error('Analiz tamamlanamadı.');
          if (status.status === 'ready' || status.status === 'cleaned') {
            result = await analyzeData(selectedDatasetId);
          }
        }
        if (result.status === 'analyzing') throw new Error('Analiz zaman aşımına uğradı.');
        if (!cancelled) setRecommendations(result.recommendations?.recommendations || []);
      } catch (err) {
        if (!cancelled) setError(err.message || 'Analiz önerileri yüklenemedi.');
      } finally {
        if (!cancelled) setAnalysisLoading(false);
      }
    };

    loadAnalysis();
    return () => { cancelled = true; };
  }, [selectedDatasetId, view]);

  const selectedDataset = datasets.find((row) => row.id === Number(selectedDatasetId));
  const meta = VIEW_META[view] || VIEW_META.profile;
  const HeaderIcon = meta.icon;
  const sourceInfo = workspace ? getWorkspaceSourceInfo(view, workspace) : null;

  const handleApply = (selections) => applyClean(selectedDatasetId, selections);
  const handleApplied = () => { setRefreshKey((key) => key + 1); };

  if (!loading && datasets.length === 0) {
    return (
      <section className="workspace-empty glass-panel">
        <Database size={34} aria-hidden />
        <h2>Henüz veri seti yok</h2>
        <p>Bu ekranları kullanmak için önce ana sayfadan CSV, XLSX veya TXT dosyası yükleyin.</p>
        <button type="button" className="btn-primary" onClick={() => onNavigate('home')}>
          Dosya yüklemeye git <ArrowRight size={17} />
        </button>
      </section>
    );
  }

  return (
    <div className={`workspace-page view-${view}`}>
      {/* ── Hero ── */}
      <header className="workspace-hero">
        <div className="workspace-heading">
          <span className="workspace-icon"><HeaderIcon size={24} /></span>
          <div>
            <span className="workspace-eyebrow">{meta.eyebrow}</span>
            <h2>{meta.title}</h2>
            <p>{meta.description}</p>
          </div>
        </div>

        <div className="workspace-dataset-picker">
          <label htmlFor="workspace-dataset">Aktif veri seti</label>
          <select
            id="workspace-dataset"
            value={selectedDatasetId || ''}
            onChange={(event) => onDatasetChange(Number(event.target.value))}
          >
            {datasets.map((row) => (
              <option key={row.id} value={row.id}>
                #{row.id} · {row.original_filename}
              </option>
            ))}
          </select>
          {selectedDataset && (
            <span>
              {formatValue(selectedDataset.row_count)} satır · {formatValue(selectedDataset.col_count)} sütun
            </span>
          )}
        </div>
      </header>

      {/* ── Tabs ── */}
      <nav className="workspace-tabs" aria-label="Veri çalışma ekranları">
        {VIEW_TABS.map((tab) => {
          const TabIcon = tab.icon;
          return (
            <button
              key={tab.id}
              type="button"
              data-tab={tab.id}
              className={view === tab.id ? 'active' : ''}
              onClick={() => onNavigate(tab.id)}
            >
              <TabIcon size={17} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* ── Source strip ── */}
      {!loading && workspace && sourceInfo && (
        <section className="workspace-source-strip glass-panel">
          <div>
            <Database size={18} />
            <span>
              <strong>{sourceInfo.title}</strong>
              <small>{sourceInfo.description}</small>
            </span>
          </div>
          <em>Durum: {formatDatasetStatus(workspace.dataset.status)}</em>
        </section>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="workspace-alert error">
          <TriangleAlert size={19} />
          <span>{error}</span>
        </div>
      )}

      {/* ── Loading ── */}
      {loading && <LoadingDots label="Veri seti hazırlanıyor…" />}

      {/* ── Profile view ── */}
      {!loading && workspace && view === 'profile' && (
        <ProfileView
          profile={workspace.profile}
          selectedColumn={selectedColumn}
          onSelectColumn={setSelectedColumn}
        />
      )}

      {/* ── Studio view ── */}
      {!loading && workspace && view === 'studio' && (
        <section className="workspace-studio">
          <div className="workspace-context-strip">
            <div>
              <Sparkles size={18} color="#00aeef" />
              <span>
                <strong>{recommendations.length}</strong>
                <small style={{ display: 'inline', marginLeft: '0.35rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  karar önerisi
                </small>
              </span>
            </div>
            <p>Öneriler gerçek analizden gelir; yöntemler otomatik uygulanmaz, son karar kullanıcıya aittir.</p>
          </div>

          {analysisLoading ? (
            <LoadingDots label="Kalite sorunları ve yöntemler hazırlanıyor…" />
          ) : recommendations.length > 0 ? (
            <AnalysisResults
              key={`${selectedDatasetId}-${refreshKey}`}
              recommendations={recommendations}
              datasetId={selectedDatasetId}
              originalFilename={workspace.dataset.filename}
              onApply={handleApply}
              templates={templates}
              onTemplatesChanged={onTemplatesChanged}
              initiallyOpen
              onApplied={handleApplied}
            />
          ) : (
            <div className="workspace-empty glass-panel">
              <CheckCircle2 size={38} />
              <h3>Uygulanacak öneri bulunamadı</h3>
              <p>Analiz bu veri setinde zorunlu bir temizleme önerisi üretmedi.</p>
            </div>
          )}
        </section>
      )}

      {/* ── Comparison view ── */}
      {!loading && workspace && view === 'comparison' && (
        <ComparisonView
          comparison={workspace.comparison}
          onOpenStudio={() => onNavigate('studio')}
        />
      )}
    </div>
  );
}



export default DatasetWorkspace;
