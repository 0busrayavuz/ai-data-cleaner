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
  return Number(value || 0).toLocaleString('tr-TR');
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
      <header className="account-hero glass-panel">
        <div className="account-avatar" aria-hidden>{getInitial(profileEmail)}</div>
        <div className="account-hero-copy">
          <span className="account-overline">Hesabım</span>
          <h2>Hesap ve güvenlik ayarları</h2>
          <p>
            Giriş bilgilerinizi, oturum durumunuzu ve VeriTemiz AI kullanım özetinizi buradan yönetin.
          </p>
        </div>
        <div className="account-hero-actions">
          <button type="button" className="account-secondary-btn" onClick={onOpenPanel}>
            <Database size={17} aria-hidden />
            Paneli aç
          </button>
          <button type="button" className="account-danger-btn" onClick={onLogout}>
            <LogOut size={17} aria-hidden />
            Çıkış yap
          </button>
        </div>
      </header>

      {error && (
        <div className="account-alert error" role="alert">
          <AlertCircle size={18} aria-hidden />
          <span>{error}</span>
          <button type="button" onClick={loadAccount}>
            <RefreshCw size={15} aria-hidden />
            Tekrar dene
          </button>
        </div>
      )}

      <div className="account-layout">
        <section className="account-card glass-panel">
          <div className="account-card-header">
            <div className="account-card-icon">
              <UserRound size={21} aria-hidden />
            </div>
            <div>
              <h3>Profil bilgileri</h3>
              <p>Hesabın sistemde kayıtlı gerçek bilgileri.</p>
            </div>
          </div>

          {loading ? (
            <p className="account-muted">Hesap bilgileri yükleniyor...</p>
          ) : (
            <div className="account-info-list">
              <div className="account-info-row">
                <Mail size={18} aria-hidden />
                <div>
                  <span>E-posta adresi</span>
                  <strong>{profileEmail || 'E-posta bulunamadı'}</strong>
                  <small>Bu adres şu an giriş kimliğiniz olarak kullanılır.</small>
                </div>
              </div>
              <div className="account-info-row">
                <ShieldCheck size={18} aria-hidden />
                <div>
                  <span>Kullanıcı numarası</span>
                  <strong>#{account?.user?.id ?? '-'}</strong>
                  <small>Veri seti sahipliği bu kullanıcı kaydıyla eşleştirilir.</small>
                </div>
              </div>
              <div className="account-info-row">
                <Calendar size={18} aria-hidden />
                <div>
                  <span>Kayıt tarihi</span>
                  <strong>{formatDate(account?.user?.created_at)}</strong>
                </div>
              </div>
              <div className="account-info-row">
                <Lock size={18} aria-hidden />
                <div>
                  <span>Oturum durumu</span>
                  <strong>{getSessionLabel()}</strong>
                </div>
              </div>
            </div>
          )}
        </section>

        <section className="account-card glass-panel">
          <div className="account-card-header">
            <div className="account-card-icon">
              <Database size={21} aria-hidden />
            </div>
            <div>
              <h3>Kullanım özeti</h3>
              <p>Panel ve analiz geçmişinden hesaplanan güncel değerler.</p>
            </div>
          </div>

          {loading ? (
            <p className="account-muted">Kullanım özeti yükleniyor...</p>
          ) : (
            <>
              <div className="account-metrics">
                {usageCards.map((item) => {
                  const Icon = item.icon;
                  return (
                    <div className="account-metric" key={item.label}>
                      <Icon size={18} aria-hidden />
                      <span>{item.label}</span>
                      <strong>{item.isText ? item.value : formatNumber(item.value)}</strong>
                    </div>
                  );
                })}
              </div>

              {usage?.status_counts && Object.keys(usage.status_counts).length > 0 && (
                <div className="account-status-strip" aria-label="Veri seti durumları">
                  {Object.entries(usage.status_counts).map(([key, value]) => (
                    <span key={key}>
                      {STATUS_LABELS[key] || key}: <strong>{value}</strong>
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
        </section>

        <section className="account-card account-security-card glass-panel">
          <div className="account-card-header">
            <div className="account-card-icon">
              <KeyRound size={21} aria-hidden />
            </div>
            <div>
              <h3>Şifre değiştir</h3>
              <p>Yeni şifre kaydedilmeden önce mevcut şifreniz doğrulanır.</p>
            </div>
          </div>

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

            <button type="submit" className="btn-primary account-submit-btn" disabled={changingPassword}>
              {changingPassword ? <Loader className="spin" size={18} aria-hidden /> : <KeyRound size={18} aria-hidden />}
              Şifreyi güncelle
            </button>
          </form>
        </section>

        <section className="account-card glass-panel">
          <div className="account-card-header">
            <div className="account-card-icon">
              <ShieldCheck size={21} aria-hidden />
            </div>
            <div>
              <h3>Hesap sınırları ve güvenlik</h3>
              <p>Bu alan proje davranışına bağlı gerçek kuralları gösterir.</p>
            </div>
          </div>

          <div className="account-policy-list">
            <div>
              <span>Yükleme sınırı</span>
              <strong>{limits?.max_upload_mb || 20} MB</strong>
            </div>
            <div>
              <span>Desteklenen formatlar</span>
              <strong>{(limits?.supported_formats || ['CSV', 'XLSX', 'TXT']).join(', ')}</strong>
            </div>
            <div>
              <span>Ham dosya davranışı</span>
              <strong>Temiz çıktı ayrı dosya olarak oluşturulur.</strong>
            </div>
            <div>
              <span>Veri sahipliği</span>
              <strong>Veri setleri yalnızca oturumdaki kullanıcıya görünür.</strong>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AccountSettings;
