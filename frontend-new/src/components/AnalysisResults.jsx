import React, { useState } from 'react';
import { CheckCircle, AlertCircle, Download } from 'lucide-react';
import './AnalysisResults.css';

const AnalysisResults = ({ recommendations, datasetId, onApply }) => {
  const [loading, setLoading] = useState(false);
  const [applied, setApplied] = useState(false);

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
      <h3 className="section-heading">
        Analysis <span className="glow-text">Recommendations</span>
      </h3>

      <div className="recommendations-list">
        {recommendations.map((rec, i) => (
          <div key={i} className="rec-item glass-panel">
            <div className="rec-header">
              <AlertCircle size={18} className="rec-icon" />
              <strong>{rec.column}</strong>
              <span className="rec-type">{rec.category}</span>
            </div>
            <p className="rec-desc">{rec.summary}</p>
          </div>
        ))}
      </div>

      <div className="actions-row">
        {!applied ? (
          <button
            className="btn-primary"
            onClick={handleApply}
            disabled={loading}
          >
            {loading ? 'Applying...' : 'Apply All Fixes'}
          </button>
        ) : (
          <div className="success-msg">
            <CheckCircle size={20} />
            <span>All fixes applied! Your dataset is ready.</span>
            <a
              href={`http://localhost:8000/download/${datasetId}`}
              className="btn-primary"
              style={{ textDecoration: 'none', marginLeft: '12px', display: 'inline-block' }}
            >
              <Download size={16} style={{ marginRight: 6 }} />
              Download
            </a>
          </div>
        )}
      </div>
    </section>
  );
};

export default AnalysisResults;
