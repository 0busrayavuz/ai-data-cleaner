import {
  Activity,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  GitCompareArrows,
  TableProperties,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatValue } from './utils';

export default function ComparisonView({ comparison, onOpenStudio }) {
  if (!comparison) {
    return (
      <section className="workspace-empty glass-panel">
        <GitCompareArrows size={36} />
        <h3>Karşılaştırma henüz hazır değil</h3>
        <p>Önce Temizlik Stüdyosu'nda en az bir işlem uygulayın. Ham veri değiştirilmeden korunacaktır.</p>
        <button type="button" className="btn-primary" onClick={onOpenStudio}>
          Temizlik Stüdyosu'na git <ArrowRight size={17} />
        </button>
      </section>
    );
  }

  const healthChart = [
    { name: 'Eksik', before: comparison.health.before.missing, after: comparison.health.after.missing },
    { name: 'Aykırı', before: comparison.health.before.outliers, after: comparison.health.after.outliers },
    { name: 'Format', before: comparison.health.before.format, after: comparison.health.after.format },
  ];
  const improvement = comparison.health.after_score - comparison.health.before_score;
  const improvementText =
    improvement > 0
      ? `+${formatValue(improvement)} puan gelişim`
      : improvement < 0
      ? `${formatValue(improvement)} puan düşüş`
      : '0 puan değişim';

  return (
    <div className="workspace-comparison">
      <section className="comparison-score-grid">
        <div className="comparison-score before glass-panel">
          <span>İşlem öncesi</span>
          <strong>%{formatValue(comparison.health.before_score)}</strong>
          <small>Başlangıç kalite puanı</small>
        </div>
        <div className="comparison-arrow"><ArrowRight size={25} /></div>
        <div className="comparison-score after glass-panel">
          <span>İşlem sonrası</span>
          <strong>%{formatValue(comparison.health.after_score)}</strong>
          <small>{improvementText}</small>
        </div>
        <div className="comparison-score changes glass-panel">
          <span>Değişen hücre</span>
          <strong>
            {comparison.total_changed_cells == null ? '—' : formatValue(comparison.total_changed_cells)}
          </strong>
          <small>
            {comparison.rows_aligned
              ? 'Satırlar aynı konumda karşılaştırıldı'
              : 'Satır silindiği için hücre bazında sayılmadı'}
          </small>
        </div>
      </section>

      <section className="comparison-health-note glass-panel">
        <div>
          <span><Activity size={18} /> Sağlık skoru nasıl okunur?</span>
          <p>
            Skor, toplam hücre sayısına göre eksik veri, format problemi ve aykırı değerlerin ağırlıklı
            cezası çıkarılarak hesaplanır. Aykırı değerler hata olmak zorunda olmadığı için daha düşük
            ağırlıkla değerlendirilir. Satır silme varsa ayrıca her %1 silme için 0.5 puan ceza uygulanır.
          </p>
        </div>
        <div className="comparison-weight-list" aria-label="Health score ağırlıkları">
          <span>Eksik veri x{comparison.weights.missing}</span>
          <span>Format x{comparison.weights.format}</span>
          <span>Aykırı değer x{comparison.weights.outlier}</span>
          {comparison.health.row_delete_penalty > 0 && (
            <span>Satır silme -{formatValue(comparison.health.row_delete_penalty)} puan</span>
          )}
        </div>
      </section>

      <section className="comparison-main-grid">
        <div className="comparison-chart glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>Kalite bileşenleri</span>
              <h3>Sorun sayısı değişimi</h3>
            </div>
            <BarChart3 size={20} color="#00aeef" />
          </div>
          <ResponsiveContainer width="100%" height={310}>
            <BarChart data={healthChart} margin={{ top: 18, right: 12, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(11, 26, 56, 0.08)" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  borderRadius: 10,
                  border: '1px solid rgba(12,143,114,0.15)',
                  background: 'rgba(255,255,255,0.97)',
                  fontSize: 12,
                }}
              />
              <Bar dataKey="before" name="Önce" fill="#e07a5f" radius={[6, 6, 0, 0]} />
              <Bar dataKey="after"  name="Sonra" fill="#00aeef" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <p className="comparison-method-note">
            Aykırı değerler önce ve sonra aynı başlangıç IQR sınırlarına göre ölçülür.
            Ağırlıklar: eksik {comparison.weights.missing}, format {comparison.weights.format},
            aykırı {comparison.weights.outlier}.
          </p>
        </div>

        <div className="comparison-structure glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>Yapısal etki</span>
              <h3>Tablo boyutu</h3>
            </div>
            <TableProperties size={20} color="#00aeef" />
          </div>
          <div className="comparison-structure-row">
            <span>Satır</span>
            <strong>{formatValue(comparison.before_rows)}</strong>
            <ArrowRight size={15} />
            <strong>{formatValue(comparison.after_rows)}</strong>
          </div>
          <div className="comparison-structure-row">
            <span>Sütun</span>
            <strong>{formatValue(comparison.before_columns)}</strong>
            <ArrowRight size={15} />
            <strong>{formatValue(comparison.after_columns)}</strong>
          </div>
          <div className="comparison-structure-callout">
            <CheckCircle2 size={20} />
            <p>Ham dosya korunur; temizlenmiş veri ayrı bir çıktı olarak oluşturulur.</p>
          </div>
        </div>
      </section>

      <section className="comparison-table-card glass-panel">
        <div className="workspace-panel-heading">
          <div>
            <span>Sütun etkisi</span>
            <h3>Önce / sonra istatistikleri</h3>
          </div>
        </div>
        <div className="workspace-table-scroll">
          <table className="workspace-data-table">
            <thead>
              <tr>
                <th>Sütun</th><th>Tür</th>
                <th>Eksik (önce)</th><th>Eksik (sonra)</th>
                <th>Ortalama (önce)</th><th>Ortalama (sonra)</th>
                <th>Değişen hücre</th>
              </tr>
            </thead>
            <tbody>
              {comparison.columns.map((column) => (
                <tr key={column.name}>
                  <td><strong>{column.name}</strong></td>
                  <td>
                    <span className={`workspace-kind ${column.kind}`}>
                      {column.kind === 'numeric' ? 'Sayısal' : 'Kategorik'}
                    </span>
                  </td>
                  <td>{formatValue(column.before_missing)}</td>
                  <td>{formatValue(column.after_missing)}</td>
                  <td>{formatValue(column.before_mean)}</td>
                  <td>{formatValue(column.after_mean)}</td>
                  <td>{column.changed_cells == null ? '—' : formatValue(column.changed_cells)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {comparison.changed_samples.length > 0 && (
        <section className="comparison-table-card glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>Değişiklik örnekleri</span>
              <h3>İlk {comparison.changed_samples.length} değişiklik</h3>
            </div>
          </div>
          <div className="workspace-table-scroll">
            <table className="workspace-data-table">
              <thead>
                <tr><th>Satır</th><th>Sütun</th><th>Önce</th><th>Sonra</th></tr>
              </thead>
              <tbody>
                {comparison.changed_samples.map((item, index) => (
                  <tr key={`${item.row}-${item.column}-${index}`}>
                    <td>{item.row}</td>
                    <td><strong>{item.column}</strong></td>
                    <td className="comparison-old">{formatValue(item.before)}</td>
                    <td className="comparison-new">{formatValue(item.after)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
