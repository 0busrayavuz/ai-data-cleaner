import React, { useMemo } from 'react';
import { Folder, Database, CheckCircle2, WandSparkles, FileText, Clock } from 'lucide-react';

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

export const UsageTab = ({ usage }) => {
  const usageCards = useMemo(() => ([
    { label: 'Proje', value: usage?.project_count, icon: Folder },
    { label: 'Veri seti', value: usage?.dataset_count, icon: Database },
    { label: 'Temiz çıktı', value: usage?.cleaned_dataset_count, icon: CheckCircle2 },
    { label: 'Şablon', value: usage?.template_count, icon: WandSparkles },
    { label: 'İşlenen satır', value: usage?.total_rows_processed, icon: FileText },
    { label: 'Son yükleme', value: formatDate(usage?.last_upload_time), icon: Clock, isText: true },
  ]), [usage]);

  return (
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
  );
};

export default UsageTab;
