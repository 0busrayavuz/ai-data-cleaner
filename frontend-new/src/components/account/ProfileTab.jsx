import React, { useState } from 'react';
import { Mail, Calendar, Loader, CheckCircle2, AlertCircle, Edit3, Award, Briefcase } from 'lucide-react';
import { updateProfile } from '../../services/api';

function getInitial(name, email) {
  const displayStr = name || email || '?';
  return displayStr.trim().slice(0, 1).toLocaleUpperCase('tr-TR');
}

export const ProfileTab = ({ account, onProfileUpdated }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(account?.user?.full_name || '');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const profileEmail = account?.user?.email || '';
  const profileName = account?.user?.full_name || '';

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const data = await updateProfile(fullName);
      setMessage({ type: 'success', text: data.message });
      setIsEditing(false);
      onProfileUpdated(data.full_name);
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Profil güncellenemedi.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="account-section">
      <div className="account-section-header">
        <h3>Profil bilgileri</h3>
        <p>Hesabınızın sistemde kayıtlı temel kimlik bilgileri.</p>
      </div>

      {message && (
        <div className={`account-inline-message ${message.type}`} role="alert">
          {message.type === 'success' ? <CheckCircle2 size={17} /> : <AlertCircle size={17} />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="account-avatar-row">
        <div className="account-avatar-circle">{getInitial(profileName, profileEmail)}</div>
        <div className="account-avatar-info">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <strong>{profileName || profileEmail}</strong>
            {!isEditing && (
              <button 
                type="button" 
                className="account-edit-btn" 
                onClick={() => setIsEditing(true)}
                title="Adı Düzenle"
              >
                <Edit3 size={14} />
              </button>
            )}
          </div>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)' }}>
            <Award size={14} /> Üyelik: Standart Plan
          </span>
        </div>
      </div>

      {isEditing && (
        <form className="account-profile-form" onSubmit={handleSave} style={{ marginBottom: '24px', background: 'var(--bg-card)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <label className="account-field">
            <span>Ad Soyad</span>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Adınızı girin..."
              disabled={saving}
              autoFocus
            />
          </label>
          <div className="form-actions" style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
            <button type="submit" className="btn-primary account-submit-btn" disabled={saving}>
              {saving ? <Loader className="spin" size={16} /> : 'Kaydet'}
            </button>
            <button type="button" className="btn-secondary account-secondary-btn" onClick={() => setIsEditing(false)} disabled={saving}>
              İptal
            </button>
          </div>
        </form>
      )}

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
            <strong>{account?.user?.created_at ? new Date(account.user.created_at).toLocaleString('tr-TR') : 'Bilinmiyor'}</strong>
          </div>
        </div>
        <div className="account-info-box">
          <Briefcase size={18} />
          <div className="info-box-content">
            <span>Kullanıcı Tipi</span>
            <strong>Bireysel Kullanıcı</strong>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileTab;
