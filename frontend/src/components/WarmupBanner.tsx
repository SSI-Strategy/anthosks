import { useEffect, useState } from 'react';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { warmupBackend, type WarmupStatus } from '../services/api';
import './WarmupBanner.css';

export const WarmupBanner = () => {
  const [status, setStatus] = useState<WarmupStatus | null>(null);
  const [isWarming, setIsWarming] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const performWarmup = async () => {
      if (!isMounted) return;

      try {
        console.log('Starting backend warmup...');
        const warmupStatus = await warmupBackend();

        if (!isMounted) return;

        setStatus(warmupStatus);
        setError(null);
        setRetryCount(0); // Reset retry count on success

        if (warmupStatus.status === 'warm') {
          console.log('Backend is warm and ready!');
          // Hide banner after 2 seconds if warm
          timeoutId = setTimeout(() => {
            if (isMounted) setIsWarming(false);
          }, 2000);
        } else {
          // Retry after 3 seconds if still warming
          timeoutId = setTimeout(() => {
            if (isMounted) performWarmup();
          }, 3000);
        }
      } catch (err) {
        if (!isMounted) return;

        const error = err as Error;
        console.error('Warmup failed:', error);
        setError(error.message || 'Failed to connect to backend');

        // Exponential backoff: 2s, 4s, 8s, 16s, max 30s
        const newRetryCount = retryCount + 1;
        setRetryCount(newRetryCount);
        const retryDelay = Math.min(1000 * Math.pow(2, newRetryCount), 30000);

        console.log(`Retrying in ${retryDelay / 1000}s (attempt ${newRetryCount})...`);
        timeoutId = setTimeout(() => {
          if (isMounted) performWarmup();
        }, retryDelay);
      }
    };

    performWarmup();

    // Cleanup function to prevent memory leaks
    return () => {
      isMounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [retryCount]);

  // Wrap render in try-catch for graceful degradation
  try {
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
  } catch (err) {
    console.error('WarmupBanner render error:', err);
    // Fail gracefully - don't crash the app
    return null;
  }
};
