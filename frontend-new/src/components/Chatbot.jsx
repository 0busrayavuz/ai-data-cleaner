import { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot } from 'lucide-react';
import './Chatbot.css';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, text: "Merhaba! Veri temizliği veya platform özellikleri hakkında size nasıl yardımcı olabilirim?", sender: 'bot' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const toggleChat = () => setIsOpen(!isOpen);

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Kullanıcı mesajı ekle
    const newMsg = { id: Date.now(), text: inputValue.trim(), sender: 'user' };
    setMessages(prev => [...prev, newMsg]);
    setInputValue('');

    // Basit bir bot cevabı simüle edelim
    setTimeout(() => {
      let botReply = "Anlıyorum. Size en iyi şekilde yardımcı olabilmek için sorunuzu inceliyorum.";
      
      const lowerInput = newMsg.text.toLowerCase();
      if (lowerInput.includes('eksik') || lowerInput.includes('missing')) {
        botReply = "Eksik verileri çözmek için önerilen algoritmaları (Mean, Median, KNNImputer vb.) tablolardaki butonlarla otomatik uygulayabilirsiniz.";
      } else if (lowerInput.includes('aykırı') || lowerInput.includes('outlier')) {
        botReply = "Aykırı değer tespiti Isolation Forest, LOF ve DBSCAN destekli çalışır. Gerekirse sınırlandırabilir (Cap) veya silebilirsiniz.";
      } else if (lowerInput.includes('indir') || lowerInput.includes('download')) {
        botReply = "İşlemler tamamlandıktan sonra sonuç ekranında 'Temizlenmiş Veriyi İndir' butonu belirecektir.";
      }

      setMessages(prev => [...prev, { id: Date.now() + 1, text: botReply, sender: 'bot' }]);
    }, 1000);
  };

  return (
    <div className={`chatbot-wrapper ${isOpen ? 'open' : ''}`}>
      {isOpen && (
        <div className="chatbot-window glass-panel">
          <div className="chatbot-header">
            <div className="chatbot-title">
              <Bot size={20} className="chatbot-icon" />
              <span>Veri Asistanı</span>
            </div>
            <button className="chatbot-close" onClick={toggleChat} aria-label="Kapat">
              <X size={20} />
            </button>
          </div>
          
          <div className="chatbot-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`chat-message ${msg.sender}`}>
                <div className="message-bubble">{msg.text}</div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form className="chatbot-input-area" onSubmit={handleSend}>
            <input 
              type="text" 
              placeholder="Bir soru sorun..." 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="chatbot-input"
            />
            <button type="submit" className="chatbot-send" disabled={!inputValue.trim()}>
              <Send size={18} />
            </button>
          </form>
        </div>
      )}

      {!isOpen && (
        <button className="chatbot-toggle-btn bounce-in" onClick={toggleChat}>
          <MessageSquare size={24} />
        </button>
      )}
    </div>
  );
};

export default Chatbot;
