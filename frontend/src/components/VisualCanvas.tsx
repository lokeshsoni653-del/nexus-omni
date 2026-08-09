"use client";

import React, { useState, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Node,
  Edge,
  Connection,
  NodeChange,
  EdgeChange,
  BackgroundVariant,
} from '@xyflow/react';

import { AgentNode } from './nodes/AgentNode';
import { ToolNode } from './nodes/ToolNode';
import { CustomNodeData, AgentRoleType, ToolKindType } from '../types/workflow';

interface VisualCanvasProps {
  nodes: Node<CustomNodeData>[];
  edges: Edge[];
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
}

export const VisualCanvas: React.FC<VisualCanvasProps> = ({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
}) => {
  // Register custom React Flow node types
  const nodeTypes = useMemo(
    () => ({
      agentNode: AgentNode,
      toolNode: ToolNode,
    }),
    []
  );

  return (
    <div className="w-full h-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        defaultEdgeOptions={{
          animated: true,
          style: { stroke: '#38bdf8', strokeWidth: 2.5 },
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1.5} color="rgba(255, 255, 255, 0.08)" />
        <Controls className="glass-panel" />
        <MiniMap
          nodeColor={(node) => {
            if (node.type === 'toolNode') return '#06b6d4';
            const role = (node.data as CustomNodeData)?.role;
            if (role === 'orchestrator') return '#a855f7';
            if (role === 'rag') return '#10b981';
            if (role === 'reviewer') return '#f59e0b';
            return '#3b82f6';
          }}
          maskColor="rgba(9, 13, 22, 0.85)"
        />
      </ReactFlow>
    </div>
  );
};
