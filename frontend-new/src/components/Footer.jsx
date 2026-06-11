import { Database } from 'lucide-react';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="container footer-content">
        <div className="footer-brand">
          <span className="footer-mark"><Database size={16} aria-hidden /></span>
          <div>
            <strong>VeriTemiz AI</strong>
            <span>Karar destekli veri kalite platformu</span>
          </div>
        </div>
        <p className="footer-stack">FastAPI · React · PostgreSQL · scikit-learn</p>
        <p className="footer-copy">© {new Date().getFullYear()} Bitirme projesi</p>
      </div>
    </footer>
  );
};

export default Footer;
