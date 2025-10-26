/**
 * Authentication Guard Component
 * Ensures user is authenticated before showing protected content
 */

import { useEffect, useState } from 'react';
import { useIsAuthenticated, useMsal } from '@azure/msal-react';
import { isAuthEnabled } from '../authConfig';
import { Login } from '../pages/Login';

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const isAuthenticated = useIsAuthenticated();
  const { inProgress } = useMsal();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    // If auth is disabled, skip initialization
    if (!isAuthEnabled()) {
      setIsInitializing(false);
      return;
    }

    // Wait for MSAL to finish initializing
    if (inProgress === 'none') {
      setIsInitializing(false);
    }
  }, [inProgress]);

  // If auth is disabled, always show children (development mode)
  if (!isAuthEnabled()) {
    return <>{children}</>;
  }

  // Show loading state while MSAL initializes
  if (isInitializing || inProgress !== 'none') {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        Loading...
      </div>
    );
  }

  // If not authenticated, show login page
  if (!isAuthenticated) {
    return <Login />;
  }

  // User is authenticated, show protected content
  return <>{children}</>;
}
