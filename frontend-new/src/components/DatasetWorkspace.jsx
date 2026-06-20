import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Columns3,
  Database,
  FileSearch,
  GitCompareArrows,
  Rows3,
  Sparkles,
  TableProperties,
  TriangleAlert,
  WandSparkles,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import AnalysisResults from './AnalysisResults';
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
    eyebrow: 'Veriyi tanı',
    title: 'Veri Profili',
    description: 'Sütun yapısını, eksik oranlarını, dağılımları ve ilişkileri inceleyin.',
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

const numberFormat = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 });

/* ── AnimatedCounter ─────────────────────────────────────────────────────── */
function AnimatedCounter({ value, duration = 900 }) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef(null);

  useEffect(() => {
    const target = Number(value) || 0;
    const start = Date.now();
    const startVal = 0;

    const tick = () => {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(startVal + (target - startVal) * eased);
      setDisplay(current);
      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [value, duration]);

  return <>{numberFormat.format(display)}</>;
}

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

function formatValue(value) {
  if (value == null || value === '') return '—';
  if (typeof value === 'number') {
    if (Number.isNaN(value) || !Number.isFinite(value)) return '—';
    return numberFormat.format(value);
  }
  return String(value);
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

/* ── ProfileView ─────────────────────────────────────────────────────────── */
function ProfileView({ profile, selectedColumn, onSelectColumn }) {
  const column = profile.columns.find((item) => item.name === selectedColumn) || profile.columns[0];
  const chartData = column?.kind === 'numeric' ? column.distribution : column?.top_values;
  const chartTitle = column?.kind === 'numeric' ? 'Değer dağılımı' : 'En sık değerler';

  return (
    <div className="workspace-profile">
      <section className="workspace-metrics">
        <MetricCard icon={Rows3} label="Satır" value={profile.row_count} tone="emerald" animate />
        <MetricCard icon={Columns3} label="Sütun" value={profile.col_count} tone="blue" animate />
        <MetricCard icon={TriangleAlert} label="Eksik hücre" value={profile.missing_cells} tone="amber" animate />
        <MetricCard icon={TableProperties} label="Tekrar eden satır" value={profile.duplicate_rows} tone="purple" animate />
      </section>

      <section className="workspace-profile-grid">
        <div className="workspace-column-list glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>Sütun kataloğu</span>
              <h3>{profile.columns.length} değişken</h3>
            </div>
          </div>
          <div className="workspace-column-scroll">
            {profile.columns.map((item) => (
              <button
                key={item.name}
                type="button"
                className={item.name === column?.name ? 'active' : ''}
                onClick={() => onSelectColumn(item.name)}
              >
                <span>
                  <strong>{item.name}</strong>
                  <small>{item.dtype}</small>
                </span>
                <span className={`workspace-kind ${item.kind}`}>
                  {item.kind === 'numeric' ? 'Sayısal' : 'Kategorik'}
                </span>
                <i style={{ '--complete': `${100 - item.missing_pct}%` }} />
                <small>%{numberFormat.format(item.missing_pct)} eksik</small>
              </button>
            ))}
          </div>
        </div>

        <div className="workspace-column-detail glass-panel">
          {column && (
            <>
              <div className="workspace-panel-heading">
                <div>
                  <span>Seçili sütun</span>
                  <h3>{column.name}</h3>
                </div>
                <span className={`workspace-kind ${column.kind}`}>
                  {column.kind === 'numeric' ? 'Sayısal' : 'Kategorik'}
                </span>
              </div>
              <div className="workspace-detail-stats">
                <div><span>Eksik</span><strong>{formatValue(column.missing_count)}</strong></div>
                <div><span>Benzersiz</span><strong>{formatValue(column.unique_count)}</strong></div>
                {column.kind === 'numeric' && (
                  <>
                    <div><span>Ortalama</span><strong>{formatValue(column.stats?.mean)}</strong></div>
                    <div><span>Medyan</span><strong>{formatValue(column.stats?.median)}</strong></div>
                    <div><span>Minimum</span><strong>{formatValue(column.stats?.min)}</strong></div>
                    <div><span>Maksimum</span><strong>{formatValue(column.stats?.max)}</strong></div>
                  </>
                )}
              </div>
              <div className="workspace-chart-block">
                <h4>{chartTitle}</h4>
                {chartData?.length ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={chartData} margin={{ top: 12, right: 8, left: -15, bottom: 48 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(11, 26, 56, 0.08)" />
                      <XAxis dataKey="label" angle={-28} textAnchor="end" interval={0} tick={{ fontSize: 11 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{
                          borderRadius: 10,
                          border: '1px solid rgba(12,143,114,0.2)',
                          background: 'rgba(255,255,255,0.97)',
                          fontSize: 12,
                        }}
                      />
                      <Bar dataKey="count" fill="#00aeef" radius={[7, 7, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="workspace-muted">Bu sütun için çizilebilir veri yok.</p>
                )}
              </div>
            </>
          )}
        </div>
      </section>

      <section className="workspace-lower-grid">
        <div className="workspace-correlation glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>İlişki analizi</span>
              <h3>En güçlü korelasyonlar</h3>
            </div>
            <Activity size={20} color="#00aeef" />
          </div>
          {profile.correlations.length > 0 ? (
            <div className="workspace-correlation-list">
              {profile.correlations.slice(0, 8).map((item) => (
                <div key={`${item.left}-${item.right}`}>
                  <span>{item.left} <ArrowRight size={13} /> {item.right}</span>
                  <strong className={item.value < 0 ? 'negative' : ''}>{item.value}</strong>
                  <i style={{ '--strength': `${Math.abs(item.value) * 100}%` }} />
                </div>
              ))}
            </div>
          ) : (
            <p className="workspace-muted">Korelasyon için en az iki sayısal sütun gerekir.</p>
          )}
        </div>
        <PreviewTable title="Ham veri ön izlemesi" rows={profile.preview} />
      </section>
    </div>
  );
}

/* ── ComparisonView ──────────────────────────────────────────────────────── */
function ComparisonView({ comparison, onOpenStudio }) {
  if (!comparison) {
    return (
      <section className="workspace-empty glass-panel">
        <GitCompareArrows size={36} />
        <h3>Karşılaştırma henüz hazır değil</h3>
        <p>Önce Temizlik Stüdyosu'nda en az bir işlem uygulayın. Ham veri değiştirilmeden korunacaktır.</p>
        <button type="button" className="btn-primary" onClick={onOpenStudio}>
          Temizlik Stüdyosu'na git <ArrowRight size={17} />
        </button>
      </section>
    );
  }

  const healthChart = [
    { name: 'Eksik', before: comparison.health.before.missing, after: comparison.health.after.missing },
    { name: 'Aykırı', before: comparison.health.before.outliers, after: comparison.health.after.outliers },
    { name: 'Format', before: comparison.health.before.format, after: comparison.health.after.format },
  ];
  const improvement = comparison.health.after_score - comparison.health.before_score;
  const improvementText =
    improvement > 0
      ? `+${formatValue(improvement)} puan gelişim`
      : improvement < 0
      ? `${formatValue(improvement)} puan düşüş`
      : '0 puan değişim';

  return (
    <div className="workspace-comparison">
      <section className="comparison-score-grid">
        <div className="comparison-score before glass-panel">
          <span>İşlem öncesi</span>
          <strong>%{formatValue(comparison.health.before_score)}</strong>
          <small>Başlangıç kalite puanı</small>
        </div>
        <div className="comparison-arrow"><ArrowRight size={25} /></div>
        <div className="comparison-score after glass-panel">
          <span>İşlem sonrası</span>
          <strong>%{formatValue(comparison.health.after_score)}</strong>
          <small>{improvementText}</small>
        </div>
        <div className="comparison-score changes glass-panel">
          <span>Değişen hücre</span>
          <strong>
            {comparison.total_changed_cells == null ? '—' : formatValue(comparison.total_changed_cells)}
          </strong>
          <small>
            {comparison.rows_aligned
              ? 'Satırlar aynı konumda karşılaştırıldı'
              : 'Satır silindiği için hücre bazında sayılmadı'}
          </small>
        </div>
      </section>

      <section className="comparison-health-note glass-panel">
        <div>
          <span><Activity size={18} /> Sağlık skoru nasıl okunur?</span>
          <p>
            Skor, toplam hücre sayısına göre eksik veri, format problemi ve aykırı değerlerin ağırlıklı
            cezası çıkarılarak hesaplanır. Aykırı değerler hata olmak zorunda olmadığı için daha düşük
            ağırlıkla değerlendirilir. Satır silme varsa ayrıca her %1 silme için 0.5 puan ceza uygulanır.
          </p>
        </div>
        <div className="comparison-weight-list" aria-label="Health score ağırlıkları">
          <span>Eksik veri x{comparison.weights.missing}</span>
          <span>Format x{comparison.weights.format}</span>
          <span>Aykırı değer x{comparison.weights.outlier}</span>
          {comparison.health.row_delete_penalty > 0 && (
            <span>Satır silme -{formatValue(comparison.health.row_delete_penalty)} puan</span>
          )}
        </div>
      </section>

      <section className="comparison-main-grid">
        <div className="comparison-chart glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>Kalite bileşenleri</span>
              <h3>Sorun sayısı değişimi</h3>
            </div>
            <BarChart3 size={20} color="#00aeef" />
          </div>
          <ResponsiveContainer width="100%" height={310}>
            <BarChart data={healthChart} margin={{ top: 18, right: 12, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(11, 26, 56, 0.08)" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  borderRadius: 10,
                  border: '1px solid rgba(12,143,114,0.15)',
                  background: 'rgba(255,255,255,0.97)',
                  fontSize: 12,
                }}
              />
              <Bar dataKey="before" name="Önce" fill="#e07a5f" radius={[6, 6, 0, 0]} />
              <Bar dataKey="after"  name="Sonra" fill="#00aeef" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <p className="comparison-method-note">
            Aykırı değerler önce ve sonra aynı başlangıç IQR sınırlarına göre ölçülür.
            Ağırlıklar: eksik {comparison.weights.missing}, format {comparison.weights.format},
            aykırı {comparison.weights.outlier}.
          </p>
        </div>

        <div className="comparison-structure glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>Yapısal etki</span>
              <h3>Tablo boyutu</h3>
            </div>
            <TableProperties size={20} color="#00aeef" />
          </div>
          <div className="comparison-structure-row">
            <span>Satır</span>
            <strong>{formatValue(comparison.before_rows)}</strong>
            <ArrowRight size={15} />
            <strong>{formatValue(comparison.after_rows)}</strong>
          </div>
          <div className="comparison-structure-row">
            <span>Sütun</span>
            <strong>{formatValue(comparison.before_columns)}</strong>
            <ArrowRight size={15} />
            <strong>{formatValue(comparison.after_columns)}</strong>
          </div>
          <div className="comparison-structure-callout">
            <CheckCircle2 size={20} />
            <p>Ham dosya korunur; temizlenmiş veri ayrı bir çıktı olarak oluşturulur.</p>
          </div>
        </div>
      </section>

      <section className="comparison-table-card glass-panel">
        <div className="workspace-panel-heading">
          <div>
            <span>Sütun etkisi</span>
            <h3>Önce / sonra istatistikleri</h3>
          </div>
        </div>
        <div className="workspace-table-scroll">
          <table className="workspace-data-table">
            <thead>
              <tr>
                <th>Sütun</th><th>Tür</th>
                <th>Eksik (önce)</th><th>Eksik (sonra)</th>
                <th>Ortalama (önce)</th><th>Ortalama (sonra)</th>
                <th>Değişen hücre</th>
              </tr>
            </thead>
            <tbody>
              {comparison.columns.map((column) => (
                <tr key={column.name}>
                  <td><strong>{column.name}</strong></td>
                  <td>
                    <span className={`workspace-kind ${column.kind}`}>
                      {column.kind === 'numeric' ? 'Sayısal' : 'Kategorik'}
                    </span>
                  </td>
                  <td>{formatValue(column.before_missing)}</td>
                  <td>{formatValue(column.after_missing)}</td>
                  <td>{formatValue(column.before_mean)}</td>
                  <td>{formatValue(column.after_mean)}</td>
                  <td>{column.changed_cells == null ? '—' : formatValue(column.changed_cells)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {comparison.changed_samples.length > 0 && (
        <section className="comparison-table-card glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>Değişiklik örnekleri</span>
              <h3>İlk {comparison.changed_samples.length} değişiklik</h3>
            </div>
          </div>
          <div className="workspace-table-scroll">
            <table className="workspace-data-table">
              <thead>
                <tr><th>Satır</th><th>Sütun</th><th>Önce</th><th>Sonra</th></tr>
              </thead>
              <tbody>
                {comparison.changed_samples.map((item, index) => (
                  <tr key={`${item.row}-${item.column}-${index}`}>
                    <td>{item.row}</td>
                    <td><strong>{item.column}</strong></td>
                    <td className="comparison-old">{formatValue(item.before)}</td>
                    <td className="comparison-new">{formatValue(item.after)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

/* ── MetricCard ──────────────────────────────────────────────────────────── */
function MetricCard({ icon: Icon, label, value, tone, animate = false }) {
  return (
    <div className={`workspace-metric glass-panel ${tone}`}>
      <span><Icon size={21} /></span>
      <div>
        <small>{label}</small>
        <strong>
          {animate ? <AnimatedCounter value={value} /> : formatValue(value)}
        </strong>
      </div>
    </div>
  );
}

/* ── PreviewTable ────────────────────────────────────────────────────────── */
function PreviewTable({ title, rows }) {
  const columns = useMemo(() => Object.keys(rows?.[0] || {}), [rows]);
  return (
    <div className="workspace-preview glass-panel">
      <div className="workspace-panel-heading">
        <div><span>İlk kayıtlar</span><h3>{title}</h3></div>
        <Database size={20} color="#00aeef" />
      </div>
      {rows?.length ? (
        <div className="workspace-table-scroll">
          <table className="workspace-data-table compact">
            <thead>
              <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => <td key={column}>{formatValue(row[column])}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="workspace-muted">Ön izleme için kayıt yok.</p>
      )}
    </div>
  );
}

export default DatasetWorkspace;
