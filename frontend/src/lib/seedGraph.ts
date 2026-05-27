// Minimal starter flow: /start → ask name → pick shoot type → confirm.
// Denis can replace this with anything via the constructor.
//
// Block types here MUST match those listed in blockSchemas.ts (and the
// Python runtime). Each node has params keyed exactly as the schema
// describes.

import type { FlowGraph } from "@/types";

export const SEED_GRAPH: FlowGraph = {
  nodes: [
    {
      id: "start",
      type: "command",
      params: { command: "start" },
      next: "hello",
      position: { x: 0, y: 0 },
    },
    {
      id: "hello",
      type: "send_message",
      params: {
        text:
          "Привет! Я бот Марины Заугольниковой — фотографа.\n\n" +
          "Помогу подобрать образ и записаться на съёмку. Поехали?",
      },
      next: "ask_name",
      position: { x: 0, y: 1 },
    },
    {
      id: "ask_name",
      type: "ask_question",
      params: {
        text: "Как тебя зовут?",
        variable: "name",
      },
      next: "ask_shoot_type",
      position: { x: 0, y: 2 },
    },
    {
      id: "ask_shoot_type",
      type: "ask_question",
      params: {
        text: "Какой тип съёмки тебе интересен?",
        variable: "shoot_type",
        inline: true,
        options: [
          { text: "Лав-стори", value: "love" },
          { text: "Семейная", value: "family" },
          { text: "Беременность", value: "preg" },
          { text: "Индивидуальная", value: "solo" },
        ],
      },
      next: "thanks",
      position: { x: 0, y: 3 },
    },
    {
      id: "thanks",
      type: "send_message",
      params: {
        text:
          "Спасибо, {{vars.name}}! Поняла, тебе интересно: {{vars.shoot_type}}.\n\n" +
          "Марина свяжется с тобой в ближайшее время.",
      },
      next: null,
      position: { x: 0, y: 4 },
    },
  ],
  edges: [],
};
