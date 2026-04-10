export default function PillarGroupNode() {
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        borderRadius: 12,
        border: '2px dashed #1d4ed8',
        background: 'rgba(29,78,216,0.07)',
        position: 'relative',
      }}
    >
      <span
        style={{
          position: 'absolute',
          top: -18,
          left: 14,
          fontSize: 11,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.8px',
          color: '#1e3a8a',
          background: '#f0f4f8',
          padding: '0 6px',
        }}
      >
        Validation &amp; Scoring Layer
      </span>

    </div>
  );
}
