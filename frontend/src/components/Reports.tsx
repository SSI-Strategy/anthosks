import { useState, useEffect } from 'react';
import { listReports } from '../services/api';
import type { Report } from '../types';
import './Reports.css';

function Reports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await listReports();
      setReports(data);
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="reports-container">
      <h2>All Reports</h2>

      {loading ? (
        <div className="loading">Loading reports...</div>
      ) : reports.length === 0 ? (
        <div className="info-message">No reports found.</div>
      ) : (
        <div className="reports-table-container">
          <table className="reports-table">
            <thead>
              <tr>
                <th>Site</th>
                <th>Country</th>
                <th>Visit Date</th>
                <th>Type</th>
                <th>Quality</th>
                <th>Questions</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td>{report.site_number}</td>
                  <td>{report.country}</td>
                  <td>{report.visit_start_date}</td>
                  <td>{report.visit_type}</td>
                  <td>
                    <span className={`quality-badge quality-${report.quality.toLowerCase().replace(' ', '-')}`}>
                      {report.quality}
                    </span>
                  </td>
                  <td>{report.questions_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Reports;
