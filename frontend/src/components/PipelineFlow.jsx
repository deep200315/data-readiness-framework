import { useEffect } from 'react';
import {
  ReactFlow, Background, Controls, MiniMap,
  BackgroundVariant, useNodesState, useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import SourceNode      from '../nodes/SourceNode.jsx';
import ProcessNode     from '../nodes/ProcessNode.jsx';
import PillarNode      from '../nodes/PillarNode.jsx';
import ScoringNode     from '../nodes/ScoringNode.jsx';
import ReportNode      from '../nodes/ReportNode.jsx';
import PillarGroupNode from '../nodes/PillarGroupNode.jsx';
import { PILLAR_META, PILLAR_ORDER, scoreColor } from '../utils.js';
import { pdfUrl } from '../api.js';

const nodeTypes = {
  sourceNode:      SourceNode,
  processNode:     ProcessNode,
  pillarNode:      PillarNode,
  scoringNode:     ScoringNode,
  reportNode:      ReportNode,
  pillarGroupNode: PillarGroupNode,
};

// Layout
const CX        = 390;    // centre-column x (nodes are 200px wide → visual centre = 490)
const GROUP_X   = -60;    // group left edge
const GROUP_W   = 1250;   // group width
const GROUP_Y   = 468;    // group top edge
const GROUP_H   = 215;    // group height
const PIL_START = 25;     // pillar x inside group (left padding)
const PIL_STEP  = 175;    // pillar x stride

function buildNodes(results) {
  const pillars = results?.pillars ?? {};
  return [
    {
      id: 'source', type: 'sourceNode',
      position: { x: CX, y: 0 },
      data: {
        filename: results?.dataset_name,
        rows: results?.profile?.row_count,
        cols: results?.profile?.column_count,
      },
    },
    {
      id: 'ingestion', type: 'processNode',
      position: { x: CX, y: 150 },
      data: { icon: '⚙️', title: 'Ingestion & Parsing', subtitle: 'Pandas — load, parse, detect schema' },
    },
    {
      id: 'profiling', type: 'processNode',
      position: { x: CX, y: 305 },
      data: { icon: '🔍', title: 'Profiling Layer', subtitle: 'Missing maps · Correlations · Distributions' },
    },
    // ── Pillar subflow group ─────────────────────────────────
    {
      id: 'pillars-group', type: 'pillarGroupNode',
      position: { x: GROUP_X, y: GROUP_Y },
      style: { width: GROUP_W, height: GROUP_H, zIndex: -1 },
      data: {},
      selectable: false,
    },
    // 7 pillar nodes (child nodes, relative to group)
    ...PILLAR_ORDER.map((key, i) => {
      const meta   = PILLAR_META[key];
      const pillar = pillars[key];
      return {
        id:       key,
        type:     'pillarNode',
        parentId: 'pillars-group',
        position: { x: PIL_START + i * PIL_STEP, y: 45 },
        data: {
          label:      meta.label,
          icon:       meta.icon,
          weight:     meta.weight,
          score:      pillar?.score ?? null,
          passed:     pillar?.passed_checks ?? 0,
          total:      pillar?.total_checks ?? 0,
          isSelected: false,
        },
      };
    }),
    {
      id: 'scoring', type: 'scoringNode',
      position: { x: CX, y: 740 },
      data: { score: results?.overall_score ?? null },
    },
    {
      id: 'report', type: 'reportNode',
      position: { x: CX, y: 960 },
      data: {
        jobId:  results?.job_id,
        pdfUrl: results?.job_id ? pdfUrl(results.job_id) : null,
      },
    },
  ];
}

function buildEdges(results) {
  const active = !!results;
  const pillars = results?.pillars ?? {};
  const idle = { stroke: '#cbd5e1', strokeWidth: 2 };

  const make = (id, source, target, style) => ({
    id, source, target, type: 'smoothstep',
    style:    style ?? (active ? { stroke: '#4f8ef7', strokeWidth: 2 } : idle),
    animated: active,
  });

  const list = [
    make('e-src-ing', 'source',    'ingestion'),
    make('e-ing-pro', 'ingestion', 'profiling'),
  ];
  PILLAR_ORDER.forEach((key) => {
    const c = active ? scoreColor(pillars[key]?.score) : '#cbd5e1';
    const s = { stroke: c, strokeWidth: 2 };
    list.push(make(`e-pro-${key}`, 'profiling', key,       s));
    list.push(make(`e-${key}-scr`, key,         'scoring', s));
  });
  list.push(make('e-scr-rep', 'scoring', 'report'));
  return list;
}

export default function PipelineFlow({ results, selectedPillar, onPillarClick }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(buildNodes(null));
  const [edges, setEdges, onEdgesChange] = useEdgesState(buildEdges(null));

  // Rebuild nodes + edges when results arrive
  useEffect(() => {
    setNodes(buildNodes(results));
    setEdges(buildEdges(results));
  }, [results]); // eslint-disable-line

  // Update only isSelected — preserves drag positions
  useEffect(() => {
    setNodes((nds) =>
      nds.map((n) =>
        n.type === 'pillarNode'
          ? { ...n, data: { ...n.data, isSelected: n.id === selectedPillar } }
          : n
      )
    );
  }, [selectedPillar]); // eslint-disable-line

  function handleNodeClick(_, node) {
    if (node.type === 'pillarNode') {
      onPillarClick(selectedPillar === node.id ? null : node.id);
    }
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={handleNodeClick}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.12 }}
      minZoom={0.25}
      maxZoom={1.6}
      proOptions={{ hideAttribution: true }}
    >
      <Background variant={BackgroundVariant.Dots} gap={22} size={1} color="#e2e8f0" />
      <Controls />
      <MiniMap
        style={{
          background: '#ffffff',
          border: '1.5px solid #e2e8f0',
          borderRadius: 8,
          boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
        }}
        nodeColor={(n) => {
          if (n.type === 'pillarGroupNode') return '#dbeafe';
          if (n.type === 'pillarNode')      return scoreColor(n.data.score) ?? '#94a3b8';
          if (n.type === 'scoringNode')     return scoreColor(n.data.score) ?? '#94a3b8';
          return '#94a3b8';
        }}
        nodeStrokeColor="#ffffff"
        nodeStrokeWidth={2}
        maskColor="rgba(226,232,240,0.75)"
        zoomable
        pannable
      />
    </ReactFlow>
  );
}
