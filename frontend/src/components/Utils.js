export const formatCurrency = (amount) => {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  return formatter.format(amount);
};

export const formatDateTime = (isoDateTime) => {
  if (!isoDateTime || isoDateTime === '1970-01-01T00:00:00') {
    return ''; // Return blank if the datetime is undefined, null, or '1970-01-01T00:00:00'
  }

  const date = new Date(isoDateTime);
  const formattedDateTime = date.toLocaleString('en-US', {
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    month: '2-digit',
    day: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  return formattedDateTime;
}

export const formatDate = (dateString) => {
if (!dateString || dateString === 0 || new Date(dateString).getTime() === 0 || new Date(dateString).getFullYear() === 1970) {
  return '';
}
const options = { year: 'numeric', month: '2-digit', day: '2-digit' };
return new Date(dateString).toLocaleDateString(undefined, options);
};

export const formatPercentage = (value) => {
return (value * 100) + '%';
};

export const capitalizeFirstLetter = (string) => {
  return string.charAt(0).toUpperCase() + string.slice(1);
};