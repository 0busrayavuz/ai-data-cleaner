import React from 'react';
import { Sparkles, BarChart2, Zap } from 'lucide-react';
import './Hero.css';

const Hero = () => {
  return (
    <section className="hero-section text-center">
      <div className="badge glass-panel" style={{ display: 'inline-flex', padding: '6px 12px', borderRadius: '20px', alignItems: 'center', gap: '8px', marginBottom: '2rem', fontSize: '0.85rem', fontWeight: '500' }}>
        <Sparkles size={16} style={{ color: 'var(--accent-secondary)' }} />
        <span style={{ color: 'var(--text-secondary)' }}>v2.0 FastAPI + React Mimarisi</span>
      </div>
      
      <h2 className="hero-title" style={{ fontSize: '4rem', fontWeight: '800', lineHeight: '1.1', marginBottom: '1.5rem', color: 'var(--text-primary)' }}>
        Yeni Nesil Yapay Zeka ile <br />
        <span className="glow-text">Veri Temizliği ve Analizi</span>
      </h2>
      
      <p className="hero-subtitle" style={{ fontSize: '1.15rem', color: 'var(--text-secondary)', maxWidth: '700px', margin: '0 auto 3rem auto', lineHeight: '1.6' }}>
        Saatler süren veri temizleme işlerinizi dakikalara indirin. Excel veya CSV dosyanızı yükleyin; yapay zeka algoritmalarımız eksik verileri doldursun, anormallikleri tespit etsin ve verinizi modellemeye hazır hale getirsin.
      </p>

      <div className="hero-stats glass-panel" style={{ display: 'inline-flex', gap: '3rem', padding: '24px 40px', borderRadius: '24px', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }}>
        <div className="stat-item" style={{ display: 'flex', alignItems: 'center', gap: '16px', textAlign: 'left' }}>
          <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '12px', borderRadius: '14px', color: 'var(--accent-secondary)' }}>
            <Zap size={28} />
          </div>
          <div>
            <h4 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', color: 'var(--text-primary)' }}>Şimşek Hızında</h4>
            <p style={{ margin: '0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Milyonlarca satırı saniyeler içinde işleyin</p>
          </div>
        </div>
        
        <div className="stat-divider" style={{ width: '1px', height: '50px', background: 'var(--glass-border)' }}></div>
        
        <div className="stat-item" style={{ display: 'flex', alignItems: 'center', gap: '16px', textAlign: 'left' }}>
          <div style={{ background: 'rgba(126, 46, 255, 0.1)', padding: '12px', borderRadius: '14px', color: 'var(--accent-primary)' }}>
            <BarChart2 size={28} />
          </div>
          <div>
            <h4 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', color: 'var(--text-primary)' }}>Akıllı Analitik</h4>
            <p style={{ margin: '0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>DBSCAN & Isolation Forest ile anormallik tespiti</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
