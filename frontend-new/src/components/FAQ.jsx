import React, { useState } from 'react';
import { HelpCircle, ChevronDown, MessageCircle, Send, CheckCircle2 } from 'lucide-react';
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
    answer: 'Hayır. Yüklenen ham dosya her zaman orijinal haliyle korunur. Sistem, seçilen işlemleri uygular ve size ayrı bir temizlenmiş CSV çıktısı (ve isteğe bağlı bir kalite raporu) verir.',
  },
  {
    question: 'Yapay zeka bu projede nerede kullanılıyor?',
    answer: 'Proje, eksik değer tahmininde ve aykırı değerlerin tespitinde makine öğrenmesi yöntemlerinden (örneğin KNN) yararlanır. Ayrıca entegre Gemini asistanımız temizleme sürecinde size rehberlik eder.',
  },
];

const FAQ = () => {
  // İlk soruyu varsayılan olarak açık tutalım
  const [openIndex, setOpenIndex] = useState(0);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    question: '',
  });
  const [isSending, setIsSending] = useState(false);
  const [isSent, setIsSent] = useState(false);

  const handleToggle = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  const handleSend = (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.email.trim() || !formData.question.trim()) return;
    
    setIsSending(true);
    // Gerçek bir API olmadığı için animasyonlu bir bekleme simülasyonu yapıyoruz
    setTimeout(() => {
      setIsSending(false);
      setIsSent(true);
      setFormData({ name: '', email: '', question: '' });
      
      // 5 saniye sonra formu eski haline getir
      setTimeout(() => setIsSent(false), 5000);
    }, 800);
  };

  return (
    <section className="faq-section" aria-labelledby="faq-heading">
      <div className="faq-container">
        
        {/* Sol Taraf - Başlık ve Soru Sorma Kutusu */}
        <div className="faq-header-side">
          <span className="faq-overline"><HelpCircle size={16} /> Sıkça Sorulan Sorular</span>
          <h3 id="faq-heading">Aklınızdaki soruları yanıtlıyoruz.</h3>
          <p>
            Veri temizleme süreçleri, algoritmaların nasıl karar verdiği ve verilerinizin güvenliği hakkında merak ettiklerinizi burada bulabilirsiniz.
          </p>
          
          <div className="faq-ask-box glass-panel">
            <div className="faq-ask-header">
              <MessageCircle size={20} className="faq-ask-icon" />
              <div>
                <strong>Cevabını bulamadınız mı?</strong>
                <span>Bize hemen sorun, uzmanlarımız yanıtlasın.</span>
              </div>
            </div>

            {isSent ? (
               <div className="faq-ask-success">
                 <CheckCircle2 size={24} />
                 <div>
                   <strong>Mesajınız ulaştı!</strong>
                   <span>Size en kısa sürede dönüş yapacağız.</span>
                 </div>
               </div>
            ) : (
              <form onSubmit={handleSend} className="faq-ask-form">
                <div className="faq-ask-inputs">
                  <input 
                    type="text" 
                    placeholder="Adınız Soyadınız" 
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required 
                  />
                  <input 
                    type="email" 
                    placeholder="E-posta Adresiniz" 
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required 
                  />
                </div>
                <textarea 
                  placeholder="Merak ettiğiniz konuyu buraya yazın..."
                  value={formData.question}
                  onChange={(e) => setFormData({...formData, question: e.target.value})}
                  rows={3}
                  required
                />
                <button 
                  type="submit" 
                  className="btn-primary" 
                  disabled={!formData.name.trim() || !formData.email.trim() || !formData.question.trim() || isSending}
                >
                  {isSending ? 'Gönderiliyor...' : (
                    <><Send size={15} /> Gönder</>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Sağ Taraf - Accordion SSS */}
        <div className="faq-accordion-side">
          {QUESTIONS.map((item, index) => {
            const isOpen = openIndex === index;
            return (
              <div 
                className={`faq-accordion-item glass-panel ${isOpen ? 'open' : ''}`} 
                key={index}
              >
                <button 
                  type="button" 
                  className="faq-accordion-header"
                  onClick={() => handleToggle(index)}
                  aria-expanded={isOpen}
                >
                  <span className="faq-question-text">{item.question}</span>
                  <span className="faq-toggle-icon">
                    <ChevronDown size={18} />
                  </span>
                </button>
                {/* CSS Grid numarasıyla height animasyonu */}
                <div className="faq-accordion-body">
                  <div className="faq-answer-content">
                    <p>{item.answer}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
};

export default FAQ;
