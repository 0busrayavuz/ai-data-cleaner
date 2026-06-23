import React, { useState, useEffect } from 'react';
import { CATEGORY_LABELS, CATEGORY_ICONS } from './AnalysisConstants';
import { AlertCircle } from 'lucide-react';

export function FloatingActionBar({ selectedCount, totalCount, onApply, loading, applied }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let interval;
    if (loading) {
      setProgress(0);
      interval = setInterval(() => {
        setProgress((p) => {
          const remaining = 95 - p;
          const step = Math.max(0.5, remaining * 0.1);
          return Math.min(95, p + step);
        });
      }, 300);
    } else if (applied) {
      setProgress(100);
    } else {
      setProgress(0);
    }
    return () => clearInterval(interval);
  }, [loading, applied]);

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
        {loading ? `Uygulanıyor... %${Math.round(progress)}` : 'Seçilenleri Uygula →'}
      </button>
      {loading && (
        <div className="studio-fab-progress">
          <div className="studio-fab-progress-bar" style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  );
}

export function CategoryChips({ categoryCount }) {
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
