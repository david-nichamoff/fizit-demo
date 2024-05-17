// Function to format amount as currency
export const formatCurrency = (amount) => {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    });
    return formatter.format(amount);
};

// Function to format a date (MM/DD/YYYY) without converting to local timezone
export const formatDate = (isoDateTime, timeZone) => {
    if (!isoDateTime || isoDateTime === '1970-01-01') {
      return ''; // Return blank if the date is undefined, null, or '1970-01-01'
    }
  
    const date = new Date(isoDateTime);
    const formattedDate = date.toLocaleDateString('en-US', {
      timeZone,
      month: '2-digit',
      day: '2-digit',
      year: 'numeric'
    });
  
    return formattedDate;
}
  
// Function to format a date and time (MM/DD/YYYY HH:MM:SS) with conversion to local timezone
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