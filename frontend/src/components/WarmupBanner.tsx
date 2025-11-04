import { useEffect, useState } from 'react';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { warmupBackend, type WarmupStatus } from '../services/api';
import './WarmupBanner.css';

export const WarmupBanner = () => {
  const [status, setStatus] = useState<WarmupStatus | null>(null);
  const [isWarming, setIsWarming] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const performWarmup = async () => {
      try {
        console.log('Starting backend warmup...');
        const warmupStatus = await warmupBackend();
        setStatus(warmupStatus);

        if (warmupStatus.status === 'warm') {
          console.log('Backend is warm and ready!');
          // Hide banner after 2 seconds if warm
          setTimeout(() => {
            setIsWarming(false);
          }, 2000);
        } else {
          // Retry after 3 seconds if still warming
          setTimeout(performWarmup, 3000);
        }
      } catch (err: any) {
        console.error('Warmup failed:', err);
        setError(err.message || 'Failed to connect to backend');
        // Retry after 5 seconds on error
        setTimeout(performWarmup, 5000);
      }
    };

    performWarmup();
  }, []);

  // Don't show banner if warmed up
  if (!isWarming) {
    return null;
  }

  // Show error state
  if (error) {
    return (
      <div className="warmup-banner warmup-error">
        <AlertCircle size={20} />
        <div className="warmup-content">
          <strong>Connection Error</strong>
          <span>{error}</span>
          <span className="warmup-hint">Retrying automatically...</span>
        </div>
      </div>
    );
  }

  // Show warming state
  if (!status || status.status === 'warming') {
    return (
      <div className="warmup-banner warmup-warming">
        <Loader2 size={20} className="warmup-spinner" />
        <div className="warmup-content">
          <strong>Warming up backend...</strong>
          <span>{status?.message || 'Initializing database connections'}</span>
          <span className="warmup-hint">This may take up to 30 seconds after inactivity</span>
        </div>
      </div>
    );
  }

  // Show warm (success) state
  return (
    <div className="warmup-banner warmup-success">
      <CheckCircle size={20} />
      <div className="warmup-content">
        <strong>Backend ready!</strong>
        <span>All systems operational</span>
      </div>
    </div>
  );
};
