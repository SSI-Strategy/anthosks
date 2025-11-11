import { useState, useEffect } from 'react';
import {
  getKPIs,
  getQuestionStatistics,
  getSiteLeaderboard,
  getGeographicSummary,
  getProtocols,
  type KPIData,
  type QuestionStatistic,
  type SiteLeaderboardEntry,
  type GeographicSummary
} from '../services/api';
import './Analytics.css';

type ViewType = 'executive' | 'compliance' | 'sites' | 'geographic';

function Analytics() {
  const [activeView, setActiveView] = useState<ViewType>('executive');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [questions, setQuestions] = useState<QuestionStatistic[]>([]);
  const [sites, setSites] = useState<SiteLeaderboardEntry[]>([]);
  const [countries, setCountries] = useState<GeographicSummary[]>([]);
  const [protocols, setProtocols] = useState<string[]>([]);

  // Filters
  const [dateRange, setDateRange] = useState<'all' | '30d' | '90d' | 'ytd'>('all');
  const [selectedCountry, setSelectedCountry] = useState<string>('');
  const [selectedProtocol, setSelectedProtocol] = useState<string>('');

  useEffect(() => {
    loadProtocols();
  }, []);

  useEffect(() => {
    loadAnalytics();
  }, [dateRange, selectedCountry, selectedProtocol]);

  const loadProtocols = async () => {
    try {
      const protocolsList = await getProtocols();
      setProtocols(protocolsList);
    } catch (err) {
      console.error('Failed to load protocols:', err);
    }
  };

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      // Calculate date range
      let date_from: string | undefined;
      let date_to: string | undefined;
      const now = new Date();

      if (dateRange === '30d') {
        date_from = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        date_to = now.toISOString().split('T')[0];
      } else if (dateRange === '90d') {
        date_from = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        date_to = now.toISOString().split('T')[0];
      } else if (dateRange === 'ytd') {
        date_from = `${now.getFullYear()}-01-01`;
        date_to = now.toISOString().split('T')[0];
      }

      const filters = {
        date_from,
        date_to,
        country: selectedCountry || undefined,
        protocol: selectedProtocol || undefined,
      };

      // Load all analytics data in parallel
      const [kpisData, questionsData, sitesData, countriesData] = await Promise.all([
        getKPIs(filters),
        getQuestionStatistics(filters),
        getSiteLeaderboard({ ...filters, limit: 50 }),
        getGeographicSummary(filters),
      ]);

      setKpis(kpisData);
      setQuestions(questionsData);
      setSites(sitesData);
      setCountries(countriesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const renderExecutiveDashboard = () => {
    if (!kpis) return null;

    return (
      <div className="executive-dashboard">
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-value">{kpis.total_sites}</div>
            <div className="kpi-label">Total Sites</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{kpis.total_reports}</div>
            <div className="kpi-label">Total Reports</div>
          </div>
          <div className="kpi-card highlight">
            <div className="kpi-value">{kpis.compliance_rate.toFixed(1)}%</div>
            <div className="kpi-label">Compliance Rate</div>
          </div>
          <div className="kpi-card alert">
            <div className="kpi-value">{kpis.non_compliance_rate.toFixed(1)}%</div>
            <div className="kpi-label">Non-Compliance Rate</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{kpis.completeness_rate.toFixed(1)}%</div>
            <div className="kpi-label">Data Completeness</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{kpis.avg_site_quality_score.toFixed(1)}/5</div>
            <div className="kpi-label">Avg Quality Score</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{kpis.avg_enrollment_rate.toFixed(1)}%</div>
            <div className="kpi-label">Enrollment Rate</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{kpis.avg_completion_rate.toFixed(1)}%</div>
            <div className="kpi-label">Completion Rate</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{kpis.total_action_items}</div>
            <div className="kpi-label">Total Action Items</div>
          </div>
          <div className="kpi-card warning">
            <div className="kpi-value">{kpis.high_risk_sites}</div>
            <div className="kpi-label">High Risk Sites</div>
          </div>
        </div>

        <div className="charts-section">
          <div className="chart-card">
            <h3>Answer Distribution</h3>
            <div className="answer-distribution">
              <div className="answer-bar">
                <div className="bar-label">Yes</div>
                <div className="bar-container">
                  <div
                    className="bar yes-bar"
                    style={{ width: `${(kpis.answer_distribution.yes / (kpis.answer_distribution.yes + kpis.answer_distribution.no + kpis.answer_distribution.na + kpis.answer_distribution.nr)) * 100}%` }}
                  >
                    {kpis.answer_distribution.yes}
                  </div>
                </div>
              </div>
              <div className="answer-bar">
                <div className="bar-label">No</div>
                <div className="bar-container">
                  <div
                    className="bar no-bar"
                    style={{ width: `${(kpis.answer_distribution.no / (kpis.answer_distribution.yes + kpis.answer_distribution.no + kpis.answer_distribution.na + kpis.answer_distribution.nr)) * 100}%` }}
                  >
                    {kpis.answer_distribution.no}
                  </div>
                </div>
              </div>
              <div className="answer-bar">
                <div className="bar-label">N/A</div>
                <div className="bar-container">
                  <div
                    className="bar na-bar"
                    style={{ width: `${(kpis.answer_distribution.na / (kpis.answer_distribution.yes + kpis.answer_distribution.no + kpis.answer_distribution.na + kpis.answer_distribution.nr)) * 100}%` }}
                  >
                    {kpis.answer_distribution.na}
                  </div>
                </div>
              </div>
              <div className="answer-bar">
                <div className="bar-label">NR</div>
                <div className="bar-container">
                  <div
                    className="bar nr-bar"
                    style={{ width: `${(kpis.answer_distribution.nr / (kpis.answer_distribution.yes + kpis.answer_distribution.no + kpis.answer_distribution.na + kpis.answer_distribution.nr)) * 100}%` }}
                  >
                    {kpis.answer_distribution.nr}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderComplianceView = () => {
    // Sort questions by compliance rate (lowest first - most problematic)
    const sortedQuestions = [...questions].sort((a, b) => a.compliance_rate - b.compliance_rate);
    const topIssues = sortedQuestions.slice(0, 10);

    return (
      <div className="compliance-view">
        <div className="section-header">
          <h3>Top 10 Compliance Issues</h3>
          <p>Questions with lowest compliance rates</p>
        </div>

        <div className="questions-table">
          <table>
            <thead>
              <tr>
                <th>Q#</th>
                <th>Question</th>
                <th>Compliance Rate</th>
                <th>Yes</th>
                <th>No</th>
                <th>N/A</th>
                <th>NR</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {topIssues.map((q) => (
                <tr key={q.question_number}>
                  <td>{q.question_number}</td>
                  <td className="question-text">{q.question_text}</td>
                  <td>
                    <span className={`compliance-badge ${q.compliance_rate < 70 ? 'low' : q.compliance_rate < 85 ? 'medium' : 'high'}`}>
                      {q.compliance_rate.toFixed(1)}%
                    </span>
                  </td>
                  <td>{q.yes_count}</td>
                  <td>{q.no_count}</td>
                  <td>{q.na_count}</td>
                  <td>{q.nr_count}</td>
                  <td>{q.total_responses}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="section-header" style={{ marginTop: '2rem' }}>
          <h3>All Questions ({questions.length})</h3>
        </div>

        <div className="questions-table">
          <table>
            <thead>
              <tr>
                <th>Q#</th>
                <th>Question</th>
                <th>Compliance Rate</th>
                <th>Yes</th>
                <th>No</th>
                <th>N/A</th>
                <th>NR</th>
              </tr>
            </thead>
            <tbody>
              {questions.map((q) => (
                <tr key={q.question_number}>
                  <td>{q.question_number}</td>
                  <td className="question-text">{q.question_text}</td>
                  <td>
                    <span className={`compliance-badge ${q.compliance_rate < 70 ? 'low' : q.compliance_rate < 85 ? 'medium' : 'high'}`}>
                      {q.compliance_rate.toFixed(1)}%
                    </span>
                  </td>
                  <td>{q.yes_count}</td>
                  <td>{q.no_count}</td>
                  <td>{q.na_count}</td>
                  <td>{q.nr_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderSitesView = () => {
    return (
      <div className="sites-view">
        <div className="section-header">
          <h3>Site Performance Leaderboard</h3>
          <p>Top {sites.length} sites ranked by compliance rate</p>
        </div>

        <div className="sites-table">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Site #</th>
                <th>Country</th>
                <th>Institution</th>
                <th>PI</th>
                <th>Compliance</th>
                <th>Quality</th>
                <th>Enrollment</th>
                <th>Completion</th>
                <th>Reports</th>
                <th>Last Visit</th>
              </tr>
            </thead>
            <tbody>
              {sites.map((site, index) => (
                <tr key={site.site_number}>
                  <td>#{index + 1}</td>
                  <td><strong>{site.site_number}</strong></td>
                  <td>{site.country}</td>
                  <td className="institution-text">{site.institution}</td>
                  <td>{site.pi_name}</td>
                  <td>
                    <span className={`compliance-badge ${site.compliance_rate < 70 ? 'low' : site.compliance_rate < 85 ? 'medium' : 'high'}`}>
                      {site.compliance_rate.toFixed(1)}%
                    </span>
                  </td>
                  <td>{site.avg_quality_score.toFixed(1)}/5</td>
                  <td>{site.enrollment_rate.toFixed(1)}%</td>
                  <td>{site.completion_rate.toFixed(1)}%</td>
                  <td>{site.report_count}</td>
                  <td>{site.last_visit_date ? new Date(site.last_visit_date).toLocaleDateString() : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderGeographicView = () => {
    return (
      <div className="geographic-view">
        <div className="section-header">
          <h3>Geographic Summary</h3>
          <p>Performance metrics by country</p>
        </div>

        <div className="countries-grid">
          {countries.map((country) => (
            <div key={country.country} className="country-card">
              <h4>{country.country}</h4>
              <div className="country-stats">
                <div className="stat">
                  <span className="stat-value">{country.site_count}</span>
                  <span className="stat-label">Sites</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{country.report_count}</span>
                  <span className="stat-label">Reports</span>
                </div>
                <div className="stat">
                  <span className={`stat-value ${country.compliance_rate < 70 ? 'low' : country.compliance_rate < 85 ? 'medium' : 'high'}`}>
                    {country.compliance_rate.toFixed(1)}%
                  </span>
                  <span className="stat-label">Compliance</span>
                </div>
              </div>
              <div className="country-distribution">
                <div className="dist-item">
                  <span className="dist-label">Yes:</span>
                  <span className="dist-value">{country.yes_count}</span>
                </div>
                <div className="dist-item">
                  <span className="dist-label">No:</span>
                  <span className="dist-value">{country.no_count}</span>
                </div>
                <div className="dist-item">
                  <span className="dist-label">N/A:</span>
                  <span className="dist-value">{country.na_count}</span>
                </div>
                <div className="dist-item">
                  <span className="dist-label">NR:</span>
                  <span className="dist-value">{country.nr_count}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="analytics-container">
        <div className="loading">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-container">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h2>Analytics Dashboard</h2>
        <div className="analytics-controls">
          <div className="filter-group">
            <label>Time Period:</label>
            <select value={dateRange} onChange={(e) => setDateRange(e.target.value as any)}>
              <option value="all">All Time</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="ytd">Year to Date</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Study:</label>
            <select value={selectedProtocol} onChange={(e) => setSelectedProtocol(e.target.value)}>
              <option value="">All Studies</option>
              {protocols.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label>Country:</label>
            <select value={selectedCountry} onChange={(e) => setSelectedCountry(e.target.value)}>
              <option value="">All Countries</option>
              {countries.map((c) => (
                <option key={c.country} value={c.country}>{c.country}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="analytics-tabs">
        <button
          className={activeView === 'executive' ? 'tab active' : 'tab'}
          onClick={() => setActiveView('executive')}
        >
          Executive Dashboard
        </button>
        <button
          className={activeView === 'compliance' ? 'tab active' : 'tab'}
          onClick={() => setActiveView('compliance')}
        >
          Compliance Analysis
        </button>
        <button
          className={activeView === 'sites' ? 'tab active' : 'tab'}
          onClick={() => setActiveView('sites')}
        >
          Site Performance
        </button>
        <button
          className={activeView === 'geographic' ? 'tab active' : 'tab'}
          onClick={() => setActiveView('geographic')}
        >
          Geographic View
        </button>
      </div>

      <div className="analytics-content">
        {activeView === 'executive' && renderExecutiveDashboard()}
        {activeView === 'compliance' && renderComplianceView()}
        {activeView === 'sites' && renderSitesView()}
        {activeView === 'geographic' && renderGeographicView()}
      </div>
    </div>
  );
}

export default Analytics;
