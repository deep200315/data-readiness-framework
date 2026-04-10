import { Handle, Position } from '@xyflow/react';

export default function ReportNode({ data }) {
  return (
    <div className="rf-node node-report" style={{ minWidth: 200 }}>
      <Handle type="target" position={Position.Top} />

      <div className="node-icon">📄</div>
      <div className="node-title">Report & Export</div>
      <div className="node-sub" style={{ marginBottom: 10 }}>
        Streamlit UI · Plotly Charts
      </div>

      {data.jobId && (
        <a
          href={data.pdfUrl}
          download="readiness_report.pdf"
          className="btn btn-green"
          style={{ textDecoration: 'none', fontSize: 12, padding: '6px 14px', display: 'inline-flex' }}
          onClick={(e) => e.stopPropagation()}
        >
          ⬇ Download PDF
        </a>
      )}
    </div>
  );
}
