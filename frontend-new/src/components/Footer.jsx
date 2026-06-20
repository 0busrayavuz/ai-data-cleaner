import { Database } from 'lucide-react';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="container footer-content">
        <div className="footer-brand">
          <span className="footer-mark"><Database size={16} aria-hidden /></span>
          <div>
            <h3>PrepWise</h3>
            <p>
              Akıllı veri ön işleme ve kalite asistanı. 
              Veri temizleme süreçlerinizi makine öğrenmesi destekli önerilerle hızlandırın, güvenle analiz yapın.
            </p>
          </div>
        </div>
        <p className="footer-stack">FastAPI · React · PostgreSQL · scikit-learn</p>
        <p className="footer-copy">© {new Date().getFullYear()} PrepWise. Tüm hakları saklıdır.</p>
      </div>
    </footer>
  );
};

export default Footer;
