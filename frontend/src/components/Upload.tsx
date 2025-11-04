import { useState } from 'react';
import { FileText, Upload as UploadIcon, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { uploadReport } from '../services/api';
import './Upload.css';

function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const response = await uploadReport(file);
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>Upload MOV Report</h2>

      <div className="upload-section">
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          disabled={uploading}
        />

        {file && (
          <div className="file-info">
            <FileText size={18} className="icon-inline" />
            File: {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </div>
        )}

        {file && (
          <button
            className="upload-button"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <Loader2 size={18} className="icon-inline spinner-icon" />
                Extracting...
              </>
            ) : (
              <>
                <UploadIcon size={18} className="icon-inline" />
                Extract Data
              </>
            )}
          </button>
        )}
      </div>

      {uploading && (
        <div className="spinner-container">
          <div className="spinner"></div>
          <p>Extracting data from {file?.name.endsWith('.docx') ? 'DOCX' : 'PDF'}...</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <XCircle size={18} className="icon-inline" />
          {error}
        </div>
      )}

      {result && (
        <div className="success-message">
          <h3>
            <CheckCircle size={24} className="icon-inline" />
            Extraction Complete!
          </h3>
          <div className="result-details">
            <p><strong>Report ID:</strong> {result.report_id}</p>
            <p><strong>Questions:</strong> {result.questions}</p>
            <p><strong>Action Items:</strong> {result.action_items}</p>
            <p><strong>Quality:</strong> {result.quality}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Upload;
