export const getCurrencySymbol = (currency: string = 'USD'): string => {
  const c = (currency || 'USD').toUpperCase().trim();
  switch (c) {
    case 'INR':
      return '₹';
    case 'EUR':
      return '€';
    case 'GBP':
      return '£';
    case 'JPY':
    case 'CNY':
      return '¥';
    case 'CAD':
      return 'CA$';
    case 'AUD':
      return 'A$';
    case 'CHF':
      return 'CHF ';
    case 'BRL':
      return 'R$';
    case 'SGD':
      return 'S$';
    case 'AED':
      return 'AED ';
    case 'SAR':
      return 'SAR ';
    case 'USD':
    default:
      return '$';
  }
};

export const formatCurrency = (value?: number | null, currency: string = 'USD'): string => {
  if (value === undefined || value === null || isNaN(value)) return '—';
  
  const symbol = getCurrencySymbol(currency);
  
  if (Math.abs(value) >= 1_000_000) {
    return `${symbol}${(value / 1_000_000).toFixed(2)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `${symbol}${(value / 1_000).toFixed(1)}k`;
  }
  return `${symbol}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export const formatPercentage = (value?: number | null, withSign: boolean = true): string => {
  if (value === undefined || value === null || isNaN(value)) return '—';
  const prefix = withSign && value > 0 ? '+' : '';
  return `${prefix}${value.toFixed(1)}%`;
};

export const formatNumber = (value?: number | null): string => {
  if (value === undefined || value === null || isNaN(value)) return '—';
  if (Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `${(value / 1_000).toFixed(1)}k`;
  }
  return value.toLocaleString();
};

export const formatKPIValue = (value?: number | null, unit: string = 'currency', currency: string = 'USD'): string => {
  if (value === undefined || value === null) return 'No Data';
  if (unit === 'currency') return formatCurrency(value, currency);
  if (unit === 'percentage') return `${value.toFixed(1)}%`;
  if (unit === 'days') return `${value.toFixed(0)} days`;
  return formatNumber(value);
};

export const formatDate = (dateStr: string): string => {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr;
  }
};

export const formatRelativeTime = (dateInput?: string | Date | number | null): string => {
  if (!dateInput) return 'Just now';
  try {
    const d = new Date(dateInput);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - d.getTime()) / 1000);

    if (diffSec < 0 || isNaN(diffSec)) return 'Just now';
    if (diffSec < 60) return 'Just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin === 1) return '1 min ago';
    if (diffMin < 60) return `${diffMin} min ago`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return 'Recently';
  }
};
