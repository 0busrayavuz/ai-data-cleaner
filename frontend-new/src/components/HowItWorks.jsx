import { createElement } from 'react';
import { CheckCircle2, FileSearch, ListChecks, PlayCircle, UploadCloud } from 'lucide-react';
import './HowItWorks.css';

const STEPS = [
  {
    number: '01',
    icon: UploadCloud,
    title: 'Verinizi yükleyin',
    text: 'CSV, XLSX veya TXT dosyanızı proje altında güvenli biçimde yükleyin.',
  },
  {
    number: '02',
    icon: FileSearch,
    title: 'Kalite profilini çıkarın',
    text: 'Eksik değer, aykırı gözlem, tip ve format problemlerini tek görünümde inceleyin.',
  },
  {
    number: '03',
    icon: ListChecks,
    title: 'Yöntemi siz seçin',
    text: 'Sistem önerilerini karşılaştırın; uygulanacak işlemleri veri setinize göre onaylayın.',
  },
  {
    number: '04',
    icon: PlayCircle,
    title: 'Uygulayın ve raporlayın',
    text: 'Temizlenmiş çıktıyı indirin; değişiklik geçmişini PDF, HTML ve denetim kaydıyla saklayın.',
  },
];

const HowItWorks = () => {
  return (
    <section className="how-it-works-section" aria-labelledby="workflow-heading">
      <div className="section-kicker"><CheckCircle2 size={15} /> Kontrollü otomasyon</div>
      <div className="hiw-header">
        <div>
          <h3 id="workflow-heading" className="section-heading">
            Kara kutu değil, <span>izlenebilir iş akışı.</span>
          </h3>
        </div>
        <p className="section-subtitle">
          Her öneri kullanıcı onayından geçer. Böylece sistem yalnızca otomasyon sağlamaz;
          hangi işlemin neden uygulandığını da görünür kılar.
        </p>
      </div>

      <div className="hiw-steps">
        {STEPS.map(({ number, icon, title, text }) => (
          <article className="hiw-step" key={number}>
            <div className="hiw-step-head">
              <span className="step-number">{number}</span>
              <span className="step-icon">
                {createElement(icon, { size: 21, 'aria-hidden': true })}
              </span>
            </div>
            <h4>{title}</h4>
            <p>{text}</p>
          </article>
        ))}
      </div>
    </section>
  );
};

export default HowItWorks;
