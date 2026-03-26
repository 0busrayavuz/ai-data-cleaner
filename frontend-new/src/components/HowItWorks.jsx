import { UploadCloud, Cpu, DownloadCloud, ArrowRight } from 'lucide-react';
import './HowItWorks.css';

const HowItWorks = () => {
  return (
    <section className="how-it-works-section">
      <div className="hiw-header text-center">
        <h3 className="section-heading">Nasıl <span className="glow-text">Çalışır?</span></h3>
        <p className="section-subtitle">Sadece 3 basit adımda verilerinizi modele hazır hale getirin.</p>
      </div>

      <div className="hiw-steps container">
        {/* Step 1 */}
        <div className="hiw-step glass-panel">
          <div className="step-number">01</div>
          <div className="step-icon">
            <UploadCloud size={32} />
          </div>
          <h4>Verinizi Yükleyin</h4>
          <p>CSV, Excel veya TXT formatındaki ham verinizi sisteme güvenle yükleyin. Tüm verileriniz tarayıcınız ile sunucumuz arasında şifrelenerek taşınır.</p>
        </div>

        <div className="step-arrow">
          <ArrowRight size={24} />
        </div>

        {/* Step 2 */}
        <div className="hiw-step glass-panel">
          <div className="step-number">02</div>
          <div className="step-icon">
            <Cpu size={32} />
          </div>
          <h4>Yapay Zeka Analizi</h4>
          <p>Algoritmalarımız (DBSCAN, Isolation Forest) saniyeler içinde verideki eksiklikleri, aykırı değerleri tespit eder ve size özel temizleme reçetesi sunar.</p>
        </div>

        <div className="step-arrow">
          <ArrowRight size={24} />
        </div>

        {/* Step 3 */}
        <div className="hiw-step glass-panel">
          <div className="step-number">03</div>
          <div className="step-icon">
            <DownloadCloud size={32} />
          </div>
          <h4>Temiz Veriyi İndirin</h4>
          <p>Önerilen işlemleri tek tıkla onaylayın. %100 temizlenmiş ve makine öğrenmesi modelleri için optimize edilmiş verinizi anında indirin.</p>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
