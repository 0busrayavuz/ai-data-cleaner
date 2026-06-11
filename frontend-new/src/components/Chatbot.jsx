import { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot } from 'lucide-react';
import './Chatbot.css';
import { getStoredToken, sendAssistantChat } from '../services/api';

const WELCOME = {
  id: 'welcome',
  text: 'Merhaba! Veri temizliği veya platform özellikleri hakkında size nasıl yardımcı olabilirim?',
  sender: 'bot',
  skipHistory: true,
};

function toGeminiMessages(list) {
  return list
    .filter((m) => !m.skipHistory)
    .map((m) => ({
      role: m.sender === 'user' ? 'user' : 'model',
      text: m.text,
    }));
}

const Chatbot = ({ onNeedAuth, isLoggedIn = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME]);
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen, sending]);

  const toggleChat = () => setIsOpen(!isOpen);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || sending) return;

    if (!getStoredToken()) {
      setChatError('');
      onNeedAuth?.();
      return;
    }

    const text = inputValue.trim();
    const userMsg = { id: Date.now(), text, sender: 'user' };
    const nextList = [...messages, userMsg];

    setInputValue('');
    setChatError('');
    setMessages(nextList);
    setSending(true);

    try {
      const payload = toGeminiMessages(nextList);
      const { reply } = await sendAssistantChat(payload);
      setMessages((prev) => [...prev, { id: Date.now() + 1, text: reply, sender: 'bot' }]);
    } catch (err) {
      setChatError(err?.message || 'Asistan yanıt veremedi.');
    } finally {
      setSending(false);
    }
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
            <button type="button" className="chatbot-close" onClick={toggleChat} aria-label="Kapat">
              <X size={20} />
            </button>
          </div>

          {!isLoggedIn && (
            <div className="chatbot-auth-hint" role="status">
              Asistanı kullanmak için giriş yapın.
              <button type="button" className="chatbot-auth-btn" onClick={() => onNeedAuth?.()}>
                Giriş / kayıt
              </button>
            </div>
          )}

          {chatError ? <div className="chatbot-error">{chatError}</div> : null}

          <div className="chatbot-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`chat-message ${msg.sender}`}>
                <div className="message-bubble">{msg.text}</div>
              </div>
            ))}
            {sending ? (
              <div className="chat-message bot" aria-live="polite">
                <div className="message-bubble chatbot-typing">Yazıyor…</div>
              </div>
            ) : null}
            <div ref={messagesEndRef} />
          </div>

          <form className="chatbot-input-area" onSubmit={handleSend}>
            <input
              type="text"
              placeholder={isLoggedIn ? 'Bir soru sorun…' : 'Önce giriş yapın…'}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="chatbot-input"
              disabled={!isLoggedIn || sending}
              autoComplete="off"
            />
            <button
              type="submit"
              className="chatbot-send"
              disabled={!isLoggedIn || !inputValue.trim() || sending}
              aria-label="Gönder"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      )}

      {!isOpen && (
        <button type="button" className="chatbot-toggle-btn bounce-in" onClick={toggleChat} aria-label="Yardımcı asistanı aç">
          <MessageSquare size={26} strokeWidth={2.25} className="chatbot-fab-icon" />
        </button>
      )}
    </div>
  );
};

export default Chatbot;
