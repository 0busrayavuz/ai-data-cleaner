import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertCircle, Download, ChevronDown, ChevronRight, Check } from 'lucide-react';
import './AnalysisResults.css';

const AnalysisResults = ({ recommendations, datasetId, onApply }) => {
  const [loading, setLoading] = useState(false);
  const [applied, setApplied] = useState(false);
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [showList, setShowList] = useState(false);
  
  const [selectedIds, setSelectedIds] = useState([]);
  const [selectedMethods, setSelectedMethods] = useState({});

  useEffect(() => {
    if (recommendations && recommendations.length > 0) {
      const initialIds = [];
      const initialMethods = {};
      recommendations.forEach(rec => {
        initialIds.push(rec.id);
        if (rec.options && rec.options.length > 0) {
          // Varsayılan olarak 2. metodu seç (eğer varsa, ör: Log Dönüşümü), yoksa ilk metot
          initialMethods[rec.id] = rec.options.length > 1 ? rec.options[1].id : rec.options[0].id;
        }
      });
      setSelectedIds(initialIds);
      setSelectedMethods(initialMethods);
    }
  }, [recommendations]);

  const toggleExpand = (i) => {
    setExpandedIndex(expandedIndex === i ? null : i);
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(recommendations.map(r => r.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id, checked) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter(x => x !== id));
    }
  };

  const handleApply = async () => {
    setLoading(true);
    try {
      // Sadece seçili olanları filtrele ve gönder
      const selections = recommendations
        .filter(rec => selectedIds.includes(rec.id))
        .map(rec => ({
          category: rec.category,
          column: rec.column,
          method: selectedMethods[rec.id] || "drop"
        }));
      
      await onApply(selections);
      setApplied(true);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (!recommendations || recommendations.length === 0) return null;

  if (!showList) {
    return (
      <section className="results-section">
        <div className="summary-banner glass-panel">
          <div className="summary-icon">🎉</div>
          <h3 className="summary-title">Analiz Tamamlandı!</h3>
          <p className="summary-text">
            Veri setiniz yapay zeka algoritmalarımızca tarandı ve toplam <strong>{recommendations.length} noktada</strong> düzeltme/geliştirme önerisi bulundu.
          </p>
          <button className="btn-primary" onClick={() => setShowList(true)}>
            Önerileri İncele ve Düzenle
          </button>
        </div>
      </section>
    );
  }

  const allSelected = recommendations.length > 0 && selectedIds.length === recommendations.length;

  return (
    <section className="results-section fade-in">
      <div className="results-header-block">
        <h3 className="section-heading" style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>
          Analiz <span className="glow-text">Önerileri</span>
        </h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
          Aşağıdaki listeden uygulamak istediğiniz işlemleri seçebilirsiniz.
        </p>
      </div>

      <div className="select-all-row glass-panel">
        <label className="checkbox-wrapper">
          <input 
            type="checkbox" 
            checked={allSelected} 
            onChange={handleSelectAll} 
          />
          <div className="checkbox-custom"><Check size={14} className="check-icon" /></div>
          <span>Tümünü Seç / Seçimi Kaldır ({selectedIds.length}/{recommendations.length} seçili)</span>
        </label>
      </div>

      <div className="recommendations-list">
        {recommendations.map((rec, i) => {
          const isExpanded = expandedIndex === i;
          const isSelected = selectedIds.includes(rec.id);

          return (
            <div key={i} className={`rec-item glass-panel ${isExpanded ? 'expanded' : ''} ${!isSelected ? 'unselected' : ''}`}>
              <div className="rec-header">
                
                <label className="checkbox-wrapper item-checkbox">
                  <input 
                    type="checkbox" 
                    checked={isSelected} 
                    onChange={(e) => handleSelectOne(rec.id, e.target.checked)} 
                  />
                  <div className="checkbox-custom"><Check size={14} className="check-icon" /></div>
                </label>

                <div className="rec-title-group" onClick={() => toggleExpand(i)} style={{ cursor: 'pointer', flex: 1 }}>
                  <AlertCircle size={18} className="rec-icon" />
                  <strong style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>{rec.column}</strong>
                </div>
                
                <div className="rec-actions">
                  <span className="rec-type">{rec.category}</span>
                  <button 
                    className={`btn-expand ${isExpanded ? 'active' : ''}`}
                    onClick={() => toggleExpand(i)}
                  >
                    {isExpanded ? 'Kapat' : 'Detay Gör'}
                    {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  </button>
                </div>
              </div>
              
              {isExpanded && (
                <div className="rec-details">
                  <p className="rec-desc">{rec.summary}</p>
                  
                  {rec.options && rec.options.length > 0 && (
                    <div className="options-container">
                      <h5 className="options-title">Çözüm Yöntemi:</h5>
                      <div className="options-grid">
                        {rec.options.map(opt => {
                          const isOptionSelected = selectedMethods[rec.id] === opt.id;
                          return (
                            <label key={opt.id} className={`option-card ${isOptionSelected ? 'selected' : ''}`}>
                              <input 
                                type="radio" 
                                name={`method-${rec.id}`} 
                                value={opt.id}
                                checked={isOptionSelected}
                                onChange={() => setSelectedMethods({...selectedMethods, [rec.id]: opt.id})}
                              />
                              <div className="option-info">
                                <div className="option-name-row">
                                  <span className="option-name">{opt.name}</span>
                                  {opt.tags && opt.tags.map(tag => (
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

      <div className="actions-row">
        {!applied ? (
          <button
            className="btn-primary"
            onClick={handleApply}
            disabled={loading || selectedIds.length === 0}
          >
            {loading ? 'Uygulanıyor...' : `Seçili Olanları Uygula (${selectedIds.length} İşlem)`}
          </button>
        ) : (
          <div className="success-msg">
            <CheckCircle size={24} />
            <span>Tüm düzeltmeler uygulandı ve veri setiniz hazır!</span>
            <a
              href={`http://localhost:8000/download/${datasetId}`}
              download={`temizlenmis_veri_${datasetId}.csv`}
              className="btn-primary"
              style={{ textDecoration: 'none', marginLeft: '16px', display: 'inline-flex', alignItems: 'center' }}
            >
              <Download size={18} style={{ marginRight: 8 }} />
              Temiz Veriyi İndir
            </a>
          </div>
        )}
      </div>
    </section>
  );
};

export default AnalysisResults;
