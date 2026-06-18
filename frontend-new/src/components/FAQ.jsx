import { HelpCircle } from 'lucide-react';
import './FAQ.css';

const QUESTIONS = [
  {
    question: 'Sağlık skoru neyi gösterir?',
    answer: 'Sağlık skoru, veri setindeki eksik hücre, format problemi ve aykırı değerleri özetleyen 0-100 arası bir kalite göstergesidir. Eksik veri en ağır, format problemi orta, aykırı değer ise daha düşük ağırlıkla değerlendirilir.',
  },
  {
    question: 'Aykırı değer her zaman hata mıdır?',
    answer: 'Hayır. Aykırı değer bazen veri giriş hatasıdır, bazen de gerçekten önemli bir gözlemdir. Bu yüzden sistem aykırı değerleri otomatik silmez; bırakma, sınırlama veya düzeltme seçeneklerini kullanıcıya sunar.',
  },
  {
    question: 'Eksik değer doldurma gerçek veri üretir mi?',
    answer: 'Eksik değer doldurma işlemi gerçek gözlem değil, istatistiksel tahmin üretir. Bu nedenle hangi yöntemin kullanıldığı raporda gösterilir ve kullanıcı onayı olmadan uygulanmaz.',
  },
  {
    question: 'Veri seti boyutu neden önemli?',
    answer: 'Analiz işlemleri veriyi bellekte işler. MICE, KNN ve aykırı değer algoritmaları veri büyüdükçe daha fazla zaman ve bellek kullanır. Bu proje güvenli demo ve makul işlem süresi için 20 MB yükleme sınırıyla çalışır.',
  },
  {
    question: 'Temizlik işlemi ham dosyayı değiştirir mi?',
    answer: 'Hayır. Yüklenen ham dosya korunur. Seçilen işlemler ayrı bir temizlenmiş CSV çıktısı üretir; yapılan işlemler de rapor ve denetim kaydı olarak saklanır.',
  },
  {
    question: 'Yapay zeka bu projede nerede kullanılıyor?',
    answer: 'Proje, eksik değer ve aykırı değer analizlerinde makine öğrenmesi yöntemlerinden yararlanır. Gemini destekli asistan ise kullanıcıya veri temizleme sürecinde yardımcı olan ek bir katmandır.',
  },
];

const FAQ = () => (
  <section className="faq-section" aria-labelledby="faq-heading">
    <div className="faq-header">
      <span className="faq-overline"><HelpCircle size={15} /> Soru-cevap</span>
      <h3 id="faq-heading">Veri temizleme kavramları daha anlaşılır olsun.</h3>
      <p>
        Sağlık skoru, aykırı değer ve eksik veri tamamlama gibi kavramlar karar verirken önemlidir.
        Bu bölüm, sistemin neyi neden önerdiğini sade bir dille açıklar.
      </p>
    </div>

    <div className="faq-grid">
      {QUESTIONS.map((item) => (
        <article className="faq-card glass-panel" key={item.question}>
          <h4>{item.question}</h4>
          <p>{item.answer}</p>
        </article>
      ))}
    </div>
  </section>
);

export default FAQ;
