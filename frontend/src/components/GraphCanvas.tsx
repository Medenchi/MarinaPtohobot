/**
 * Интерактивная карта блоков. SVG-based, без сторонних зависимостей.
 *
 * Возможности:
 *  - drag-and-drop узлов мышью (позиции пишутся в node.position и сохраняются
 *    как часть graph — переживают reload);
 *  - bezier-«верёвочки» между узлами по полю `next` и между кнопками `target`;
 *  - вытягивание новой связи: схватили правый порт узла → отпустили на левом
 *    порту другого узла → next установился;
 *  - клик по узлу = выбор (как раньше);
 *  - подсветка ошибок валидатора (красная рамка для error, жёлтая для warning).
 */

import React, { useCallback, useMemo, useRef, useState } from "react";
import type { BlockNode, FlowGraph } from "@/types";
import { schemaFor } from "@/lib/blockSchemas";
import type { Issue } from "@/lib/validator";

const NODE_W = 200;
const NODE_H = 64;
const GRID = 24;

export interface GraphCanvasProps {
  graph: FlowGraph;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onChange: (graph: FlowGraph) => void;
  onRemove: (id: string) => void;
  issues?: Issue[];
}

type DragState =
  | { kind: "node"; id: string; offsetX: number; offsetY: number }
  | { kind: "link"; fromId: string; cursorX: number; cursorY: number }
  | null;

function levelClass(level: Issue["level"] | undefined): string {
  if (level === "error") return "stroke-red-500";
  if (level === "warning") return "stroke-amber-500";
  return "stroke-slate-300";
}

function nodeIssueLevel(id: string, issues?: Issue[]): Issue["level"] | undefined {
  if (!issues) return undefined;
  const matched = issues.filter((i) => i.node_id === id);
  if (matched.some((i) => i.level === "error")) return "error";
  if (matched.some((i) => i.level === "warning")) return "warning";
  if (matched.some((i) => i.level === "hint")) return "hint";
  return undefined;
}

function snap(v: number): number {
  return Math.round(v / GRID) * GRID;
}

/**
 * Возвращает позицию узла — либо из node.position, либо вычисляет дефолтную
 * по индексу. Чисто read-only, граф НЕ мутирует, чтобы не было бесконечных
 * setState→re-render циклов (это была причина «белого экрана»).
 */
function posOf(n: BlockNode, index: number): { x: number; y: number } {
  const p = n.position;
  if (p && typeof p.x === "number" && typeof p.y === "number") {
    // Старые seeds кладут логические индексы {x:0,y:1} — масштабируем визуально,
    // но в state не пишем (запишется только когда юзер сам подвинет блок).
    if (Math.abs(p.x) < 10 && Math.abs(p.y) < 10) {
      return { x: 80 + p.x * (NODE_W + 80), y: 80 + p.y * (NODE_H + 60) };
    }
    return { x: p.x, y: p.y };
  }
  return {
    x: 80 + (index % 4) * (NODE_W + 60),
    y: 80 + Math.floor(index / 4) * (NODE_H + 80),
  };
}

function bezierPath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = Math.max(40, Math.abs(x2 - x1) * 0.5);
  return `M ${x1},${y1} C ${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`;
}

