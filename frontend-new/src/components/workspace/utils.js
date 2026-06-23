export const numberFormat = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 });

export function formatValue(value) {
  if (value == null || value === '') return '—';
  if (typeof value === 'number') {
    if (Number.isNaN(value) || !Number.isFinite(value)) return '—';
    return numberFormat.format(value);
  }
  return String(value);
}
