import React from 'react';
import { Check, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react';
import { CATEGORY_LABELS, CATEGORY_ICONS } from './AnalysisConstants';

export default function RecommendationCard({
  rec,
  isExpanded,
  isSelected,
  selectedMethod,
  onToggleExpand,
  onSelectOne,
  onMethodChange,
}) {
  const RecIcon = CATEGORY_ICONS[rec.category] || AlertCircle;

  return (
    <div
      className={`rec-item rec-${rec.category} ${isExpanded ? 'expanded' : ''} ${!isSelected ? 'unselected' : ''}`}
    >
      <div className="rec-header">
        {/* Checkbox */}
        <label className="checkbox-wrapper item-checkbox">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => onSelectOne(rec.id, e.target.checked)}
          />
          <div className="checkbox-custom"><Check size={14} className="check-icon" /></div>
        </label>

        {/* Title group — clickable to expand */}
        <div
          className="rec-title-group"
          onClick={onToggleExpand}
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
            onClick={onToggleExpand}
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
                  const isOptionSelected = selectedMethod === opt.id;
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
                        onChange={() => onMethodChange(rec.id, opt.id)}
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
}
