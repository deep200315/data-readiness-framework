export const scoreColor = (score) => {
  if (score == null) return '#4a5568';
  if (score >= 85) return '#27ae60';
  if (score >= 70) return '#2ecc71';
  if (score >= 50) return '#f39c12';
  return '#e74c3c';
};

export const bandInfo = (score) => {
  if (score == null) return { label: '—', color: '#4a5568' };
  if (score >= 85) return { label: 'Excellent', color: '#27ae60' };
  if (score >= 70) return { label: 'Good', color: '#2ecc71' };
  if (score >= 50) return { label: 'At Risk', color: '#f39c12' };
  return { label: 'Not Ready', color: '#e74c3c' };
};

export const PILLAR_META = {
  completeness: { label: 'Completeness', weight: '20%', icon: '📋' },
  validity:     { label: 'Validity',     weight: '15%', icon: '✅' },
  uniqueness:   { label: 'Uniqueness',   weight: '10%', icon: '🔑' },
  consistency:  { label: 'Consistency',  weight: '15%', icon: '🔗' },
  timeliness:   { label: 'Timeliness',   weight: '10%', icon: '⏱' },
  accuracy:     { label: 'Accuracy',     weight: '15%', icon: '🎯' },
  ai_readiness: { label: 'AI Readiness', weight: '15%', icon: '🤖' },
};

export const PILLAR_ORDER = [
  'completeness', 'validity', 'uniqueness', 'consistency',
  'timeliness', 'accuracy', 'ai_readiness',
];
