export const formatPrice = (value) => {
  return new Intl.NumberFormat('pt-BR', { 
    style: 'currency', 
    currency: 'BRL' 
  }).format(value || 0);
};

export const formatDate = (isoString) => {
  if (!isoString) return '';
  return new Intl.DateTimeFormat('pt-BR', { 
    day: '2-digit', 
    month: 'short', 
    year: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  }).format(new Date(isoString));
};