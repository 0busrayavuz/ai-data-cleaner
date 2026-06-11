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
  { label: 'Eksik değerler', value: 92, tone: 'emerald' },
  { label: 'Format tutarlılığı', value: 78, tone: 'cyan' },
  { label: 'Aykırı gözlemler', value: 71, tone: 'amber' },
];

const Hero = ({ isLoggedIn, onStart, onOpenDashboard }) => {
  return (
    <section className="hero-section" aria-labelledby="hero-heading">
      <div className="hero-copy">
        <div className="hero-badge">
          <Sparkles size={15} aria-hidden />
          <span>Akıllı veri kalitesi ve karar destek sistemi</span>
        </div>

        <h2 id="hero-heading" className="hero-title">
          Ham veriden
          <span> güvenilir analize.</span>
        </h2>

        <p className="hero-lead">
          Veri setinizi analiz edin, kalite sorunlarını görün, uygun temizleme
          yöntemini seçin ve tüm dönüşümleri izlenebilir raporlarla yönetin.
        </p>

        <div className="hero-actions">
          <button type="button" className="btn-primary hero-primary" onClick={onStart}>
            {isLoggedIn ? 'Yeni analiz başlat' : 'Ücretsiz kullanmaya başla'}
            <ArrowRight size={18} aria-hidden />
          </button>
          {isLoggedIn && (
            <button type="button" className="hero-secondary" onClick={onOpenDashboard}>
              Çalışma alanını aç
            </button>
          )}
        </div>

        <div className="hero-proof" aria-label="Desteklenen özellikler">
          <span><CheckCircle2 size={16} /> CSV, XLSX ve TXT</span>
          <span><CheckCircle2 size={16} /> Kullanıcı onaylı işlemler</span>
          <span><CheckCircle2 size={16} /> PDF ve HTML rapor</span>
        </div>
      </div>

      <div className="hero-visual" aria-label="Örnek veri kalite kokpiti">
        <div className="cockpit-shell">
          <div className="cockpit-topbar">
            <div className="cockpit-file">
              <span className="cockpit-file-icon"><FileSpreadsheet size={18} /></span>
              <div>
                <strong>sales_dataset.csv</strong>
                <small>12.480 satır · 18 sütun</small>
              </div>
            </div>
            <span className="cockpit-live"><i /> ÖRNEK KALİTE GÖRÜNÜMÜ</span>
          </div>

          <div className="cockpit-grid">
            <div className="quality-score-card">
              <div className="quality-score-head">
                <span>Veri kalite skoru</span>
                <Gauge size={18} aria-hidden />
              </div>
              <div className="quality-score-body">
                <div className="score-ring">
                  <strong>84</strong>
                  <small>/100</small>
                </div>
                <div>
                  <span className="score-trend">+19 puan potansiyel</span>
                  <p>Önerilen 7 işlem incelenmeye hazır.</p>
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
                <span className="cockpit-label">Öneri motoru</span>
                <BarChart3 size={17} aria-hidden />
              </div>
              <div className="pipeline-list">
                <div><i className="pipeline-dot emerald" /><span>MICE ile eksik değer tahmini</span><b>3</b></div>
                <div><i className="pipeline-dot cyan" /><span>Format standardizasyonu</span><b>2</b></div>
                <div><i className="pipeline-dot amber" /><span>Aykırı değer incelemesi</span><b>2</b></div>
              </div>
            </div>
          </div>
        </div>

        <div className="floating-security">
          <ShieldCheck size={19} aria-hidden />
          <div><strong>İzlenebilir işlem</strong><span>Her değişiklik kayıt altında</span></div>
        </div>
        <div className="floating-dataset">
          <Database size={18} aria-hidden />
          <span>CSV çıktı + kalite raporu</span>
        </div>
      </div>
    </section>
  );
};

export default Hero;
