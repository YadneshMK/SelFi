'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LogoutPage() {
  const router = useRouter();

  useEffect(() => {
    // Clear all authentication data
    console.log('Logout page - clearing auth data');
    
    // Clear localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.clear();
    
    // Clear all cookies
    document.cookie.split(";").forEach((c) => {
      document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
    
    // Clear sessionStorage
    sessionStorage.clear();
    
    console.log('Auth data cleared, redirecting to login...');
    
    // Redirect to login page
    setTimeout(() => {
      window.location.href = '/login';
    }, 100);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Logging out...</h2>
        <p className="text-gray-600">You will be redirected to the login page.</p>
        <div className="mt-4">
          <a 
            href="/login" 
            className="text-indigo-600 hover:text-indigo-500 underline"
          >
            Click here if not redirected
          </a>
        </div>
      </div>
    </div>
  );
}