import React, { useState, useEffect, useRef } from 'react';
import {
  CheckCircle,
  AlertCircle,
  Download,
  ChevronDown,
  ChevronRight,
  Check,
  BookmarkPlus,
  Wand2,
  AlertTriangle,
  FileCode2,
  Cpu,
} from 'lucide-react';
import './AnalysisResults.css';
import {
  downloadCleanedDataset,
  saveTemplate,
  applyTemplateToDataset,
  downloadQualityReport,
  getDatasetStatus,
} from '../services/api';

/* ── Category meta ───────────────────────────────────────────────────────── */

const FORMAT_DEFAULTS = {
  numeric_as_string: 'to_numeric',
  date_as_string: 'to_datetime',
  whitespace: 'strip_whitespace',
  case_inconsistency: 'normalize_case',
  fuzzy_duplicates: 'semantic_merge',
};

const CATEGORY_LABELS = {
  missing: 'Eksik veri',
  outlier: 'Aykırı değer',
  format: 'Format',
  feature: 'Özellik',
};

const CATEGORY_ICONS = {
  missing: AlertCircle,
  outlier: AlertTriangle,
  format: FileCode2,
  feature: Cpu,
};

/* ── FloatingActionBar ───────────────────────────────────────────────────── */

function FloatingActionBar({ selectedCount, totalCount, onApply, loading, applied }) {
  const visible = !applied && selectedCount > 0;

  return (
    <div className={`studio-fab ${visible ? 'visible' : ''}`} role="status" aria-live="polite">
      <div className="studio-fab-info">
        <div className="studio-fab-count">{selectedCount} / {totalCount}</div>
        <div className="studio-fab-label">
          {selectedCount === 1 ? 'işlem seçildi' : 'işlem seçildi'}
        </div>
      </div>
      <button
        type="button"
        className="studio-fab-apply"
        onClick={onApply}
        disabled={loading || selectedCount === 0}
      >
        {loading ? 'Uygulanıyor…' : 'Seçilenleri Uygula →'}
      </button>
      {loading && (
        <div className="studio-fab-progress">
          <div className="studio-fab-progress-bar" />
        </div>
      )}
    </div>
  );
}

/* ── CategoryChips ───────────────────────────────────────────────────────── */

function CategoryChips({ categoryCount }) {
  return (
    <div className="studio-stats-bar">
      {Object.entries(categoryCount).map(([cat, count]) => {
        const CatIcon = CATEGORY_ICONS[cat] || AlertCircle;
        return (
          <span key={cat} className={`studio-stat-chip chip-${cat}`}>
            <CatIcon size={14} />
            <b>{count}</b>
            {CATEGORY_LABELS[cat] || cat}
          </span>
        );
      })}
    </div>
  );
}

/* ── Main component ──────────────────────────────────────────────────────── */

