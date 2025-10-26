import { useState } from 'react';
import './App.css';
import Upload from './components/Upload';
import Review from './components/Review';
import Reports from './components/Reports';
import Analytics from './components/Analytics';
import { LoginButton } from './components/LoginButton';

type Tab = 'upload' | 'review' | 'reports' | 'analytics';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('upload');

  return (
    <div className="app">
      <header className="app-header">
        <h1>📋 MOV Report Extraction & Review</h1>
        <LoginButton />
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'upload' ? 'active' : ''}
          onClick={() => setActiveTab('upload')}
        >
          Upload
        </button>
        <button
          className={activeTab === 'review' ? 'active' : ''}
          onClick={() => setActiveTab('review')}
        >
          Review
        </button>
        <button
          className={activeTab === 'reports' ? 'active' : ''}
          onClick={() => setActiveTab('reports')}
        >
          Reports
        </button>
        <button
          className={activeTab === 'analytics' ? 'active' : ''}
          onClick={() => setActiveTab('analytics')}
        >
          Analytics
        </button>
      </nav>

      <main className="content">
        {activeTab === 'upload' && <Upload />}
        {activeTab === 'review' && <Review />}
        {activeTab === 'reports' && <Reports />}
        {activeTab === 'analytics' && <Analytics />}
      </main>
    </div>
  );
}

export default App;
