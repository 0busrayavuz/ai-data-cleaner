import React, { useEffect, useRef } from 'react';
import './AnalysisCards.css';

const FEATURES = [
  {
    title: 'Eksik Veri Doldurma',
    description: 'Sütun tipine ve veri dağılımına göre MICE, KNN veya basamaklı medyan stratejilerini otomatik belirler.',
    icon: '🔧',
    color: '#3b82f6',
  },
  {
    title: 'Aykırı Değer Tespiti',
    description: 'DBSCAN kümeleme ve Isolation Forest ile gözle görülmeyen bağlamsal anormallikleri yüzeye çıkarır.',
    icon: '🔍',
    color: '#8b5cf6',
  },
  {
    title: 'Format Standardizasyonu',
    description: 'Metin, tarih ve telefon numarası gibi alanlardaki tutarsızlıkları akıllı NLP destekli formatlayıcı ile onarır.',
    icon: '✨',
    color: '#06b6d4',
  },
  {
    title: 'Özellik Mühendisliği',
    description: 'Modelinizin başarısını artırmak için otomatik olarak yeni kategorik ve polinom özellikleri türetir.',
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
    card.style.boxShadow = `${-rotateY * 2}px ${rotateX * 2}px 30px rgba(${hexToRgb(color)}, 0.15)`;
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
    <section className="analysis-section" style={{ padding: '5rem 0' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h3 style={{ fontSize: '2.5rem', fontWeight: '700', marginBottom: '1rem', color: 'var(--text-primary)' }}>
          <span className="glow-text">Yapay Zeka (AI)</span> Boru Hattımız Neler Yapar?
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '600px', margin: '0 auto' }}>
          Arka planda çalışan güçlü makine öğrenmesi modellerimiz, verinizi bir veri bilimci titizliğinde analiz eder ve otomatik düzeltmeler önerir.
        </p>
      </div>
      <div className="cards-grid">
        {FEATURES.map((feat) => (
          <TiltCard key={feat.title} {...feat} />
        ))}
      </div>
    </section>
  );
};

export default AnalysisCards;
