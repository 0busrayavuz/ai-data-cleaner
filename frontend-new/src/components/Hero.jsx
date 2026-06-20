import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  Gauge,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import './Hero.css';

const QUALITY_ROWS = [
  { label: 'Eksik veri oranı', value: 92, tone: 'emerald' },
  { label: 'Şema tutarlılığı', value: 78, tone: 'cyan' },
  { label: 'Aykırı değer skoru', value: 71, tone: 'amber' },
];

const Hero = ({ isLoggedIn, onStart, onOpenPanel }) => {
  return (
    <section className="hero-section" aria-labelledby="hero-heading">
      <div className="hero-copy">

        <h2 id="hero-heading" className="hero-title">
          Ham veriden
          <span> güvenilir analiz.</span>
        </h2>

        <p className="hero-lead">
          Veri setinizi yükleyin; eksik değer, format tutarsızlığı ve aykırı
          gözlem sorunlarını otomatik tespit edin. Temizleme yöntemini seçin,
          her adımı denetim izi ile kayıt altına alın, PDF rapor indirin.
        </p>

        <div className="hero-actions">
          <button type="button" className="btn-primary hero-primary" onClick={onStart}>
            {isLoggedIn ? 'Yeni analiz başlat' : 'Hemen başla'}
            <ArrowRight size={18} aria-hidden />
          </button>
          {isLoggedIn && (
            <button type="button" className="hero-secondary" onClick={onOpenPanel}>
              Çalışma paneli
            </button>
          )}
        </div>

        <div className="hero-proof" aria-label="Desteklenen özellikler">
          <span><CheckCircle2 size={16} /> CSV, XLSX ve TXT desteği</span>
          <span><CheckCircle2 size={16} /> Denetim izi &amp; sürüm kaydı</span>
          <span><CheckCircle2 size={16} /> PDF / HTML kalite raporu</span>
        </div>
      </div>

      <div className="hero-visual" aria-label="Örnek veri kalitesi paneli">
        <div className="cockpit-shell">
          <div className="cockpit-topbar">
            <div className="cockpit-file">
              <span className="cockpit-file-icon"><FileSpreadsheet size={18} /></span>
              <div>
                <strong>musteri_segmentasyon.csv</strong>
                <small>48.320 satır · 24 sütun · 3,2 MB</small>
              </div>
            </div>
            <span className="cockpit-live"><i /> CANLI ÖN İZLEME</span>
          </div>

          <div className="cockpit-grid">
            <div className="quality-score-card">
              <div className="quality-score-head">
                <span>Kalite puanı</span>
                <Gauge size={18} aria-hidden />
              </div>
              <div className="quality-score-body">
                <div className="score-ring">
                  <strong>84</strong>
                  <small>/100</small>
                </div>
                <div>
                  <span className="score-trend">↑ +16 puan potansiyel</span>
                  <p>9 öneri otomatik oluşturuldu.</p>
                </div>
              </div>
            </div>

            <div className="quality-bars-card">
              <span className="cockpit-label">Kalite boyutları</span>
              {QUALITY_ROWS.map((row) => (
                <div className="quality-row" key={row.label}>
                  <div className="quality-row-meta">
                    <span>{row.label}</span>
                    <strong>{row.value}%</strong>
                  </div>
                  <div className="quality-track">
                    <span className={`quality-fill ${row.tone}`} style={{ width: `${row.value}%` }} />
                  </div>
                </div>
              ))}
            </div>

            <div className="pipeline-card">
              <div className="pipeline-head">
                <span className="cockpit-label">Temizleme pipeline'ı</span>
                <BarChart3 size={17} aria-hidden />
              </div>
              <div className="pipeline-list">
                <div><i className="pipeline-dot emerald" /><span>MICE ile eksik değer imputasyonu</span><b>3</b></div>
                <div><i className="pipeline-dot cyan" /><span>Tarih / tip standardizasyonu</span><b>5</b></div>
                <div><i className="pipeline-dot amber" /><span>IQR tabanlı aykırı değer tespiti</span><b>2</b></div>
              </div>
            </div>
          </div>
        </div>

        <div className="floating-security">
          <ShieldCheck size={19} aria-hidden />
          <div><strong>Tam denetim izi</strong><span>Her operasyon zaman damgalı</span></div>
        </div>
        <div className="floating-dataset">
          <Database size={18} aria-hidden />
          <span>Temiz CSV + kalite raporu</span>
        </div>
      </div>
    </section>
  );
};

export default Hero;
