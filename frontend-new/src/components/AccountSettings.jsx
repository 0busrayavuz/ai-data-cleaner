import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  Database,
  FileText,
  Folder,
  KeyRound,
  Loader,
  Lock,
  LogOut,
  Mail,
  RefreshCw,
  ShieldCheck,
  UserRound,
  WandSparkles,
  BarChart2
} from 'lucide-react';
import { changePassword, fetchAccountSummary } from '../services/api';
import './AccountSettings.css';

const STATUS_LABELS = {
  ready: 'Analiz hazır',
  analyzing: 'Analiz ediliyor',
  processing: 'Temizleniyor',
  cleaned: 'Temizlendi',
  error: 'Hata',
};

function formatDate(value) {
  if (!value) return 'Henüz yok';
  try {
    return new Date(value).toLocaleString('tr-TR');
  } catch {
    return value;
  }
}

function formatNumber(value) {
  const num = Number(value || 0);
  if (Number.isNaN(num) || !Number.isFinite(num)) return '0';
  return num.toLocaleString('tr-TR');
}

function getSessionLabel() {
  if (localStorage.getItem('token')) return 'Bu tarayıcıda hatırlanıyor';
  if (sessionStorage.getItem('token')) return 'Yalnızca bu sekmede saklanıyor';
  return 'Aktif oturum bulunamadı';
}

function getInitial(email) {
  return (email || '?').trim().slice(0, 1).toLocaleUpperCase('tr-TR');
}

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

const AccountSettings = ({ userEmail, onOpenPanel, onLogout }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [account, setAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [passwordMessage, setPasswordMessage] = useState(null);
  const [changingPassword, setChangingPassword] = useState(false);

  const loadAccount = async () => {
    setLoading(true);
    try {
      const data = await fetchAccountSummary();
      setAccount(data);
      setError('');
    } catch (e) {
      setError(e.message || 'Hesap bilgileri yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAccount();
  }, []);

  const profileEmail = account?.user?.email || userEmail || '';
  const usage = account?.usage;
  const limits = account?.limits;
  const strength = passwordStrengthLabel(form.newPassword);

  const usageCards = useMemo(() => ([
    { label: 'Proje', value: usage?.project_count, icon: Folder },
    { label: 'Veri seti', value: usage?.dataset_count, icon: Database },
    { label: 'Temiz çıktı', value: usage?.cleaned_dataset_count, icon: CheckCircle2 },
    { label: 'Şablon', value: usage?.template_count, icon: WandSparkles },
    { label: 'İşlenen satır', value: usage?.total_rows_processed, icon: FileText },
    { label: 'Son yükleme', value: formatDate(usage?.last_upload_time), icon: Clock, isText: true },
  ]), [usage]);

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
    <div className="account-container">
      <div className="account-header">
        <div>
          <h2>Hesap Ayarları</h2>
          <p>Kişisel bilgilerinizi, güvenlik ayarlarınızı ve kullanım özetinizi yönetin.</p>
        </div>
        <div className="account-header-actions">
          <button type="button" className="account-secondary-btn" onClick={onOpenPanel}>
            <Database size={16} aria-hidden /> Panel
          </button>
          <button type="button" className="account-danger-btn" onClick={onLogout}>
            <LogOut size={16} aria-hidden /> Çıkış yap
          </button>
        </div>
      </div>

      {error && (
        <div className="account-alert error" role="alert">
          <AlertCircle size={18} aria-hidden />
          <span>{error}</span>
          <button type="button" onClick={loadAccount}>
            <RefreshCw size={15} aria-hidden /> Tekrar dene
          </button>
        </div>
      )}

      <div className="account-layout">
        {/* Sol Menü (Sidebar) */}
        <nav className="account-sidebar" aria-label="Hesap menüsü">
          <button
            type="button"
            className={`account-tab ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            <UserRound size={18} aria-hidden /> Profil
          </button>
          <button
            type="button"
            className={`account-tab ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            <ShieldCheck size={18} aria-hidden /> Güvenlik
          </button>
          <button
            type="button"
            className={`account-tab ${activeTab === 'usage' ? 'active' : ''}`}
            onClick={() => setActiveTab('usage')}
          >
            <BarChart2 size={18} aria-hidden /> Kullanım Özeti
          </button>
        </nav>

        {/* Sağ İçerik */}
        <main className="account-content glass-panel">
          {loading ? (
            <div className="account-loading">
              <Loader className="spin" size={24} />
              <p>Bilgiler yükleniyor...</p>
            </div>
          ) : (
            <>
              {activeTab === 'profile' && (
                <div className="account-section">
                  <div className="account-section-header">
                    <h3>Profil bilgileri</h3>
                    <p>Hesabınızın sistemde kayıtlı temel kimlik bilgileri.</p>
                  </div>
                  <div className="account-avatar-row">
                    <div className="account-avatar-circle">{getInitial(profileEmail)}</div>
                    <div className="account-avatar-info">
                      <strong>{profileEmail || 'Bilinmeyen Kullanıcı'}</strong>
                      <span>Kullanıcı ID: #{account?.user?.id ?? '-'}</span>
                    </div>
                  </div>
                  
                  <div className="account-info-grid">
                    <div className="account-info-box">
                      <Mail size={18} />
                      <div className="info-box-content">
                        <span>E-posta adresi</span>
                        <strong>{profileEmail || 'E-posta bulunamadı'}</strong>
                      </div>
                    </div>
                    <div className="account-info-box">
                      <Calendar size={18} />
                      <div className="info-box-content">
                        <span>Kayıt tarihi</span>
                        <strong>{formatDate(account?.user?.created_at)}</strong>
                      </div>
                    </div>
                    <div className="account-info-box">
                      <Lock size={18} />
                      <div className="info-box-content">
                        <span>Oturum durumu</span>
                        <strong>{getSessionLabel()}</strong>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'security' && (
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
                        <span className="limit-value">{limits?.max_upload_mb || 20} MB</span>
                      </li>
                      <li>
                        <span className="limit-label">Desteklenen formatlar</span>
                        <span className="limit-value">{(limits?.supported_formats || ['CSV', 'XLSX', 'TXT']).join(', ')}</span>
                      </li>
                      <li>
                        <span className="limit-label">Veri sahipliği</span>
                        <span className="limit-value">Yalnızca oturumdaki kullanıcıya görünür.</span>
                      </li>
                    </ul>
                  </div>
                </div>
              )}

              {activeTab === 'usage' && (
                <div className="account-section">
                  <div className="account-section-header">
                    <h3>Kullanım özeti</h3>
                    <p>Hesabınızda gerçekleştirilen analiz ve işlemlerin toplam değerleri.</p>
                  </div>

                  <div className="account-metrics-grid">
                    {usageCards.map((item) => {
                      const Icon = item.icon;
                      return (
                        <div className="account-metric-card" key={item.label}>
                          <div className="metric-icon"><Icon size={18} aria-hidden /></div>
                          <div className="metric-content">
                            <span>{item.label}</span>
                            <strong>{item.isText ? item.value : formatNumber(item.value)}</strong>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {usage?.status_counts && Object.keys(usage.status_counts).length > 0 && (
                    <div className="account-status-summary">
                      <h4>Veri seti durumları</h4>
                      <div className="account-status-strip">
                        {Object.entries(usage.status_counts).map(([key, value]) => (
                          <span key={key}>
                            {STATUS_LABELS[key] || key}: <strong>{value}</strong>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default AccountSettings;
