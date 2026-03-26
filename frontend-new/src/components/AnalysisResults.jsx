import React, { useState } from 'react';
import { CheckCircle, AlertCircle, Download, ChevronDown, ChevronRight } from 'lucide-react';
import './AnalysisResults.css';

const AnalysisResults = ({ recommendations, datasetId, onApply }) => {
  const [loading, setLoading] = useState(false);
  const [applied, setApplied] = useState(false);
  const [expandedIndex, setExpandedIndex] = useState(null);

  const toggleExpand = (i) => {
    setExpandedIndex(expandedIndex === i ? null : i);
  };

  const handleApply = async () => {
    setLoading(true);
    try {
      // Backend beklediği format: { selections: [{ category, column, method }] }
      const selections = recommendations.map(rec => ({
        category: rec.category, // e.g. "missing", "outlier", "format"
        column: rec.column,
        method: rec.options && rec.options.length > 0 ? rec.options[0].id : "drop"
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

  return (
    <section className="results-section">
      <h3 className="section-heading" style={{ fontSize: '2.5rem', marginBottom: '2rem' }}>
        Analiz <span className="glow-text">Önerileri</span>
      </h3>

      <div className="recommendations-list">
        {recommendations.map((rec, i) => {
          const isExpanded = expandedIndex === i;
          return (
            <div key={i} className={`rec-item glass-panel ${isExpanded ? 'expanded' : ''}`}>
              <div className="rec-header">
                <div className="rec-title-group">
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
            disabled={loading}
          >
            {loading ? 'Uygulanıyor...' : 'Tüm Düzeltmeleri Uygula'}
          </button>
        ) : (
          <div className="success-msg">
            <CheckCircle size={24} />
            <span>Tüm düzeltmeler uygulandı! Veri setiniz hazır.</span>
            <a
              href={`http://localhost:8000/download/${datasetId}`}
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
