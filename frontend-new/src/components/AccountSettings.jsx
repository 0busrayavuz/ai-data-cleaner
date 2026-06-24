import { useEffect, useState } from 'react';
import {
  AlertCircle,
  Database,
  Loader,
  LogOut,
  RefreshCw,
  ShieldCheck,
  UserRound,
  BarChart2
} from 'lucide-react';
import { fetchAccountSummary } from '../services/api';
import './AccountSettings.css';

import ProfileTab from './account/ProfileTab';
import SecurityTab from './account/SecurityTab';
import UsageTab from './account/UsageTab';

const AccountSettings = ({ userEmail, onOpenPanel, onLogout }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [account, setAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sessionLabel, setSessionLabel] = useState('Aktif oturum bulunamadı');

  const checkSession = () => {
    if (localStorage.getItem('token')) setSessionLabel('Bu tarayıcıda hatırlanıyor');
    else if (sessionStorage.getItem('token')) setSessionLabel('Yalnızca bu sekmede saklanıyor');
    else setSessionLabel('Aktif oturum bulunamadı');
  };

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
    checkSession();
    // Dinamik sekme geçişlerinde vs session'ı kontrol edebilmek için event listener
    window.addEventListener('storage', checkSession);
    return () => window.removeEventListener('storage', checkSession);
  }, []);

  const handleProfileUpdated = (newFullName) => {
    setAccount(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        user: {
          ...prev.user,
          full_name: newFullName
        }
      };
    });
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
                <ProfileTab 
                  account={account} 
                  getSessionLabel={() => sessionLabel} 
                  onProfileUpdated={handleProfileUpdated}
                />
              )}
              {activeTab === 'security' && (
                <SecurityTab limits={account?.limits} />
              )}
              {activeTab === 'usage' && (
                <UsageTab usage={account?.usage} />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default AccountSettings;
