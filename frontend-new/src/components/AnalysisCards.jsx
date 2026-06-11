import { createElement } from 'react';
import {
  Binary,
  BrainCircuit,
  Braces,
  ChartNoAxesCombined,
  CircleDotDashed,
  FileCheck2,
} from 'lucide-react';
import './AnalysisCards.css';

const METHODS = [
  {
    icon: BrainCircuit,
    eyebrow: 'Eksik veri',
    title: 'Akıllı tamamlama',
    description: 'MICE ve KNN ile diğer sütunlardaki örüntülerden yararlanarak tahmin üretir.',
    methods: ['MICE', 'KNN Imputer', 'Ortalama / Medyan'],
    tone: 'emerald',
  },
  {
    icon: CircleDotDashed,
    eyebrow: 'Anomali',
    title: 'Çok yöntemli tespit',
    description: 'Tek değişkenli ve bağlamsal anomalileri farklı algoritmalarla karşılaştırır.',
    methods: ['Isolation Forest', 'DBSCAN', 'IQR'],
    tone: 'cyan',
  },
  {
    icon: Braces,
    eyebrow: 'Format',
    title: 'Tutarlılık onarımı',
    description: 'Metin, tarih, sayısal tip ve benzer kategori problemlerini standartlaştırır.',
    methods: ['Tip dönüşümü', 'Fuzzy eşleme', 'Metin normalizasyonu'],
    tone: 'amber',
  },
  {
    icon: Binary,
    eyebrow: 'Özellik',
    title: 'Model öncesi hazırlık',
    description: 'Kategorik ve sayısal değişkenleri makine öğrenmesi için hazır hale getirir.',
    methods: ['One-hot', 'Label encoding', 'Ölçekleme'],
    tone: 'violet',
  },
];

const AnalysisCards = () => {
  return (
    <section className="analysis-section" aria-labelledby="methods-heading">
      <div className="analysis-intro">
        <div>
          <span className="analysis-overline"><ChartNoAxesCombined size={15} /> Yöntem kütüphanesi</span>
          <h3 id="methods-heading">Tek algoritmaya bağlı kalmayan analiz.</h3>
        </div>
        <p>
          Veri tipine ve probleme göre farklı istatistiksel ve makine öğrenmesi
          yöntemleri sunulur. Son kararı kullanıcı verir.
        </p>
      </div>

      <div className="method-grid">
        {METHODS.map(({ icon, eyebrow, title, description, methods, tone }) => (
          <article className={`method-card method-card--${tone}`} key={title}>
            <div className="method-card-top">
              <span className="method-icon">
                {createElement(icon, { size: 22, 'aria-hidden': true })}
              </span>
              <span className="method-eyebrow">{eyebrow}</span>
            </div>
            <h4>{title}</h4>
            <p>{description}</p>
            <div className="method-tags">
              {methods.map((method) => <span key={method}>{method}</span>)}
            </div>
          </article>
        ))}
      </div>

      <div className="analysis-note">
        <FileCheck2 size={20} aria-hidden />
        <div>
          <strong>Sonuç yalnızca temiz veri değil.</strong>
          <span>Uygulanan yöntemler, kalite değişimi ve işlem geçmişi raporlanır.</span>
        </div>
      </div>
    </section>
  );
};

export default AnalysisCards;
