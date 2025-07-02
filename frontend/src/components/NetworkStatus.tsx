'use client';

import { useNetworkStatus } from '@/lib/network-monitor';
import { WifiOff, AlertCircle } from 'lucide-react';
import { useEffect, useState } from 'react';

export function NetworkStatus() {
  const isOnline = useNetworkStatus();
  const [showOffline, setShowOffline] = useState(false);

  useEffect(() => {
    if (!isOnline) {
      setShowOffline(true);
    } else {
      // Delay hiding the notification for smooth transition
      const timer = setTimeout(() => setShowOffline(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [isOnline]);

  if (!showOffline) return null;

  return (
    <div className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isOnline ? 'bg-green-600' : 'bg-red-600'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-3 flex items-center justify-center space-x-2">
          {isOnline ? (
            <>
              <AlertCircle className="h-5 w-5 text-white" />
              <p className="text-white text-sm font-medium">
                Connection restored
              </p>
            </>
          ) : (
            <>
              <WifiOff className="h-5 w-5 text-white animate-pulse" />
              <p className="text-white text-sm font-medium">
                No internet connection. Some features may be unavailable.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}