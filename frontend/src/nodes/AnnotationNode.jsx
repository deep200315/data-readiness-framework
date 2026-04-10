export default function AnnotationNode({ data }) {
  return (
    <div
      style={{
        width: 180,
        fontSize: 18,
        color: '#4f8ef7',
        fontWeight: 500,
        lineHeight: 1.6,
        pointerEvents: 'none',
        userSelect: 'none',
      }}
    >
      {data.text}
      <div style={{ fontSize: 24, marginTop: 6 }}>{data.arrow}</div>
    </div>
  );
}
