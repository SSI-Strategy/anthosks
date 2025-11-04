import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import { listReports, getReport } from '../services/api';
import type { ReportDetail } from '../types';
import './Review.css';

function Review() {
  const [reports, setReports] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const data = await listReports();
      setReports(data);
    } catch (err) {
      console.error('Failed to load reports:', err);
    }
  };

  const handleSelectReport = async (reportId: string) => {
    setLoading(true);
    try {
      const report = await getReport(reportId);
      setSelectedReport(report);
    } catch (err) {
      console.error('Failed to load report details:', err);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredQuestions = () => {
    if (!selectedReport) return [];

    switch (filter) {
      case 'no':
        return selectedReport.question_responses.filter(q => q.answer === 'No');
      case 'findings':
        return selectedReport.question_responses.filter(q => q.key_finding);
      case 'first20':
        return selectedReport.question_responses.slice(0, 20);
      default:
        return selectedReport.question_responses;
    }
  };

  const getSentimentClass = (sentiment: string) => {
    switch (sentiment) {
      case 'Positive':
        return 'sentiment-positive';
      case 'Negative':
        return 'sentiment-negative';
      case 'Neutral':
        return 'sentiment-neutral';
      case 'Unknown':
        return 'sentiment-unknown';
      default:
        return '';
    }
  };

  return (
    <div className="review-container">
      <h2>Review Extracted Data</h2>

      {reports.length === 0 ? (
        <div className="info-message">
          No reports to review. Upload a report in the Upload tab.
        </div>
      ) : (
        <div>
          <div className="report-selector">
            <label htmlFor="report-select">Select report:</label>
            <select
              id="report-select"
              onChange={(e) => handleSelectReport(e.target.value)}
              defaultValue=""
            >
              <option value="" disabled>Choose a report...</option>
              {reports.map((report) => (
                <option key={report.id} value={report.id}>
                  {report.site_number} - {report.visit_start_date}
                </option>
              ))}
            </select>
          </div>

          {loading && (
            <div className="loading">Loading report...</div>
          )}

          {selectedReport && !loading && (
            <div className="report-details">
              <div className="report-grid">
                <div className="report-main">
                  <section className="report-section">
                    <h3>Site Information</h3>
                    <p><strong>Site:</strong> {selectedReport.site_info.site_number} - {selectedReport.site_info.institution}</p>
                    <p><strong>Country:</strong> {selectedReport.site_info.country}</p>
                    <p><strong>PI:</strong> Dr. {selectedReport.site_info.pi_first_name} {selectedReport.site_info.pi_last_name}</p>
                    <p><strong>Visit:</strong> {selectedReport.visit_type} ({selectedReport.visit_start_date} to {selectedReport.visit_end_date})</p>
                  </section>

                  <section className="report-section">
                    <h3>Recruitment Statistics</h3>
                    <div className="stats-grid">
                      <div>Screened: <strong>{selectedReport.recruitment_stats.screened}</strong></div>
                      <div>Screen Failures: <strong>{selectedReport.recruitment_stats.screen_failures}</strong></div>
                      <div>Randomized: <strong>{selectedReport.recruitment_stats.randomized_enrolled}</strong></div>
                      <div>Discontinued: <strong>{selectedReport.recruitment_stats.early_discontinued}</strong></div>
                      <div>Completed Treatment: <strong>{selectedReport.recruitment_stats.completed_treatment}</strong></div>
                      <div>Completed Study: <strong>{selectedReport.recruitment_stats.completed_study}</strong></div>
                    </div>
                  </section>

                  <section className="report-section">
                    <h3>Questions ({selectedReport.question_responses.length})</h3>

                    <div className="filter-buttons">
                      <button
                        className={filter === 'all' ? 'active' : ''}
                        onClick={() => setFilter('all')}
                      >
                        All questions
                      </button>
                      <button
                        className={filter === 'no' ? 'active' : ''}
                        onClick={() => setFilter('no')}
                      >
                        Only 'No' answers
                      </button>
                      <button
                        className={filter === 'findings' ? 'active' : ''}
                        onClick={() => setFilter('findings')}
                      >
                        Only with findings
                      </button>
                      <button
                        className={filter === 'first20' ? 'active' : ''}
                        onClick={() => setFilter('first20')}
                      >
                        First 20
                      </button>
                    </div>

                    <div className="questions-list">
                      {getFilteredQuestions().map((q) => (
                        <details key={q.question_number} className={`question-item ${getSentimentClass(q.sentiment)}`}>
                          <summary>
                            <span className="question-number">Q{q.question_number}</span>
                            <span className="question-text">{q.question_text}</span>
                            <span className={`answer-badge ${getSentimentClass(q.sentiment)}`}>{q.answer}</span>
                          </summary>
                          <div className="question-details">
                            {q.narrative_summary && (
                              <p><strong>Summary:</strong> {q.narrative_summary}</p>
                            )}
                            {q.key_finding && (
                              <div className="key-finding">
                                <strong>
                                  <AlertTriangle size={16} className="icon-inline-sm" />
                                  Key Finding:
                                </strong> {q.key_finding}
                              </div>
                            )}
                          </div>
                        </details>
                      ))}
                    </div>
                  </section>
                </div>

                <div className="report-sidebar">
                  <section className="report-section">
                    <h3>Quality Assessment</h3>
                    <div className="quality-metric">
                      {selectedReport.overall_site_quality}
                    </div>

                    {selectedReport.key_concerns.length > 0 && (
                      <div className="concerns">
                        <h4>
                          <AlertTriangle size={18} className="icon-inline-sm" />
                          Concerns:
                        </h4>
                        <ul>
                          {selectedReport.key_concerns.map((concern, idx) => (
                            <li key={idx}>{concern}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {selectedReport.key_strengths.length > 0 && (
                      <div className="strengths">
                        <h4>
                          <CheckCircle size={18} className="icon-inline-sm" />
                          Strengths:
                        </h4>
                        <ul>
                          {selectedReport.key_strengths.map((strength, idx) => (
                            <li key={idx}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </section>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Review;
