import { Handle, Position } from '@xyflow/react';

export default function ProcessNode({ data }) {
  return (
    <div className="rf-node">
      <Handle type="target" position={Position.Top} />
      <div className="node-icon">{data.icon}</div>
      <div className="node-title">{data.title}</div>
      <div className="node-sub">{data.subtitle}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
