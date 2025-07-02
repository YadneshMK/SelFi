export function debugAuth() {
  const token = localStorage.getItem('access_token');
  const authCookie = document.cookie
    .split('; ')
    .find(row => row.startsWith('auth-token='))
    ?.split('=')[1];
  
  console.log('=== Authentication Debug Info ===');
  console.log('LocalStorage token:', token ? `${token.substring(0, 20)}...` : 'No token');
  console.log('Auth cookie:', authCookie ? `${authCookie.substring(0, 20)}...` : 'No cookie');
  console.log('Token match:', token === authCookie ? 'Yes' : 'No');
  
  if (token) {
    try {
      // Decode JWT to check expiration (basic decoding, not verification)
      const parts = token.split('.');
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        const exp = payload.exp;
        const now = Math.floor(Date.now() / 1000);
        console.log('Token expires at:', new Date(exp * 1000).toLocaleString());
        console.log('Token expired:', exp < now ? 'Yes' : 'No');
        console.log('Time until expiry:', exp > now ? `${Math.floor((exp - now) / 60)} minutes` : 'Already expired');
      }
    } catch (e) {
      console.error('Failed to decode token:', e);
    }
  }
  
  console.log('================================');
}

// Add to window for easy access in browser console
if (typeof window !== 'undefined') {
  (window as any).debugAuth = debugAuth;
}