import { useState, useEffect } from 'react';
import { X, Mail, Lock, User, KeyRound, ArrowRight } from 'lucide-react';
import './AuthModal.css';

const AuthModal = ({ isOpen, onClose, onLogin }) => {
  const [view, setView] = useState('login'); // 'login', 'register', 'forgot-password'
  const [animationClass, setAnimationClass] = useState('');

  // Reset view when modal opens
  useEffect(() => {
    if (isOpen) {
      setView('login');
      setAnimationClass('fade-in-scale');
    } else {
      setAnimationClass('');
    }
  }, [isOpen]);

  const changeView = (newView) => {
    setAnimationClass('fade-out-left');
    setTimeout(() => {
      setView(newView);
      setAnimationClass('fade-in-right');
    }, 200);
  };

  const handleClose = () => {
    setAnimationClass('fade-out-down');
    setTimeout(() => {
      onClose();
    }, 300);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (view === 'login') {
      const email = e.target.querySelector('input[type="email"]').value;
      if (onLogin) onLogin({ email });
    } else {
      console.log(`Submitted form for view: ${view}`);
    }
  };

  if (!isOpen && !animationClass.includes('fade-out')) return null;

  return (
    <div className={`auth-overlay ${isOpen ? 'show' : ''}`} onMouseDown={handleClose}>
      <div 
        className={`auth-modal glass-panel ${animationClass}`} 
        onMouseDown={(e) => e.stopPropagation()}
      >
        <button className="auth-close-btn" onClick={handleClose}>
          <X size={24} />
        </button>

        <div className="auth-content">
          {view === 'login' && (
            <div className="auth-view">
              <h2 className="glow-text">Hoş Geldiniz</h2>
              <p className="auth-subtitle">Sisteme giriş yaparak verilerinizi yönetin.</p>
              
              <form onSubmit={handleSubmit} className="auth-form">
                <div className="input-group">
                  <Mail className="input-icon" size={20} />
                  <input type="email" placeholder="E-posta" className="auth-input" required />
                </div>
                <div className="input-group">
                  <Lock className="input-icon" size={20} />
                  <input type="password" placeholder="Şifre" className="auth-input" required />
                </div>
                <div className="auth-options">
                  <label className="checkbox-container">
                    <input type="checkbox" />
                    <span className="checkmark"></span>
                    Beni hatırla
                  </label>
                  <button type="button" className="text-btn" onClick={() => changeView('forgot-password')}>
                    Şifremi Unuttum
                  </button>
                </div>
                <button type="submit" className="btn-primary auth-submit">
                  Giriş Yap <ArrowRight size={18} />
                </button>
              </form>
              
              <p className="auth-footer">
                Hesabınız yok mu? <button className="text-btn highlight" onClick={() => changeView('register')}>Kayıt Ol</button>
              </p>
            </div>
          )}

          {view === 'register' && (
            <div className="auth-view">
              <h2 className="glow-text">Hesap Oluştur</h2>
              <p className="auth-subtitle">Veri temizleme uzmanı olmak için ilk adımı atın.</p>
              
              <form onSubmit={handleSubmit} className="auth-form">
                <div className="input-group">
                  <User className="input-icon" size={20} />
                  <input type="text" placeholder="Ad Soyad" className="auth-input" required />
                </div>
                <div className="input-group">
                  <Mail className="input-icon" size={20} />
                  <input type="email" placeholder="E-posta" className="auth-input" required />
                </div>
                <div className="input-group">
                  <Lock className="input-icon" size={20} />
                  <input type="password" placeholder="Şifre" className="auth-input" required />
                </div>
                <button type="submit" className="btn-primary auth-submit">
                  Kayıt Ol <ArrowRight size={18} />
                </button>
              </form>
              
              <p className="auth-footer">
                Zaten hesabınız var mı? <button className="text-btn highlight" onClick={() => changeView('login')}>Giriş Yap</button>
              </p>
            </div>
          )}

          {view === 'forgot-password' && (
            <div className="auth-view">
              <div className="icon-header">
                <KeyRound size={40} className="glow-icon" />
              </div>
              <h2 className="glow-text">Şifremi Unuttum</h2>
              <p className="auth-subtitle">E-posta adresinizi girin, size sıfırlama bağlantısı gönderelim.</p>
              
              <form onSubmit={handleSubmit} className="auth-form">
                <div className="input-group">
                  <Mail className="input-icon" size={20} />
                  <input type="email" placeholder="E-posta Adresi" className="auth-input" required />
                </div>
                <button type="submit" className="btn-primary auth-submit">
                  Bağlantı Gönder <ArrowRight size={18} />
                </button>
              </form>
              
              <p className="auth-footer">
                <button className="text-btn highlight" onClick={() => changeView('login')}>Giriş Ekranına Dön</button>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
