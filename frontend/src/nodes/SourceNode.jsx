import { Handle, Position } from '@xyflow/react';

export default function SourceNode({ data }) {
  return (
    <div className="rf-node node-source">
      <div className="node-icon">📂</div>
      <div className="node-title">Data Source</div>
      {data.filename ? (
        <div className="node-sub">
          {data.filename}<br />
          {data.rows?.toLocaleString()} rows · {data.cols} cols
        </div>
      ) : (
        <div className="node-sub">CSV / Excel Upload</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
