import { Handle, Position } from '@xyflow/react';
import { scoreColor } from '../utils.js';

export default function PillarNode({ data, selected }) {
  const color = scoreColor(data.score);
  const isSelected = data.isSelected;

  return (
    <div
      className={`rf-node clickable${isSelected ? ' selected-node' : ''}`}
      style={{ borderTop: `3px solid ${color}`, minWidth: 150 }}
    >
      <Handle type="target" position={Position.Top} />

      <div className="node-icon">{data.icon}</div>
      <div className="node-title" style={{ fontSize: 12 }}>{data.label}</div>

      {data.score != null ? (
        <>
          <div className="node-score" style={{ color }}>{data.score.toFixed(1)}</div>
          <div className="node-checks">
            {data.passed}/{data.total} checks
          </div>
        </>
      ) : (
        <div className="node-sub" style={{ marginTop: 6 }}>—</div>
      )}

      <div className="node-sub" style={{ marginTop: 4, fontSize: 10, opacity: 0.6 }}>
        {data.weight}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
