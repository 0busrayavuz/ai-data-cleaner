import { useState, useEffect, useCallback } from 'react';
import { X, Mail, Lock, KeyRound, ArrowRight, Loader, Eye, EyeOff, UserPlus } from 'lucide-react';
import { loginUser, registerUser, forgotPassword, resetPassword, setAuthToken } from '../services/api';
import './AuthModal.css';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function registerPasswordScore(pw) {
  if (!pw) return { score: 0, label: '' };
  let s = 0;
  if (pw.length >= 8) s += 1;
  if (pw.length >= 12) s += 1;
  if (/[a-züğıöşç]/.test(pw) && /[A-ZÜĞİÖŞÇ]/.test(pw)) s += 1;
  if (/\d/.test(pw)) s += 1;
  if (/[^a-zA-Z0-9üğıöşçÜĞİÖŞÇ]/.test(pw)) s += 1;
  const score = Math.min(3, Math.ceil(s / 2));
  const labels = ['', 'Zayıf', 'Orta', 'Güçlü'];
  return { score, label: labels[score] };
}

const AuthModal = ({ isOpen, onClose, onLogin }) => {
  const [view, setView] = useState('login');
  const [animationClass, setAnimationClass] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [loginFieldErrors, setLoginFieldErrors] = useState({});

  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirm, setRegConfirm] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [showRegConfirm, setShowRegConfirm] = useState(false);
  const [regFieldErrors, setRegFieldErrors] = useState({});
  const [acceptTerms, setAcceptTerms] = useState(false);

  const resetLoginForm = useCallback(() => {
    setLoginEmail('');
    setLoginPassword('');
    setRememberMe(true);
    setShowLoginPassword(false);
    setLoginFieldErrors({});
  }, []);

  const resetRegisterForm = useCallback(() => {
    setRegEmail('');
    setRegPassword('');
    setRegConfirm('');
    setShowRegPassword(false);
    setShowRegConfirm(false);
    setRegFieldErrors({});
    setAcceptTerms(false);
  }, []);

  useEffect(() => {
    if (isOpen) {
      setView('login');
      setAnimationClass('fade-in-scale');
      setErrorMsg('');
      resetLoginForm();
      resetRegisterForm();
    } else {
      setAnimationClass('');
    }
  }, [isOpen, resetLoginForm, resetRegisterForm]);

  const changeView = (newView) => {
    setAnimationClass('fade-out-left');
    setErrorMsg('');
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

  const validateLogin = () => {
    const next = {};
    const em = loginEmail.trim();
    if (!em) next.email = 'E-posta adresi gerekli.';
    else if (!EMAIL_RE.test(em)) next.email = 'Geçerli bir e-posta adresi girin.';
    if (!loginPassword) next.password = 'Şifre gerekli.';
    return Object.keys(next).length ? next : null;
  };

  const validateRegister = () => {
    const next = {};
    const em = regEmail.trim();
    if (!em) next.email = 'E-posta adresi gerekli.';
    else if (!EMAIL_RE.test(em)) next.email = 'Geçerli bir e-posta adresi girin.';
    if (!regPassword) next.password = 'Şifre gerekli.';
    else if (regPassword.length < 8) next.password = 'Şifre en az 8 karakter olmalı.';
    if (!regConfirm) next.confirmPassword = 'Şifre tekrarı gerekli.';
    else if (regConfirm !== regPassword) next.confirmPassword = 'Şifreler eşleşmiyor.';
    if (!acceptTerms) next.terms = 'Devam etmek için kullanım koşullarını kabul etmelisiniz.';
    return Object.keys(next).length ? next : null;
  };

  const goToRegister = () => {
    resetRegisterForm();
    changeView('register');
  };

  const regPwStrength = view === 'register' ? registerPasswordScore(regPassword) : { score: 0, label: '' };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    try {
      if (view === 'login') {
        const fieldErr = validateLogin();
        if (fieldErr) {
          setLoginFieldErrors(fieldErr);
          return;
        }
        setLoginFieldErrors({});
        const data = await loginUser(loginEmail.trim(), loginPassword);
        setAuthToken(data.access_token, rememberMe, data.refresh_token);
        if (onLogin) onLogin({ email: data.email });
      } else if (view === 'register') {
        const fieldErr = validateRegister();
        if (fieldErr) {
          setRegFieldErrors(fieldErr);
          return;
        }
        setRegFieldErrors({});
        await registerUser(regEmail.trim(), regPassword);
        resetRegisterForm();
        changeView('login');
        resetLoginForm();
        setTimeout(() => setErrorMsg('Kayıt başarılı. Lütfen giriş yapın.'), 400);
      } else if (view === 'forgot-password') {
        const email = e.target.querySelector('input[type="email"]').value;
        await forgotPassword(email);
        changeView('reset-password');
        setTimeout(() => setErrorMsg('Sıfırlama kodu oluşturuldu. Geliştirme ortamında kod sunucu çıktısında görüntülenir.'), 450);
      } else if (view === 'reset-password') {
        const tokenVal = e.target.querySelector('input[name="reset-token"]').value;
        const pw = e.target.querySelector('input[name="new-password"]').value;
        const pw2 = e.target.querySelector('input[name="confirm-password"]').value;
        if (!tokenVal) {
          setErrorMsg('Sıfırlama kodu gerekli.');
          return;
        }
        if (pw.length < 8) {
          setErrorMsg('Şifre en az 8 karakter olmalı.');
          return;
        }
        if (pw !== pw2) {
          setErrorMsg('Şifreler eşleşmiyor.');
          return;
        }
        await resetPassword(tokenVal, pw);
        changeView('login');
        resetLoginForm();
        setTimeout(() => setErrorMsg('Şifreniz güncellendi. Giriş yapabilirsiniz.'), 450);
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen && !animationClass.includes('fade-out')) return null;

  return (
    <div
      className={`auth-overlay ${isOpen ? 'show' : ''}`}
      onMouseDown={handleClose}
      role="presentation"
    >
      <div
        className={`auth-modal glass-panel ${animationClass}`}
        onMouseDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Giriş veya kayıt"
      >
        <button type="button" className="auth-close-btn" onClick={handleClose} aria-label="Kapat">
          <X size={24} aria-hidden />
        </button>

        <div className="auth-content">
          {view === 'login' && (
            <div className="auth-view">
              <h2 className="glow-text">PrepWise'a Giriş Yap</h2>
              <p className="auth-subtitle">Sisteme giriş yaparak verilerinizi yönetin.</p>

              {errorMsg && (
                <div
                  className={`auth-message ${errorMsg.includes('başarılı') || errorMsg.includes('güncellendi') ? 'success' : 'error'}`}
                  role="alert"
                >
                  {errorMsg}
                </div>
              )}

              <form onSubmit={handleSubmit} className="auth-form" noValidate>
                <div className={`input-group ${loginFieldErrors.email ? 'has-error' : ''}`}>
                  <Mail className="input-icon" size={20} aria-hidden />
                  <input
                    id="login-email"
                    type="email"
                    name="email"
                    autoComplete="email"
                    inputMode="email"
                    placeholder="ornek@eposta.com"
                    className="auth-input"
                    value={loginEmail}
                    onChange={(e) => {
                      setLoginEmail(e.target.value);
                      if (loginFieldErrors.email) setLoginFieldErrors((p) => ({ ...p, email: undefined }));
                    }}
                    aria-invalid={!!loginFieldErrors.email}
                    aria-describedby={loginFieldErrors.email ? 'login-email-err' : undefined}
                  />
                </div>
                {loginFieldErrors.email && (
                  <p id="login-email-err" className="field-error">
                    {loginFieldErrors.email}
                  </p>
                )}

                <div className={`input-group input-group-password ${loginFieldErrors.password ? 'has-error' : ''}`}>
                  <Lock className="input-icon" size={20} aria-hidden />
                  <input
                    id="login-password"
                    type={showLoginPassword ? 'text' : 'password'}
                    name="password"
                    autoComplete="current-password"
                    placeholder="Şifreniz"
                    className="auth-input"
                    value={loginPassword}
                    onChange={(e) => {
                      setLoginPassword(e.target.value);
                      if (loginFieldErrors.password) setLoginFieldErrors((p) => ({ ...p, password: undefined }));
                    }}
                    aria-invalid={!!loginFieldErrors.password}
                    aria-describedby={loginFieldErrors.password ? 'login-password-err' : undefined}
                  />
                  <button
                    type="button"
                    className="input-suffix-btn"
                    tabIndex={0}
                    aria-label={showLoginPassword ? 'Şifreyi gizle' : 'Şifreyi göster'}
                    onClick={() => setShowLoginPassword((v) => !v)}
                  >
                    {showLoginPassword ? <EyeOff size={20} aria-hidden /> : <Eye size={20} aria-hidden />}
                  </button>
                </div>
                {loginFieldErrors.password && (
                  <p id="login-password-err" className="field-error">
                    {loginFieldErrors.password}
                  </p>
                )}

                <div className="auth-options">
                  <label className="checkbox-container">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                    />
                    <span className="checkmark" aria-hidden />
                    Beni hatırla
                  </label>
                  <button type="button" className="text-btn" onClick={() => changeView('forgot-password')}>
                    Şifremi unuttum
                  </button>
                </div>
                <p className="remember-hint">
                  İşaretli değilse oturum yalnızca bu sekmede saklanır; tarayıcıyı kapatınca çıkış yapılır.
                </p>

                <button type="submit" className="btn-primary auth-submit" disabled={loading}>
                  {loading ? <Loader className="spin" size={18} aria-hidden /> : <>Giriş yap <ArrowRight size={18} aria-hidden /></>}
                </button>
              </form>

              <p className="auth-footer">
                Hesabınız yok mu?{' '}
                <button type="button" className="text-btn highlight" onClick={goToRegister}>
                  Kayıt ol
                </button>
              </p>
            </div>
          )}

          {view === 'register' && (
            <div className="auth-view">
              <div className="icon-header">
                <UserPlus size={40} className="glow-icon" aria-hidden />
              </div>
              <h2 className="glow-text">Hesap oluştur</h2>
              <p className="auth-subtitle">
                PrepWise ile dosyalarınızı güvenle yükleyin. Kayıt için yalnızca e-posta ve şifre yeterlidir.
              </p>

              {errorMsg && (
                <div className="auth-message error" role="alert">
                  {errorMsg}
                </div>
              )}

              <form onSubmit={handleSubmit} className="auth-form" noValidate>
                <div className={`input-group ${regFieldErrors.email ? 'has-error' : ''}`}>
                  <Mail className="input-icon" size={20} aria-hidden />
                  <input
                    id="reg-email"
                    type="email"
                    name="register-email"
                    autoComplete="email"
                    inputMode="email"
                    placeholder="ornek@eposta.com"
                    className="auth-input"
                    value={regEmail}
                    onChange={(e) => {
                      setRegEmail(e.target.value);
                      if (regFieldErrors.email) setRegFieldErrors((p) => ({ ...p, email: undefined }));
                    }}
                    aria-invalid={!!regFieldErrors.email}
                    aria-describedby={regFieldErrors.email ? 'reg-email-err' : undefined}
                  />
                </div>
                {regFieldErrors.email && (
                  <p id="reg-email-err" className="field-error">
                    {regFieldErrors.email}
                  </p>
                )}

                <div className={`input-group input-group-password ${regFieldErrors.password ? 'has-error' : ''}`}>
                  <Lock className="input-icon" size={20} aria-hidden />
                  <input
                    id="reg-password"
                    type={showRegPassword ? 'text' : 'password'}
                    name="register-password"
                    autoComplete="new-password"
                    placeholder="Şifre (en az 8 karakter)"
                    className="auth-input"
                    value={regPassword}
                    onChange={(e) => {
                      setRegPassword(e.target.value);
                      if (regFieldErrors.password) setRegFieldErrors((p) => ({ ...p, password: undefined }));
                    }}
                    aria-invalid={!!regFieldErrors.password}
                    aria-describedby="reg-password-hint reg-password-err"
                  />
                  <button
                    type="button"
                    className="input-suffix-btn"
                    aria-label={showRegPassword ? 'Şifreyi gizle' : 'Şifreyi göster'}
                    onClick={() => setShowRegPassword((v) => !v)}
                  >
                    {showRegPassword ? <EyeOff size={20} aria-hidden /> : <Eye size={20} aria-hidden />}
                  </button>
                </div>
                <p id="reg-password-hint" className="field-hint">
                  Harf, rakam ve mümkünse özel karakter kullanın. Minimum 8 karakter.
                </p>
                {regPassword.length > 0 && (
                  <div className="password-strength" aria-live="polite">
                    <div className="password-strength-track" role="presentation">
                      {[1, 2, 3].map((seg) => (
                        <div
                          key={seg}
                          className={`password-strength-seg ${regPwStrength.score >= seg ? `strength-${regPwStrength.score}` : ''}`}
                        />
                      ))}
                    </div>
                    {regPwStrength.label ? (
                      <span className="password-strength-label">Güvenlik: {regPwStrength.label}</span>
                    ) : null}
                  </div>
                )}
                {regFieldErrors.password && (
                  <p id="reg-password-err" className="field-error">
                    {regFieldErrors.password}
                  </p>
                )}

                <div className={`input-group input-group-password ${regFieldErrors.confirmPassword ? 'has-error' : ''}`}>
                  <Lock className="input-icon" size={20} aria-hidden />
                  <input
                    id="reg-confirm"
                    type={showRegConfirm ? 'text' : 'password'}
                    name="register-confirm"
                    autoComplete="new-password"
                    placeholder="Şifre tekrarı"
                    className="auth-input"
                    value={regConfirm}
                    onChange={(e) => {
                      setRegConfirm(e.target.value);
                      if (regFieldErrors.confirmPassword) setRegFieldErrors((p) => ({ ...p, confirmPassword: undefined }));
                    }}
                    aria-invalid={!!regFieldErrors.confirmPassword}
                    aria-describedby={regFieldErrors.confirmPassword ? 'reg-confirm-err' : undefined}
                  />
                  <button
                    type="button"
                    className="input-suffix-btn"
                    aria-label={showRegConfirm ? 'Şifre tekrarını gizle' : 'Şifre tekrarını göster'}
                    onClick={() => setShowRegConfirm((v) => !v)}
                  >
                    {showRegConfirm ? <EyeOff size={20} aria-hidden /> : <Eye size={20} aria-hidden />}
                  </button>
                </div>
                {regFieldErrors.confirmPassword && (
                  <p id="reg-confirm-err" className="field-error">
                    {regFieldErrors.confirmPassword}
                  </p>
                )}

                <label className={`terms-row ${regFieldErrors.terms ? 'has-error' : ''}`}>
                  <input
                    type="checkbox"
                    checked={acceptTerms}
                    onChange={(e) => {
                      setAcceptTerms(e.target.checked);
                      if (regFieldErrors.terms) setRegFieldErrors((p) => ({ ...p, terms: undefined }));
                    }}
                    aria-invalid={!!regFieldErrors.terms}
                  />
                  <span className="terms-text">
                    <span className="terms-em">Kullanım koşulları</span> ve{' '}
                    <span className="terms-em">gizlilik bildirimini</span> okudum ve kabul ediyorum.
                  </span>
                </label>
                {regFieldErrors.terms && <p className="field-error terms-error">{regFieldErrors.terms}</p>}

                <button type="submit" className="btn-primary auth-submit" disabled={loading}>
                  {loading ? (
                    <Loader className="spin" size={18} aria-hidden />
                  ) : (
                    <>Hesap oluştur <ArrowRight size={18} aria-hidden /></>
                  )}
                </button>
              </form>

              <p className="auth-footer">
                Zaten hesabınız var mı?{' '}
                <button type="button" className="text-btn highlight" onClick={() => changeView('login')}>
                  Giriş yap
                </button>
              </p>
            </div>
          )}

          {view === 'forgot-password' && (
            <div className="auth-view">
              <div className="icon-header">
                <KeyRound size={40} className="glow-icon" />
              </div>
              <h2 className="glow-text">Şifremi unuttum</h2>
              <p className="auth-subtitle">
                E-posta adresinizi girin. Şifre sıfırlama kodu oluşturulacaktır.
              </p>

              {errorMsg && <div className={`auth-message ${errorMsg.includes('alındı') ? 'success' : 'error'}`}>{errorMsg}</div>}

              <form onSubmit={handleSubmit} className="auth-form">
                <div className="input-group">
                  <Mail className="input-icon" size={20} />
                  <input type="email" placeholder="E-posta adresi" className="auth-input" required />
                </div>
                <button type="submit" className="btn-primary auth-submit" disabled={loading}>
                  {loading ? <Loader className="spin" size={18} /> : <>Devam et <ArrowRight size={18} /></>}
                </button>
              </form>

              <p className="auth-footer">
                <button type="button" className="text-btn highlight" onClick={() => changeView('login')}>
                  Giriş ekranına dön
                </button>
              </p>
            </div>
          )}

          {view === 'reset-password' && (
            <div className="auth-view">
              <div className="icon-header">
                <KeyRound size={40} className="glow-icon" />
              </div>
              <h2 className="glow-text">Yeni şifre</h2>
              <p className="auth-subtitle">Yeni şifreniz en az 8 karakter olmalıdır.</p>

              {errorMsg && (
                <div className={`auth-message ${errorMsg.includes('Geliştirme') ? 'success' : 'error'}`}>{errorMsg}</div>
              )}

              <form onSubmit={handleSubmit} className="auth-form">
                <div className="input-group">
                  <KeyRound className="input-icon" size={20} />
                  <input type="text" name="reset-token" placeholder="Sıfırlama kodu" className="auth-input" required />
                </div>
                <div className="input-group">
                  <Lock className="input-icon" size={20} />
                  <input type="password" name="new-password" placeholder="Yeni şifre" className="auth-input" required minLength={8} />
                </div>
                <div className="input-group">
                  <Lock className="input-icon" size={20} />
                  <input
                    type="password"
                    name="confirm-password"
                    placeholder="Yeni şifre (tekrar)"
                    className="auth-input"
                    required
                    minLength={8}
                  />
                </div>
                <button type="submit" className="btn-primary auth-submit" disabled={loading}>
                  {loading ? <Loader className="spin" size={18} /> : <>Şifreyi güncelle <ArrowRight size={18} /></>}
                </button>
              </form>

              <p className="auth-footer">
                <button type="button" className="text-btn highlight" onClick={() => changeView('login')}>
                  Giriş ekranına dön
                </button>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
