import { useState } from 'react';
import { uploadFile } from './api.js';
import UploadZone from './components/UploadZone.jsx';
import PipelineFlow from './components/PipelineFlow.jsx';
import DetailPanel from './components/DetailPanel.jsx';

export default function App() {
  const [phase, setPhase] = useState('idle'); // idle | uploading | done
  const [results, setResults] = useState(null);
  const [selectedPillar, setSelectedPillar] = useState(null);
  const [error, setError] = useState(null);

  async function handleFile(file) {
    setError(null);
    setPhase('uploading');
    setSelectedPillar(null);
    try {
      const data = await uploadFile(file);
      setResults(data);
      setPhase('done');
    } catch (err) {
      setError(err.message || 'Upload failed');
      setPhase('idle');
    }
  }

  function handleReset() {
    setPhase('idle');
    setResults(null);
    setSelectedPillar(null);
    setError(null);
  }

  return (
    <div className="app">
      <header className="header">
        <span style={{ fontSize: 24 }}>📊</span>
        <h1>AI Data Readiness Framework</h1>
        {results && (
          <>
            <span className="header-badge">
              {results.dataset_name}
            </span>
            <button className="btn btn-outline" onClick={handleReset} style={{ marginLeft: 8 }}>
              ↩ New Dataset
            </button>
          </>
        )}
        <span className="header-sub">7-Pillar Scoring Engine</span>
      </header>

      <div className="main-area">
        {phase === 'idle' && (
          <UploadZone onFile={handleFile} error={error} />
        )}

        {phase === 'uploading' && (
          <div className="loading-page">
            <div className="spinner" />
            <h3>Analysing your dataset…</h3>
            <p>Running 7-pillar validation and scoring</p>
            <div className="loading-steps">
              {['Ingesting & parsing', 'Profiling columns', 'Running validators', 'Computing scores', 'Generating recommendations'].map((s, i) => (
                <div key={i} className="loading-step active">⟳ {s}</div>
              ))}
            </div>
          </div>
        )}

        {phase === 'done' && results && (
          <>
            <div className="canvas-area" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <div style={{ flex: 1, position: 'relative' }}>
              <PipelineFlow
                results={results}
                selectedPillar={selectedPillar}
                onPillarClick={setSelectedPillar}
              />
              </div>

              {/* Bottom stats bar */}
              <div className="stats-bar">
                {[
                  { label: 'Rows', value: results.profile.row_count?.toLocaleString() },
                  { label: 'Columns', value: results.profile.column_count },
                  { label: 'Missing', value: `${results.profile.overall_missing_pct}%` },
                  { label: 'Duplicates', value: results.profile.duplicate_rows?.toLocaleString() },
                  { label: 'Memory', value: `${results.profile.memory_mb} MB` },
                ].map(({ label, value }) => (
                  <div key={label} className="stat-cell">
                    <div className="stat-value">{value ?? '—'}</div>
                    <div className="stat-label">{label}</div>
                  </div>
                ))}
              </div>
            </div>

            {selectedPillar && (
              <DetailPanel
                pillar={selectedPillar}
                data={results.pillars[selectedPillar]}
                recommendations={results.recommendations}
                onClose={() => setSelectedPillar(null)}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
