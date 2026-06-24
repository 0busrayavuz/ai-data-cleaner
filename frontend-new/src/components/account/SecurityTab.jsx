import React, { useState } from 'react';
import { KeyRound, CheckCircle2, AlertCircle, Loader } from 'lucide-react';
import { changePassword } from '../../services/api';

function passwordStrengthLabel(password) {
  if (!password) return '';
  let score = 0;
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[a-zçğıöşü]/.test(password) && /[A-ZÇĞİÖŞÜ]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]/.test(password)) score += 1;
  if (score >= 4) return 'Güçlü';
  if (score >= 2) return 'Orta';
  return 'Zayıf';
}

export const SecurityTab = ({ limits }) => {
  const [form, setForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [passwordMessage, setPasswordMessage] = useState(null);
  const [changingPassword, setChangingPassword] = useState(false);

  const strength = passwordStrengthLabel(form.newPassword);

  const setFormValue = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setPasswordMessage(null);
    if (fieldErrors[key]) {
      setFieldErrors((prev) => ({ ...prev, [key]: undefined }));
    }
  };

  const validatePasswordForm = () => {
    const next = {};
    if (!form.currentPassword) next.currentPassword = 'Mevcut şifre gerekli.';
    if (!form.newPassword) next.newPassword = 'Yeni şifre gerekli.';
    else if (form.newPassword.length < 8) next.newPassword = 'Yeni şifre en az 8 karakter olmalı.';
    else if (form.newPassword === form.currentPassword) next.newPassword = 'Yeni şifre mevcut şifreyle aynı olamaz.';
    if (!form.confirmPassword) next.confirmPassword = 'Yeni şifre tekrarını girin.';
    else if (form.confirmPassword !== form.newPassword) next.confirmPassword = 'Şifreler eşleşmiyor.';
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  };

  const handlePasswordSubmit = async (event) => {
    event.preventDefault();
    setPasswordMessage(null);
    if (!validatePasswordForm()) return;

    setChangingPassword(true);
    try {
      const data = await changePassword(form.currentPassword, form.newPassword);
      setForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setPasswordMessage({ type: 'success', text: data.message || 'Şifreniz güncellendi.' });
    } catch (e) {
      setPasswordMessage({ type: 'error', text: e.message || 'Şifre güncellenemedi.' });
    } finally {
      setChangingPassword(false);
    }
  };

  return (
    <div className="account-section">
      <div className="account-section-header">
        <h3>Güvenlik ayarları</h3>
        <p>Şifrenizi güncelleyin ve hesap sınırlarınızı inceleyin.</p>
      </div>

      <div className="account-password-area">
        <h4>Şifre değiştir</h4>
        {passwordMessage && (
          <div className={`account-inline-message ${passwordMessage.type}`} role="alert">
            {passwordMessage.type === 'success' ? <CheckCircle2 size={17} /> : <AlertCircle size={17} />}
            <span>{passwordMessage.text}</span>
          </div>
        )}
        <form className="account-password-form" onSubmit={handlePasswordSubmit} noValidate>
          <label className="account-field">
            <span>Mevcut şifre</span>
            <input
              type="password"
              autoComplete="current-password"
              value={form.currentPassword}
              onChange={(e) => setFormValue('currentPassword', e.target.value)}
              aria-invalid={!!fieldErrors.currentPassword}
            />
            {fieldErrors.currentPassword && <small>{fieldErrors.currentPassword}</small>}
          </label>

          <label className="account-field">
            <span>Yeni şifre</span>
            <input
              type="password"
              autoComplete="new-password"
              value={form.newPassword}
              onChange={(e) => setFormValue('newPassword', e.target.value)}
              aria-invalid={!!fieldErrors.newPassword}
            />
            {strength && <em>Güvenlik düzeyi: {strength}</em>}
            {fieldErrors.newPassword && <small>{fieldErrors.newPassword}</small>}
          </label>

          <label className="account-field">
            <span>Yeni şifre tekrar</span>
            <input
              type="password"
              autoComplete="new-password"
              value={form.confirmPassword}
              onChange={(e) => setFormValue('confirmPassword', e.target.value)}
              aria-invalid={!!fieldErrors.confirmPassword}
            />
            {fieldErrors.confirmPassword && <small>{fieldErrors.confirmPassword}</small>}
          </label>

          <div className="form-actions">
            <button type="submit" className="btn-primary account-submit-btn" disabled={changingPassword}>
              {changingPassword ? <Loader className="spin" size={16} aria-hidden /> : <KeyRound size={16} aria-hidden />}
              Şifreyi güncelle
            </button>
          </div>
        </form>
      </div>

      <div className="account-limits-area">
        <h4>Hesap sınırları</h4>
        <ul className="account-limits-list">
          <li>
            <span className="limit-label">Yükleme sınırı</span>
            <span className="limit-value">{limits?.max_upload_mb ? `${limits.max_upload_mb} MB` : 'Bilinmiyor'}</span>
          </li>
          <li>
            <span className="limit-label">Desteklenen formatlar</span>
            <span className="limit-value">{limits?.supported_formats ? limits.supported_formats.join(', ') : 'Tümü'}</span>
          </li>
          <li>
            <span className="limit-label">Veri sahipliği</span>
            <span className="limit-value">Yalnızca oturumdaki kullanıcıya görünür.</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default SecurityTab;
