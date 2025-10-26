/**
 * Login/Logout button component
 */

import { useMsal, useIsAuthenticated } from '@azure/msal-react';
import { loginRequest, isAuthEnabled } from '../authConfig';
import { getCurrentUser } from '../services/authService';
import './LoginButton.css';

export function LoginButton() {
  const { instance } = useMsal();
  const isAuthenticated = useIsAuthenticated();
  const user = getCurrentUser();

  if (!isAuthEnabled()) {
    // Development mode - show dev user info
    return (
      <div className="auth-info">
        <span className="dev-badge">DEV MODE</span>
        <span className="user-name">{user?.name || 'Development User'}</span>
      </div>
    );
  }

  const handleLogin = async () => {
    try {
      await instance.loginPopup(loginRequest);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await instance.logoutPopup({
        mainWindowRedirectUri: '/',
      });
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (!isAuthenticated) {
    return (
      <button className="login-button" onClick={handleLogin}>
        Sign In
      </button>
    );
  }

  return (
    <div className="auth-info">
      <span className="user-name">{user?.name || user?.username}</span>
      <button className="logout-button" onClick={handleLogout}>
        Sign Out
      </button>
    </div>
  );
}
