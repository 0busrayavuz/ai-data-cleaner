import { useEffect, useRef } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import './ConfirmModal.css';

/**
 * Genel amaçlı onay modalı.
 *
 * Props:
 *   isOpen      - Modal açık mı?
 *   title       - Modal başlığı
 *   message     - Ana açıklama metni
 *   warning     - (opsiyonel) Kırmızı uyarı metni
 *   confirmText - Onayla butonu metni (varsayılan: "Onayla")
 *   cancelText  - İptal butonu metni (varsayılan: "İptal")
 *   onConfirm   - Onay tıklandığında çağrılan callback
 *   onCancel    - İptal/kapatma tıklandığında çağrılan callback
 *   danger      - true ise onay butonu kırmızı/tehlikeli stil alır
 */
export default function ConfirmModal({
  isOpen,
  title = 'Emin misiniz?',
  message,
  warning,
  confirmText = 'Onayla',
  cancelText = 'İptal',
  onConfirm,
  onCancel,
  danger = false,
}) {
  const dialogRef = useRef(null);

  // Escape tuşuyla kapat
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e) => {
      if (e.key === 'Escape') onCancel?.();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onCancel]);

  // Dışarıya tıklayınca kapat
  const handleOverlayClick = (e) => {
    if (dialogRef.current && !dialogRef.current.contains(e.target)) {
      onCancel?.();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="confirm-overlay"
      role="presentation"
      onMouseDown={handleOverlayClick}
    >
      <div
        ref={dialogRef}
        className="confirm-modal glass-panel"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby={message ? 'confirm-message' : undefined}
      >
        {/* Kapat butonu */}
        <button
          type="button"
          className="confirm-close-btn"
          onClick={onCancel}
          aria-label="Kapat"
        >
          <X size={20} />
        </button>

        {/* İkon */}
        <div className={`confirm-icon-wrap ${danger ? 'danger' : 'neutral'}`}>
          <AlertTriangle size={30} aria-hidden />
        </div>

        {/* Başlık */}
        <h2 id="confirm-title" className="confirm-title">
          {title}
        </h2>

        {/* Açıklama */}
        {message && (
          <p id="confirm-message" className="confirm-message">
            {message}
          </p>
        )}

        {/* Kırmızı uyarı */}
        {warning && (
          <div className="confirm-warning" role="alert">
            <AlertTriangle size={16} aria-hidden />
            <span>{warning}</span>
          </div>
        )}

        {/* Butonlar */}
        <div className="confirm-actions">
          <button
            type="button"
            className="confirm-cancel-btn"
            onClick={onCancel}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className={`confirm-ok-btn ${danger ? 'danger' : ''}`}
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