export default function GraphCanvas(props: GraphCanvasProps) {
  const { graph, selectedId, onSelect, onChange, onRemove, issues } = props;
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [drag, setDrag] = useState<DragState>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [panning, setPanning] = useState<{ x: number; y: number } | null>(null);

  // index -> resolved position; считаем один раз за рендер, никаких setState отсюда
  const posByIdx = useMemo(
    () => graph.nodes.map((n, i) => posOf(n, i)),
    [graph.nodes],
  );
  const posById = useMemo(() => {
    const m: Record<string, { x: number; y: number }> = {};
    graph.nodes.forEach((n, i) => {
      if (n.id) m[n.id] = posByIdx[i];
    });
    return m;
  }, [graph.nodes, posByIdx]);

  const nodesById = useMemo(() => {
    const m: Record<string, BlockNode> = {};
    graph.nodes.forEach((n) => (m[n.id] = n));
    return m;
  }, [graph.nodes]);

  const toLocal = useCallback(
    (clientX: number, clientY: number) => {
      const svg = svgRef.current;
      if (!svg) return { x: 0, y: 0 };
      const r = svg.getBoundingClientRect();
      return { x: clientX - r.left - pan.x, y: clientY - r.top - pan.y };
    },
    [pan.x, pan.y],
  );

  function onMouseMove(e: React.MouseEvent) {
    if (drag?.kind === "node") {
      const { x, y } = toLocal(e.clientX, e.clientY);
      const nx = snap(x - drag.offsetX);
      const ny = snap(y - drag.offsetY);
      onChange({
        ...graph,
        nodes: graph.nodes.map((n) =>
          n.id === drag.id ? { ...n, position: { x: nx, y: ny } } : n,
        ),
      });
    } else if (drag?.kind === "link") {
      const { x, y } = toLocal(e.clientX, e.clientY);
      setDrag({ ...drag, cursorX: x, cursorY: y });
    } else if (panning) {
      setPan({ x: e.clientX - panning.x, y: e.clientY - panning.y });
    }
  }

  function onMouseUp() {
    setDrag(null);
    setPanning(null);
  }

  function startNodeDrag(e: React.MouseEvent, n: BlockNode) {
    e.stopPropagation();
    onSelect(n.id);
    const { x, y } = toLocal(e.clientX, e.clientY);
    const pos = posById[n.id] || { x: 0, y: 0 };
    setDrag({ kind: "node", id: n.id, offsetX: x - pos.x, offsetY: y - pos.y });
  }

  function startLink(e: React.MouseEvent, n: BlockNode) {
    e.stopPropagation();
    const { x, y } = toLocal(e.clientX, e.clientY);
    setDrag({ kind: "link", fromId: n.id, cursorX: x, cursorY: y });
  }

  function finishLinkOn(targetId: string) {
    if (drag?.kind === "link" && drag.fromId !== targetId) {
      onChange({
        ...graph,
        nodes: graph.nodes.map((n) =>
          n.id === drag.fromId ? { ...n, next: targetId } : n,
        ),
      });
    }
    setDrag(null);
  }

  function clearLink(fromId: string) {
    onChange({
      ...graph,
      nodes: graph.nodes.map((n) => (n.id === fromId ? { ...n, next: null } : n)),
    });
  }

  function onBgMouseDown(e: React.MouseEvent) {
    onSelect(null);
    setPanning({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  }

  // Все рёбра, которые нужно нарисовать
  const edges: { from: string; to: string; kind: "next" | "button" }[] = [];
  for (const n of graph.nodes) {
    if (n.next && nodesById[n.next]) edges.push({ from: n.id, to: n.next, kind: "next" });
    const btns = (n.params as Record<string, unknown>)?.buttons;
    if (Array.isArray(btns)) {
      for (const b of btns) {
        const t = (b as { next?: string; target?: string })?.next ||
          (b as { target?: string })?.target;
        if (t && nodesById[t]) edges.push({ from: n.id, to: t, kind: "button" });
      }
    }
  }

  return (
    <div className="relative w-full h-[70vh] border border-line rounded-lg bg-white overflow-hidden">
      <div className="absolute z-10 top-2 left-2 text-[10px] text-muted bg-white/80 px-2 py-1 rounded border border-line">
        Перетаскивайте блоки · тяните за правый порт → к левому, чтобы соединить · ПКМ по верёвочке — отвязать
      </div>
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onMouseDown={onBgMouseDown}
        style={{ cursor: panning ? "grabbing" : drag?.kind === "node" ? "grabbing" : "default" }}
      >
        <defs>
          <pattern id="grid" width={GRID} height={GRID} patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="#e5e7eb" />
          </pattern>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#64748b" />
          </marker>
          <marker id="arrow-blue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#0ea5e9" />
          </marker>
        </defs>
        <rect x="-2000" y="-2000" width="10000" height="10000" fill="url(#grid)" />
        <g transform={`translate(${pan.x},${pan.y})`}>
          {/* Edges */}
          {edges.map((e, i) => {
            const a = nodesById[e.from];
            const b = nodesById[e.to];
            if (!a || !b) return null;
            const ap = posById[a.id] || { x: 0, y: 0 };
            const bp = posById[b.id] || { x: 0, y: 0 };
            const ax = ap.x + NODE_W;
            const ay = ap.y + NODE_H / 2;
            const bx = bp.x;
            const by = bp.y + NODE_H / 2;
            const color = e.kind === "button" ? "#0ea5e9" : "#64748b";
            return (
              <path
                key={i}
                d={bezierPath(ax, ay, bx, by)}
                fill="none"
                stroke={color}
                strokeWidth={2}
                markerEnd={`url(#${e.kind === "button" ? "arrow-blue" : "arrow"})`}
                onContextMenu={(ev) => {
                  ev.preventDefault();
                  if (e.kind === "next") clearLink(e.from);
                }}
                style={{ cursor: e.kind === "next" ? "pointer" : "default" }}
              />
            );
          })}
          {/* Pending link */}
          {drag?.kind === "link" && posById[drag.fromId] && (
            <path
              d={bezierPath(
                posById[drag.fromId].x + NODE_W,
                posById[drag.fromId].y + NODE_H / 2,
                drag.cursorX,
                drag.cursorY,
              )}
              fill="none"
              stroke="#0ea5e9"
              strokeWidth={2}
              strokeDasharray="4 4"
            />
          )}
          {/* Nodes */}
          {graph.nodes.map((n, idx) => {
            const p = posByIdx[idx];
            const x = p.x;
            const y = p.y;
            const isSelected = n.id === selectedId;
            const level = nodeIssueLevel(n.id, issues);
            const schema = schemaFor(n.type);
            const params = (n.params || {}) as Record<string, unknown>;
            const subtitle = String(
              params.text || params.command || params.variable || params.pattern || "",
            ).slice(0, 40);
            return (
              <g
                key={n.id}
                transform={`translate(${x},${y})`}
                onMouseDown={(e) => startNodeDrag(e, n)}
                onMouseUp={() => finishLinkOn(n.id)}
                style={{ cursor: "grab" }}
              >
                <rect
                  width={NODE_W}
                  height={NODE_H}
                  rx={10}
                  fill="white"
                  className={`${levelClass(level)} ${isSelected ? "stroke-slate-900" : ""}`}
                  strokeWidth={isSelected ? 2 : 1.5}
                />
                <text x={12} y={22} fontSize={12} fontWeight={600} fill="#0f172a">
                  {schema?.title || n.type}
                </text>
                <text x={12} y={40} fontSize={10} fill="#64748b">
                  #{n.id}
                </text>
                <text x={12} y={56} fontSize={10} fill="#94a3b8">
                  {subtitle}
                </text>
                {/* left port (input) */}
                <circle cx={0} cy={NODE_H / 2} r={5} fill="#fff" stroke="#94a3b8" />
                {/* right port (output) */}
                <circle
                  cx={NODE_W}
                  cy={NODE_H / 2}
                  r={6}
                  fill="#0ea5e9"
                  stroke="#0369a1"
                  onMouseDown={(e) => startLink(e, n)}
                  style={{ cursor: "crosshair" }}
                />
                {/* delete */}
                <g
                  transform={`translate(${NODE_W - 18},6)`}
                  style={{ cursor: "pointer" }}
                  onMouseDown={(e) => {
                    e.stopPropagation();
                    if (confirm(`Удалить блок ${n.id}?`)) onRemove(n.id);
                  }}
                >
                  <circle r={8} fill="#fee2e2" />
                  <text x={-3} y={3} fontSize={11} fill="#b91c1c">
                    ×
                  </text>
                </g>
                {level && (
                  <circle
                    cx={NODE_W - 14}
                    cy={NODE_H - 10}
                    r={5}
                    fill={
                      level === "error" ? "#ef4444" : level === "warning" ? "#f59e0b" : "#94a3b8"
                    }
                  />
                )}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}
