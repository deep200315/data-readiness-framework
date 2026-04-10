import { PILLAR_META, bandInfo, scoreColor } from '../utils.js';

export default function DetailPanel({ pillar, data, recommendations, onClose }) {
  const meta = PILLAR_META[pillar];
  const color = scoreColor(data?.score);
  const band = bandInfo(data?.score);

  // Filter recommendations that mention this pillar
  const pillarRecs = (recommendations ?? []).filter((r) =>
    r.toLowerCase().includes(pillar.replace('_', ' ')) ||
    r.toLowerCase().includes(meta.label.toLowerCase())
  );

  return (
    <div className="detail-panel">
      <div className="panel-header">
        <h3>
          <span>{meta.icon}</span>
          {meta.label}
        </h3>
        <button className="panel-close" onClick={onClose}>✕</button>
      </div>

      <div className="panel-body">
        {/* Score card */}
        <div className="panel-score-card" style={{ background: `${color}18`, borderColor: color }}>
          <div className="panel-score-num" style={{ color }}>{data?.score?.toFixed(1) ?? '—'}</div>
          <div className="panel-score-label" style={{ color }}>{band.label}</div>
          <div className="panel-score-sub">
            Weight: {meta.weight} · {data?.passed_checks ?? 0}/{data?.total_checks ?? 0} checks passed
          </div>
          <div style={{ marginTop: 14 }}>
            <div className="progress-bar-wrap">
              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${data?.score ?? 0}%`, background: color }}
                />
              </div>
              <span className="progress-label">{data?.score?.toFixed(1) ?? 0}/100</span>
            </div>
          </div>
        </div>

        {/* Issues */}
        <div className="panel-section">
          <h4>Issues Found</h4>
          {data?.issues?.length > 0 ? (
            <div className="issue-list">
              {data.issues.map((issue, i) => (
                <div key={i} className="issue-item">{issue}</div>
              ))}
            </div>
          ) : (
            <div className="no-issues">✓ No issues detected</div>
          )}
        </div>

        {/* Recommendations */}
        <div className="panel-section">
          <h4>Recommendations</h4>
          {pillarRecs.length > 0 ? (
            <div className="rec-list">
              {pillarRecs.map((r, i) => (
                <div key={i} className="rec-item">{r}</div>
              ))}
            </div>
          ) : (
            <div className="no-issues">✓ No remediation needed</div>
          )}
        </div>

        {/* Details key-values */}
        {data?.details && Object.keys(data.details).length > 0 && (
          <div className="panel-section">
            <h4>Details</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {Object.entries(data.details).slice(0, 12).map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: 12,
                    padding: '4px 0',
                    borderBottom: '1px solid var(--border)',
                  }}
                >
                  <span style={{ color: 'var(--text-muted)' }}>{k.replace(/_/g, ' ')}</span>
                  <span style={{ fontWeight: 600 }}>
                    {typeof v === 'number' ? (Number.isInteger(v) ? v : v.toFixed(3)) : String(v)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
