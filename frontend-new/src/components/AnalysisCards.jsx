import React, { useEffect, useRef } from 'react';
import './AnalysisCards.css';

const FEATURES = [
  {
    title: 'Missing Value Imputation',
    description: 'MICE, KNN, and median-based strategies auto-selected per column type.',
    icon: '🔧',
    color: '#3b82f6',
  },
  {
    title: 'Anomaly Detection',
    description: 'DBSCAN clustering and Z-score analysis to surface hidden outliers.',
    icon: '🔍',
    color: '#8b5cf6',
  },
  {
    title: 'NLP Processing',
    description: 'TF-IDF, lemmatization and semantic feature extraction from text columns.',
    icon: '🧠',
    color: '#06b6d4',
  },
  {
    title: 'Feature Engineering',
    description: 'Automatic polynomial features, date decomposition, and categorical encoding.',
    icon: '⚙️',
    color: '#10b981',
  },
];

const TiltCard = ({ title, description, icon, color }) => {
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    const rotateX = (-y / rect.height) * 15;
    const rotateY = (x / rect.width) * 15;

    card.style.transform = `perspective(600px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.04)`;
    card.style.boxShadow = `${-rotateY * 2}px ${rotateX * 2}px 30px rgba(${hexToRgb(color)}, 0.25)`;
  };

  const handleMouseLeave = () => {
    const card = cardRef.current;
    if (!card) return;
    card.style.transform = 'perspective(600px) rotateX(0) rotateY(0) scale(1)';
    card.style.boxShadow = '';
  };

  const hexToRgb = (hex) => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `${r}, ${g}, ${b}`;
  };

  return (
    <div
      ref={cardRef}
      className="tilt-card glass-panel"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ '--card-accent': color }}
    >
      <div className="card-icon-wrap">
        <span className="card-icon">{icon}</span>
      </div>
      <h4 className="card-title">{title}</h4>
      <p className="card-desc">{description}</p>
      <div className="card-glow" style={{ background: color }}></div>
    </div>
  );
};

const AnalysisCards = () => {
  return (
    <section className="analysis-section">
      <h3 className="section-heading">
        What our <span className="glow-text">AI Pipeline</span> does
      </h3>
      <div className="cards-grid">
        {FEATURES.map((feat) => (
          <TiltCard key={feat.title} {...feat} />
        ))}
      </div>
    </section>
  );
};

export default AnalysisCards;
