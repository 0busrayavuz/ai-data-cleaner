import { Activity, Database, Clock, Download, ChevronRight } from 'lucide-react';
import './UserDashboard.css';

const MOCK_HISTORY = [];

const UserDashboard = () => {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h2 className="glow-text">Analiz Paneliniz</h2>
        <p className="dashboard-subtitle">Geçmiş temizlik raporlarınıza ve veri istatistiklerinize buradan ulaşabilirsiniz.</p>
      </header>

      <section className="dashboard-stats">
        <div className="stat-card glass-panel">
          <div className="stat-icon-wrapper blue">
            <Database size={24} />
          </div>
          <div className="stat-info">
            <h3>Toplam İşlenen Satır</h3>
            <p className="stat-value">0</p>
          </div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-icon-wrapper purple">
            <Activity size={24} />
          </div>
          <div className="stat-info">
            <h3>Temizlenen Veri Seti</h3>
            <p className="stat-value">0</p>
          </div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-icon-wrapper pink">
            <Clock size={24} />
          </div>
          <div className="stat-info">
            <h3>Kurtarılan Zaman</h3>
            <p className="stat-value">0 Saat</p>
          </div>
        </div>
      </section>

      <section className="dashboard-history">
        <div className="history-header">
          <h3>Geçmiş Analizler</h3>
          <button className="text-btn highlight">Tümünü Gör <ChevronRight size={16}/></button>
        </div>
        
        <div className="history-table-container glass-panel">
          <table className="history-table">
            <thead>
              <tr>
                <th>Dosya Adı</th>
                <th>Tarih</th>
                <th>Satır Sayısı</th>
                <th>Durum</th>
                <th>İşlem</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_HISTORY.length > 0 ? (
                MOCK_HISTORY.map((item) => (
                  <tr key={item.id}>
                    <td className="file-name">
                      <Database size={16} className="file-icon" />
                      {item.name}
                    </td>
                    <td>{item.date}</td>
                    <td>{item.rows.toLocaleString()}</td>
                    <td>
                      <span className={`status-badge ${item.status === 'Temizlendi' ? 'success' : 'warning'}`}>
                        {item.status}
                      </span>
                    </td>
                    <td>
                      {item.status === 'Temizlendi' ? (
                        <button className="action-btn download">
                          <Download size={16} /> İndir
                        </button>
                      ) : (
                        <button className="action-btn continue">
                          Devam Et
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                    Henüz hiçbir veri temizleme işlemi yapmadınız. Yeni bir dosya yükleyerek başlayabilirsiniz.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

export default UserDashboard;
