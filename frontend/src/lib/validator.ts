/**
 * Mirror of backend/app/bot/runtime/validator.py — те же правила, но в TS,
 * чтобы в конструкторе видно было проблемы до публикации, а не из логов бота.
 */

import type { BlockNode, FlowGraph } from "@/types";

export type Level = "error" | "warning" | "hint";

export interface Issue {
  level: Level;
  node_id: string | null;
  message: string;
  code: string;
}

const TRIGGER_TYPES = new Set(["command", "text_match"]);
const NEXT_BEARING = new Set([
  "send_message",
  "ask_question",
  "set_var",
  "branch",
  "send_photo",
  "send_document",
  "buttons",
  "delay",
]);

export function validateGraph(graph: FlowGraph): Issue[] {
  const issues: Issue[] = [];
  const nodes = (graph?.nodes || []).filter(Boolean) as BlockNode[];
  const idCounts = new Map<string, number>();
  for (const n of nodes) {
    if (!n.id) {
      issues.push({ level: "error", node_id: null, code: "missing_id", message: "Узел без id" });
      continue;
    }
    idCounts.set(n.id, (idCounts.get(n.id) || 0) + 1);
  }
  for (const [nid, c] of idCounts) {
    if (c > 1) {
      issues.push({
        level: "error",
        node_id: nid,
        code: "duplicate_id",
        message: `id «${nid}» встречается ${c} раз`,
      });
    }
  }

  if (!nodes.some((n) => TRIGGER_TYPES.has(n.type))) {
    issues.push({
      level: "error",
      node_id: null,
      code: "no_trigger",
      message: "В флоу нет ни одного триггера (command/text_match)",
    });
  }

  const byId = new Map(nodes.filter((n) => n.id).map((n) => [n.id, n]));

  for (const n of nodes) {
    const nid = n.id || "?";
    const params = (n.params || {}) as Record<string, unknown>;
    if (n.next && !byId.has(n.next)) {
      issues.push({
        level: "error",
        node_id: nid,
        code: "dangling_next",
        message: `next=«${n.next}» указывает в никуда`,
      });
    }
    if (n.next === nid && NEXT_BEARING.has(n.type)) {
      issues.push({
        level: "warning",
        node_id: nid,
        code: "self_loop",
        message: "Узел ссылается сам на себя — возможен бесконечный цикл",
      });
    }
    if (n.type === "send_message" && !(params.text as string)?.trim()) {
      issues.push({
        level: "warning",
        node_id: nid,
        code: "empty_text",
        message: "Пустой текст сообщения",
      });
    }
    if (n.type === "ask_question") {
      if (!(params.variable as string)?.trim()) {
        issues.push({
          level: "error",
          node_id: nid,
          code: "no_variable",
          message: "ask_question без переменной — ответ потеряется",
        });
      }
      if (!(params.text as string)?.trim()) {
        issues.push({
          level: "warning",
          node_id: nid,
          code: "empty_question",
          message: "Вопрос без текста",
        });
      }
    }
    if (n.type === "buttons") {
      const btns = (params.buttons as Array<{ target?: string; next?: string | null }>) || [];
      if (!btns.length) {
        issues.push({
          level: "warning",
          node_id: nid,
          code: "no_buttons",
          message: "У блока кнопок пустой список",
        });
      }
      for (const b of btns) {
        const t = b?.target || b?.next || null;
        if (t && !byId.has(t)) {
          issues.push({
            level: "error",
            node_id: nid,
            code: "dangling_button",
            message: `Кнопка ведёт на «${t}», которого нет`,
          });
        }
      }
    }
  }

  // достижимость
  const reachable = new Set<string>();
  const stack = nodes.filter((n) => TRIGGER_TYPES.has(n.type) && n.id).map((n) => n.id as string);
  while (stack.length) {
    const cur = stack.pop()!;
    if (reachable.has(cur)) continue;
    reachable.add(cur);
    const n = byId.get(cur);
    if (!n) continue;
    if (n.next) stack.push(n.next);
    const btns = ((n.params as Record<string, unknown>)?.buttons as Array<{ target?: string; next?: string }>) || [];
    for (const b of btns) {
      const t = b?.target || b?.next;
      if (t) stack.push(t);
    }
    if (n.type === "branch") {
      const p = (n.params as Record<string, unknown>) || {};
      for (const k of ["true_next", "false_next"] as const) {
        const t = p[k] as string | undefined;
        if (t) stack.push(t);
      }
    }
  }
  for (const n of nodes) {
    if (!n.id || TRIGGER_TYPES.has(n.type)) continue;
    if (!reachable.has(n.id)) {
      issues.push({
        level: "hint",
        node_id: n.id,
        code: "unreachable",
        message: "Блок не достижим ни из одного триггера",
      });
    }
  }

  return issues;
}

export function summary(issues: Issue[]): Record<Level, number> {
  const o: Record<Level, number> = { error: 0, warning: 0, hint: 0 };
  for (const i of issues) o[i.level]++;
  return o;
}