const AnalysisResults = ({
  recommendations,
  datasetId,
  originalFilename,
  onApply,
  templates = [],
  onTemplatesChanged,
  initiallyOpen = false,
  onApplied,
}) => {
  const [loading, setLoading] = useState(false);
  const [applied, setApplied] = useState(false);
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [showList, setShowList] = useState(initiallyOpen);
  const [downloadError, setDownloadError] = useState('');
  const [templateName, setTemplateName] = useState('');
  const [templateMsg, setTemplateMsg] = useState('');
  const [templateBusy, setTemplateBusy] = useState(false);
  const [pickTemplateId, setPickTemplateId] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [selectedMethods, setSelectedMethods] = useState({});

  /* Filename helpers */
  const downloadFilename = () => {
    const base = originalFilename || `veri_${datasetId}`;
    const stem = base.replace(/\.[^/.]+$/, '');
    return `cleaned_${stem}.csv`;
  };

  /* Downloads */
  const handleDownloadClick = async (e) => {
    e.preventDefault();
    setDownloadError('');
    try { await downloadCleanedDataset(datasetId, downloadFilename()); }
    catch (err) { setDownloadError(err.message || 'İndirme başarısız.'); }
  };

  const handleDownloadReportClick = async (e, format) => {
    e.preventDefault();
    setDownloadError('');
    try { await downloadQualityReport(datasetId, format); }
    catch (err) { setDownloadError(err.message || `${format.toUpperCase()} raporu indirilemedi.`); }
  };

  /* Init selections */
  useEffect(() => {
    if (recommendations && recommendations.length > 0) {
      const initialIds = [];
      const initialMethods = {};
      recommendations.forEach((rec) => {
        initialIds.push(rec.id);
        if (rec.options && rec.options.length > 0) {
          const formatIssue = Object.keys(FORMAT_DEFAULTS).find((issue) => rec.id.endsWith(issue));
          const preferredMethod = formatIssue ? FORMAT_DEFAULTS[formatIssue] : rec.options[0].id;
          initialMethods[rec.id] = rec.options.some((opt) => opt.id === preferredMethod)
            ? preferredMethod
            : rec.options[0].id;
        }
      });
      setSelectedIds(initialIds);
      setSelectedMethods(initialMethods);
    }
  }, [recommendations]);

  useEffect(() => {
    setApplied(false);
    setTemplateMsg('');
    setPickTemplateId('');
  }, [datasetId]);

  /* Handlers */
  const toggleExpand = (i) => setExpandedIndex(expandedIndex === i ? null : i);

  const handleSelectAll = (e) => {
    setSelectedIds(e.target.checked ? recommendations.map((r) => r.id) : []);
  };

  const handleSelectOne = (id, checked) => {
    setSelectedIds(checked ? [...selectedIds, id] : selectedIds.filter((x) => x !== id));
  };

  const buildSelections = () =>
    recommendations
      .filter((rec) => selectedIds.includes(rec.id))
      .map((rec) => ({
        category: rec.category,
        column: rec.column,
        method: selectedMethods[rec.id] || 'drop',
      }));

  /* Polling */
  const POLL_TIMEOUT_MS = 120_000;

  const pollCleanStatus = async (id) =>
    new Promise((resolve, reject) => {
      const deadline = Date.now() + POLL_TIMEOUT_MS;
      const interval = setInterval(async () => {
        if (Date.now() > deadline) {
          clearInterval(interval);
          reject(new Error('İşlem zaman aşımına uğradı. Lütfen sayfayı yenileyip durumu tekrar kontrol edin.'));
          return;
        }
        try {
          const statusRes = await getDatasetStatus(id);
          if (statusRes.status === 'cleaned') { clearInterval(interval); resolve(); }
          else if (statusRes.status === 'error') {
            clearInterval(interval);
            reject(new Error('Temizleme işlemi sırasında hata oluştu.'));
          }
        } catch (err) { clearInterval(interval); reject(err); }
      }, 1500);
    });

  const handleApply = async () => {
    setLoading(true);
    setTemplateMsg('');
    try {
      const res = await onApply(buildSelections());
      if (res && res.status === 'processing') await pollCleanStatus(datasetId);
      setApplied(true);
      onApplied?.();
    } catch (e) {
      setTemplateMsg(e.message || 'İşlem uygulanamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTemplate = async () => {
    const name = templateName.trim();
    if (!name) { setTemplateMsg('Şablon adı girin.'); return; }
    const s = buildSelections();
    if (s.length === 0) { setTemplateMsg('En az bir işlem seçin.'); return; }
    setTemplateBusy(true);
    setTemplateMsg('');
    try {
      await saveTemplate(name, s);
      setTemplateName('');
      setTemplateMsg('Şablon kaydedildi.');
      onTemplatesChanged?.();
    } catch (e) {
      setTemplateMsg(e.message || 'Şablon kaydedilemedi.');
    } finally {
      setTemplateBusy(false);
    }
  };

  const handleApplyTemplate = async () => {
    const tid = Number(pickTemplateId);
    if (!tid) { setTemplateMsg('Önce bir şablon seçin.'); return; }
    setLoading(true);
    setTemplateMsg('');
    try {
      const res = await applyTemplateToDataset(datasetId, tid);
      if (res && res.status === 'processing') await pollCleanStatus(datasetId);
      setApplied(true);
      onApplied?.();
    } catch (e) {
      setTemplateMsg(e.message || 'Şablon uygulanamadı.');
    } finally {
      setLoading(false);
    }
  };

  if (!recommendations || recommendations.length === 0) return null;

  const categoryCount = recommendations.reduce((acc, rec) => {
    acc[rec.category] = (acc[rec.category] || 0) + 1;
    return acc;
  }, {});

  /* ── Collapsed (summary) view ── */
  if (!showList) {
    return (
      <section className="results-section">
        <div className="summary-banner">
          <div className="summary-icon"><CheckCircle size={28} aria-hidden /></div>
          <span className="summary-overline">Kalite profili hazır</span>
          <h3 className="summary-title">Analiz tamamlandı</h3>
          <p className="summary-text">
            Veri setinizde incelenebilecek <strong>{recommendations.length} öneri</strong> bulundu.
            Hiçbir işlem onayınız olmadan uygulanmayacak.
          </p>
          <div className="summary-breakdown">
            {Object.entries(categoryCount).map(([category, count]) => (
              <span key={category}><b>{count}</b> {CATEGORY_LABELS[category] || category}</span>
            ))}
          </div>
          <button type="button" className="btn-primary" onClick={() => setShowList(true)}>
            Önerileri incele <ChevronRight size={17} aria-hidden />
          </button>
        </div>
      </section>
    );
  }

  const allSelected = recommendations.length > 0 && selectedIds.length === recommendations.length;

  /* ── Full (expanded) view ── */
  return (
    <section className="results-section fade-in">
      {/* Header */}
      <div className="results-header-block">
        <span className="results-overline">Karar ekranı</span>
        <h3 className="section-heading">
          Temizleme <span>önerileri</span>
        </h3>
        <p>Her problemi ayrı ayrı inceleyin, uygulanacak yöntemi karşılaştırın ve seçimlerinizi onaylayın.</p>
      </div>

      {/* Category chips */}
      <CategoryChips categoryCount={categoryCount} />

      {/* Select all */}
      <div className="select-all-row glass-panel">
        <label className="checkbox-wrapper">
          <input type="checkbox" checked={allSelected} onChange={handleSelectAll} />
          <div className="checkbox-custom"><Check size={14} className="check-icon" /></div>
          <span>Tümünü seç / seçimi kaldır ({selectedIds.length}/{recommendations.length} seçili)</span>
        </label>
      </div>

      {/* How it works */}
      <div className="studio-decision-note">
        <strong>Nasıl çalışır?</strong>
        <span>
          Yalnızca seçili öneriler uygulanır. Her öneride tek yöntem seçilir ve işlem ham dosyayı
          değiştirmeden ayrı bir temizlenmiş çıktı üretir.
        </span>
      </div>

      {/* Template quick apply */}
      {!applied && templates.length > 0 && (
        <div className="template-quick glass-panel">
          <Wand2 size={20} className="template-quick-icon" aria-hidden />
          <div className="template-quick-body">
            <strong>Kayıtlı şablon</strong>
            <p className="template-quick-desc">Sütun adları dosyanızla eşleşen kurallar tek tıkla uygulanır.</p>
            <div className="template-quick-actions">
              <select
                className="template-select"
                value={pickTemplateId}
                onChange={(e) => setPickTemplateId(e.target.value)}
                aria-label="Şablon seç"
              >
                <option value="">— Şablon seçin —</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.selections_count ?? 0} kural)
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="btn-primary btn-template-apply"
                onClick={handleApplyTemplate}
                disabled={loading || !pickTemplateId}
              >
                Şablonu uygula
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="recommendations-list">
        {recommendations.map((rec, i) => {
          const isExpanded = expandedIndex === i;
          const isSelected = selectedIds.includes(rec.id);
          const RecIcon = CATEGORY_ICONS[rec.category] || AlertCircle;

          return (
            <div
              key={rec.id || i}
              className={`rec-item rec-${rec.category} ${isExpanded ? 'expanded' : ''} ${!isSelected ? 'unselected' : ''}`}
            >
              <div className="rec-header">
                {/* Checkbox */}
                <label className="checkbox-wrapper item-checkbox">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => handleSelectOne(rec.id, e.target.checked)}
                  />
                  <div className="checkbox-custom"><Check size={14} className="check-icon" /></div>
                </label>

                {/* Title group — clickable to expand */}
                <div
                  className="rec-title-group"
                  onClick={() => toggleExpand(i)}
                  style={{ cursor: 'pointer', flex: 1 }}
                >
                  <RecIcon size={18} className="rec-icon" />
                  <span className="rec-col-name">{rec.column}</span>
                </div>

                {/* Actions */}
                <div className="rec-actions">
                  <span className="rec-type">{CATEGORY_LABELS[rec.category] || rec.category}</span>
                  <button
                    type="button"
                    className={`btn-expand ${isExpanded ? 'active' : ''}`}
                    onClick={() => toggleExpand(i)}
                  >
                    {isExpanded ? 'Kapat' : 'Detay'}
                    {isExpanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                  </button>
                </div>
              </div>

              {/* Detail panel */}
              {isExpanded && (
                <div className="rec-details">
                  <p className="rec-desc">{rec.summary}</p>
                  {rec.options && rec.options.length > 0 && (
                    <div className="options-container">
                      <h5 className="options-title">Çözüm yöntemi seçin</h5>
                      <div className="options-grid">
                        {rec.options.map((opt) => {
                          const isOptionSelected = selectedMethods[rec.id] === opt.id;
                          return (
                            <label
                              key={opt.id}
                              className={`option-card ${isOptionSelected ? 'selected' : ''}`}
                            >
                              <input
                                type="radio"
                                name={`method-${rec.id}`}
                                value={opt.id}
                                checked={isOptionSelected}
                                onChange={() =>
                                  setSelectedMethods({ ...selectedMethods, [rec.id]: opt.id })
                                }
                              />
                              <div className="option-radio-dot" />
                              <div className="option-info">
                                <div className="option-name-row">
                                  <span className="option-name">{opt.name}</span>
                                  {opt.tags && opt.tags.map((tag) => (
                                    <span key={tag} className="option-tag">{tag}</span>
                                  ))}
                                </div>
                                <p className="option-desc">{opt.desc}</p>
                              </div>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Actions row (save template + success/download) */}
      <div className="actions-row">
        {!applied && (
          <div className="save-template-row glass-panel">
            <BookmarkPlus size={20} aria-hidden />
            <div className="save-template-fields">
              <span className="save-template-label">Seçimleri şablon olarak kaydet</span>
              <div className="save-template-inputs">
                <input
                  type="text"
                  className="template-name-input"
                  placeholder="Örn: Aylık satış temizliği"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                />
                <button
                  type="button"
                  className="btn-secondary-template"
                  onClick={handleSaveTemplate}
                  disabled={templateBusy || selectedIds.length === 0}
                >
                  {templateBusy ? 'Kaydediliyor…' : 'Kaydet'}
                </button>
              </div>
            </div>
          </div>
        )}

        {templateMsg && (
          <p className={`template-feedback ${templateMsg.includes('kaydedildi') || templateMsg.includes('başarı') ? 'ok' : 'err'}`}>
            {templateMsg}
          </p>
        )}

        {applied && (
          <>
            <div className="success-msg">
              <CheckCircle size={24} />
              <span>Tüm düzeltmeler uygulandı ve veri setiniz hazır!</span>
            </div>
            <div className="download-actions-group">
              <button type="button" className="btn-primary download-primary" onClick={handleDownloadClick}>
                <Download size={18} style={{ marginRight: 8 }} />
                Temiz veriyi indir (CSV)
              </button>
              <button
                type="button"
                className="btn-secondary-template download-secondary"
                onClick={(e) => handleDownloadReportClick(e, 'html')}
              >
                <Download size={18} style={{ marginRight: 8 }} />
                HTML raporunu indir
              </button>
              <button
                type="button"
                className="btn-secondary-template download-secondary"
                onClick={(e) => handleDownloadReportClick(e, 'pdf')}
              >
                <Download size={18} style={{ marginRight: 8 }} />
                PDF raporunu indir
              </button>
            </div>
          </>
        )}

        {downloadError && (
          <p className="status-msg error download-error">{downloadError}</p>
        )}
      </div>

      {/* Floating sticky action bar */}
      <FloatingActionBar
        selectedCount={selectedIds.length}
        totalCount={recommendations.length}
        onApply={handleApply}
        loading={loading}
        applied={applied}
      />
    </section>
  );
};

export default AnalysisResults;
