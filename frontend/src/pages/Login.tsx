/**
 * Login page component
 * Displayed when user is not authenticated
 */

import { useMsal } from '@azure/msal-react';
import { ClipboardList } from 'lucide-react';
import { loginRequest } from '../authConfig';
import './Login.css';

export function Login() {
  const { instance } = useMsal();

  const handleLogin = async () => {
    try {
      await instance.loginPopup(loginRequest);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>
            <ClipboardList size={36} className="icon-inline" style={{ marginRight: '12px' }} />
            MOV Report Extraction & Review
          </h1>
          <p className="login-subtitle">Compliance Document Analysis System</p>
        </div>

        <div className="login-content">
          <p className="login-description">
            Sign in with your organizational account to access the application.
          </p>

          <button
            className="login-button"
            onClick={handleLogin}
          >
            <svg
              width="21"
              height="21"
              viewBox="0 0 21 21"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              style={{ marginRight: '12px' }}
            >
              <path d="M0 0h9.996v9.996H0V0zm11.004 0H21v9.996h-9.996V0zM0 11.004h9.996V21H0v-9.996zm11.004 0H21V21h-9.996v-9.996z" fill="#F25022"/>
              <path d="M11.004 0H21v9.996h-9.996V0z" fill="#7FBA00"/>
              <path d="M0 11.004h9.996V21H0v-9.996z" fill="#00A4EF"/>
              <path d="M11.004 11.004H21V21h-9.996v-9.996z" fill="#FFB900"/>
            </svg>
            Sign in with Microsoft
          </button>

          <div className="login-footer">
            <p className="login-note">
              This application requires Azure AD authentication.
              <br />
              Please contact your administrator if you need access.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
