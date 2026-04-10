import { Handle, Position } from '@xyflow/react';
import { bandInfo, scoreColor } from '../utils.js';

export default function ScoringNode({ data }) {
  const score = data.score;
  const color = scoreColor(score);
  const band = bandInfo(score);

  return (
    <div
      className="rf-node node-scoring"
      style={{ borderColor: color, minWidth: 200 }}
    >
      <Handle type="target" position={Position.Top} />

      <div className="node-icon">⚙️</div>
      <div className="node-title">Scoring Engine</div>

      {score != null ? (
        <>
          <div className="node-score" style={{ color, fontSize: 36 }}>
            {score.toFixed(1)}
            <span style={{ fontSize: 16, fontWeight: 400, color: 'var(--text-muted)' }}>/100</span>
          </div>
          <div className="node-band" style={{ color }}>{band.label}</div>
          <div className="node-sub" style={{ marginTop: 6 }}>
            Weighted 7-pillar score
          </div>
        </>
      ) : (
        <div className="node-sub">Weighted sum → 0–100</div>
      )}

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
