import { AlertCircle, AlertTriangle, Cpu, FileCode2 } from 'lucide-react';

export const FORMAT_DEFAULTS = {
  numeric_as_string: 'to_numeric',
  date_as_string: 'to_datetime',
  whitespace: 'strip_whitespace',
  case_inconsistency: 'normalize_case',
  fuzzy_duplicates: 'semantic_merge',
};

export const CATEGORY_LABELS = {
  missing: 'Eksik veri',
  outlier: 'Aykırı değer',
  format: 'Format',
  feature: 'Özellik',
};

export const CATEGORY_ICONS = {
  missing: AlertCircle,
  outlier: AlertTriangle,
  format: FileCode2,
  feature: Cpu,
};
