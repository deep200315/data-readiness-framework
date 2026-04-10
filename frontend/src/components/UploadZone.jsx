import { useRef, useState } from 'react';

export default function UploadZone({ onFile, error }) {
  const inputRef = useRef();
  const [dragOver, setDragOver] = useState(false);

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  }

  function handleChange(e) {
    const file = e.target.files[0];
    if (file) onFile(file);
  }

  return (
    <div className="upload-page" style={{ flex: 1 }}>
      <div className="upload-hero">
        <h2>AI Data Readiness Framework</h2>
        <p>
          Upload your dataset and get an instant Data Readiness Score (0–100)
          across 7 quality dimensions — with actionable ML remediation advice.
        </p>
      </div>

      <div
        className={`upload-zone${dragOver ? ' drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current.click()}
      >
        <div className="upload-icon">📂</div>
        <h3>Drop your dataset here</h3>
        <p>CSV or Excel files · Up to 200 MB</p>
        <button className="btn btn-primary" onClick={(e) => { e.stopPropagation(); inputRef.current.click(); }}>
          Browse Files
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          style={{ display: 'none' }}
          onChange={handleChange}
        />
      </div>

      {error && (
        <div style={{ color: 'var(--red)', fontSize: 13, maxWidth: 460, textAlign: 'center' }}>
          ⚠ {error}
        </div>
      )}

      <p className="upload-note">
        Try the DataCo Supply Chain Dataset from Kaggle (180K rows × 53 cols)
      </p>
    </div>
  );
}
