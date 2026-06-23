import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  ArrowRight,
  Columns3,
  Database,
  Rows3,
  TableProperties,
  TriangleAlert,
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
import { formatValue, numberFormat } from './utils';

/* ── AnimatedCounter ─────────────────────────────────────────────────────── */
function AnimatedCounter({ value, duration = 900 }) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef(null);

  useEffect(() => {
    const target = Number(value) || 0;
    const start = Date.now();
    const startVal = 0;

    const tick = () => {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(startVal + (target - startVal) * eased);
      setDisplay(current);
      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [value, duration]);

  return <>{numberFormat.format(display)}</>;
}

/* ── MetricCard ──────────────────────────────────────────────────────────── */
function MetricCard({ icon: Icon, label, value, tone, animate = false }) {
  return (
    <div className={`workspace-metric glass-panel ${tone}`}>
      <span><Icon size={21} /></span>
      <div>
        <small>{label}</small>
        <strong>
          {animate ? <AnimatedCounter value={value} /> : formatValue(value)}
        </strong>
      </div>
    </div>
  );
}

/* ── PreviewTable ────────────────────────────────────────────────────────── */
function PreviewTable({ title, rows }) {
  const columns = useMemo(() => Object.keys(rows?.[0] || {}), [rows]);
  return (
    <div className="workspace-preview glass-panel">
      <div className="workspace-panel-heading">
        <div><span>İlk kayıtlar</span><h3>{title}</h3></div>
        <Database size={20} color="#00aeef" />
      </div>
      {rows?.length ? (
        <div className="workspace-table-scroll">
          <table className="workspace-data-table compact">
            <thead>
              <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => <td key={column}>{formatValue(row[column])}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="workspace-muted">Ön izleme için kayıt yok.</p>
      )}
    </div>
  );
}

/* ── ProfileView ─────────────────────────────────────────────────────────── */
export default function ProfileView({ profile, selectedColumn, onSelectColumn }) {
  const column = profile.columns.find((item) => item.name === selectedColumn) || profile.columns[0];
  const chartData = column?.kind === 'numeric' ? column.distribution : column?.top_values;
  const chartTitle = column?.kind === 'numeric' ? 'Değer dağılımı' : 'En sık değerler';

  return (
    <div className="workspace-profile">
      <section className="workspace-metrics">
        <MetricCard icon={Rows3} label="Başlangıç satır" value={profile.row_count} tone="emerald" animate />
        <MetricCard icon={Columns3} label="Başlangıç sütun" value={profile.col_count} tone="blue" animate />
        <MetricCard icon={TriangleAlert} label="Orijinal eksik hücre" value={profile.missing_cells} tone="amber" animate />
        <MetricCard icon={TableProperties} label="İlk tekrar eden satır" value={profile.duplicate_rows} tone="purple" animate />
      </section>

      <section className="workspace-profile-grid">
        <div className="workspace-column-list glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>Sütun kataloğu</span>
              <h3>{profile.columns.length} değişken</h3>
            </div>
          </div>
          <div className="workspace-column-scroll">
            {profile.columns.map((item) => (
              <button
                key={item.name}
                type="button"
                className={item.name === column?.name ? 'active' : ''}
                onClick={() => onSelectColumn(item.name)}
              >
                <span>
                  <strong>{item.name}</strong>
                  <small>{item.dtype}</small>
                </span>
                <span className={`workspace-kind ${item.kind}`}>
                  {item.kind === 'numeric' ? 'Sayısal' : 'Kategorik'}
                </span>
                <i style={{ '--complete': `${100 - item.missing_pct}%` }} />
                <small>%{numberFormat.format(item.missing_pct)} eksik</small>
              </button>
            ))}
          </div>
        </div>

        <div className="workspace-column-detail glass-panel">
          {column && (
            <>
              <div className="workspace-panel-heading">
                <div>
                  <span>Seçili sütun</span>
                  <h3>{column.name}</h3>
                </div>
                <span className={`workspace-kind ${column.kind}`}>
                  {column.kind === 'numeric' ? 'Sayısal' : 'Kategorik'}
                </span>
              </div>
              <div className="workspace-detail-stats">
                <div><span>Eksik</span><strong>{formatValue(column.missing_count)}</strong></div>
                <div><span>Benzersiz</span><strong>{formatValue(column.unique_count)}</strong></div>
                {column.kind === 'numeric' && (
                  <>
                    <div><span>Ortalama</span><strong>{formatValue(column.stats?.mean)}</strong></div>
                    <div><span>Medyan</span><strong>{formatValue(column.stats?.median)}</strong></div>
                    <div><span>Minimum</span><strong>{formatValue(column.stats?.min)}</strong></div>
                    <div><span>Maksimum</span><strong>{formatValue(column.stats?.max)}</strong></div>
                  </>
                )}
              </div>
              <div className="workspace-chart-block">
                <h4>{chartTitle}</h4>
                {chartData?.length ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={chartData} margin={{ top: 12, right: 8, left: -15, bottom: 48 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(11, 26, 56, 0.08)" />
                      <XAxis dataKey="label" angle={-28} textAnchor="end" interval={0} tick={{ fontSize: 11 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{
                          borderRadius: 10,
                          border: '1px solid rgba(12,143,114,0.2)',
                          background: 'rgba(255,255,255,0.97)',
                          fontSize: 12,
                        }}
                      />
                      <Bar dataKey="count" fill="#00aeef" radius={[7, 7, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="workspace-muted">Bu sütun için çizilebilir veri yok.</p>
                )}
              </div>
            </>
          )}
        </div>
      </section>

      <section className="workspace-lower-grid">
        <div className="workspace-correlation glass-panel">
          <div className="workspace-panel-heading">
            <div>
              <span>İlişki analizi</span>
              <h3>En güçlü korelasyonlar</h3>
            </div>
            <Activity size={20} color="#00aeef" />
          </div>
          {profile.correlations.length > 0 ? (
            <div className="workspace-correlation-list">
              {profile.correlations.slice(0, 8).map((item) => (
                <div key={`${item.left}-${item.right}`}>
                  <span>{item.left} <ArrowRight size={13} /> {item.right}</span>
                  <strong className={item.value < 0 ? 'negative' : ''}>{item.value}</strong>
                  <i style={{ '--strength': `${Math.abs(item.value) * 100}%` }} />
                </div>
              ))}
            </div>
          ) : (
            <p className="workspace-muted">Korelasyon için en az iki sayısal sütun gerekir.</p>
          )}
        </div>
        <PreviewTable title="Ham veri ön izlemesi" rows={profile.preview} />
      </section>
    </div>
  );
}
