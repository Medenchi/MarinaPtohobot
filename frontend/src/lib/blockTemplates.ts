/**
 * Готовые шаблоны узлов и под-графов специально под флоу Марины
 * Заугольниковой. Кнопка «+ Шаблон» в конструкторе вставляет сразу
 * пачку узлов в правильном порядке — пользователь только цепляет
 * стрелочки к месту.
 *
 * Шаблоны делятся на:
 *   - "occasion" — про поводы съёмок (love-story, семейная, lookbook…)
 *   - "outfits"  — выборка/показ образов из БД по поводу
 *   - "courses"  — то же для курсов
 *   - "packages" — пакеты услуг Марины (15/25/35/115 тыс)
 *   - "contacts" — контакты, бронь, цены, важные условия
 */

import type { BlockNode } from "@/types";

export interface BlockTemplate {
  id: string;
  group: "occasion" | "outfits" | "courses" | "packages" | "contacts";
  title: string;
  description: string;
  /** Возвращает массив новых узлов с УЖЕ уникальными id (вызывается с генератором). */
  build: (genId: (prefix: string) => string) => BlockNode[];
}

// -- утилита для шаблона: создать ask_question с готовыми поводами --
function occasionPicker(genId: (p: string) => string, variable = "occasion"): BlockNode {
  return {
    id: genId("ask_occasion"),
    type: "ask_question",
    params: {
      text: "По какому поводу выбираем?",
      variable,
      inline: true,
      options: [
        { text: "💕 Love-story",        value: "love-story" },
        { text: "👨‍👩‍👧 Семейная",       value: "семейная съёмка" },
        { text: "🤰 Беременность",      value: "беременность" },
        { text: "👩 Индивидуальная",    value: "индивидуальная" },
        { text: "🤝 Lookbook",          value: "lookbook" },
        { text: "📱 Контент для соцсетей", value: "контент для соцсетей" },
        { text: "🎥 Репортаж",          value: "репортаж" },
      ],
    },
    next: null,
  };
}

export const BLOCK_TEMPLATES: BlockTemplate[] = [
  // ---- OCCASION ----
  {
    id: "occasion_picker",
    group: "occasion",
    title: "Вопрос: повод съёмки",
    description: "Готовый ask_question со всеми поводами Марины в кнопках.",
    build: (g) => [occasionPicker(g)],
  },

  // ---- OUTFITS BY OCCASION ----
  {
    id: "outfits_by_occasion_pack",
    group: "outfits",
    title: "Подборка образов по поводу",
    description:
      "Спрашивает повод → запрос в outfits с фильтром occasions ilike → шлёт альбом из 10 фото.",
    build: (g) => {
      const askId = g("ask_occasion");
      const qId = g("query_outfits");
      const albumId = g("album_outfits");
      return [
        {
          id: askId,
          type: "ask_question",
          params: {
            text: "По какому поводу подобрать образы?",
            variable: "occasion",
            inline: true,
            options: [
              { text: "💕 Love-story",     value: "love-story" },
              { text: "👨‍👩‍👧 Семейная",   value: "семейная съёмка" },
              { text: "🤰 Беременность",  value: "беременность" },
              { text: "🤝 Lookbook",      value: "lookbook" },
            ],
          },
          next: qId,
        },
        {
          id: qId,
          type: "db_query",
          params: {
            table: "outfits",
            select: "*, outfit_images(*)",
            filters: [
              { column: "occasions", op: "ilike", value: "%{{vars.occasion}}%" },
              { column: "is_published", op: "eq", value: "true" },
            ],
            order_by: "sort_order",
            limit: 10,
            save_to: "matched_outfits",
          },
          next: albumId,
        },
        {
          id: albumId,
          type: "send_album",
          params: {
            items_var: "matched_outfits",
            caption_template: "{{outfit.title}}",
          },
          next: null,
        },
      ];
    },
  },
  {
    id: "outfits_pdf_pack",
    group: "outfits",
    title: "PDF подборки образов",
    description: "Берёт matched_outfits и собирает их в один PDF с водяным знаком.",
    build: (g) => {
      const pdfId = g("pdf_outfits");
      return [
        {
          id: pdfId,
          type: "generate_pdf",
          params: {
            items_var: "matched_outfits",
            filename: "podbor_obrazov.pdf",
            caption: "Подборка для тебя, {{vars.name}} ✨",
            send_now: true,
            save_to: "pdf",
          },
          next: null,
        },
      ];
    },
  },

  // ---- COURSES ----
  {
    id: "courses_list_pack",
    group: "courses",
    title: "Список курсов",
    description: "Запрос published-курсов из БД + отправка их карточками.",
    build: (g) => {
      const qId = g("query_courses");
      const msgId = g("show_courses");
      return [
        {
          id: qId,
          type: "db_query",
          params: {
            table: "courses",
            select: "id, slug, title, description, cover_path, preview_pages",
            filters: [{ column: "is_published", op: "eq", value: "true" }],
            order_by: "sort_order",
            limit: 20,
            save_to: "courses",
          },
          next: msgId,
        },
        {
          id: msgId,
          type: "send_message",
          params: {
            text: "📚 <b>Курсы Марины</b>\n\nВот что есть прямо сейчас. Жми, чтобы узнать подробнее.",
            buttons: [
              [{ text: "📖 Открыть каталог", url: "https://zaugolnikova.ru/" }],
            ],
          },
          next: null,
        },
      ];
    },
  },

  // ---- PACKAGES (по брифу Марины) ----
  {
    id: "package_express",
    group: "packages",
    title: "Пакет «Экспресс» — 15 000 ₽",
    description: "Сообщение с описанием экспресс-пакета (1 час, 15 фото).",
    build: (g) => [
      {
        id: g("pkg_express"),
        type: "send_message",
        params: {
          text:
            "✨ <b>Экспресс — 15 000 ₽</b>\n\n" +
            "• Консультация и подбор студии\n" +
            "• 1 час съёмки\n" +
            "• 15 фото в цвете и ч/б (готовы за 14 рабочих дней)\n\n" +
            "<i>Все удачные исходники в jpg можно выкупить за 6 000 ₽.</i>",
          buttons: [[{ text: "✅ Записаться", next: "" }]],
        },
        next: null,
      },
    ],
  },
  {
    id: "package_light",
    group: "packages",
    title: "Пакет «Лайт» — 25 000 ₽",
    description: "Сообщение с описанием пакета Лайт.",
    build: (g) => [
      {
        id: g("pkg_light"),
        type: "send_message",
        params: {
          text:
            "🌿 <b>Лайт — 25 000 ₽</b>\n\n" +
            "• Консультация и подбор студии (аренда оплачивается отдельно)\n" +
            "• Съёмка до результата\n" +
            "• 40 фото в цвете и ч/б + все удачные исходники\n" +
            "• Срок: 14 рабочих дней",
          buttons: [[{ text: "✅ Записаться", next: "" }]],
        },
        next: null,
      },
    ],
  },
  {
    id: "package_comfort",
    group: "packages",
    title: "Пакет «Комфорт» — 35 000 ₽",
    description: "Сообщение с описанием пакета Комфорт.",
    build: (g) => [
      {
        id: g("pkg_comfort"),
        type: "send_message",
        params: {
          text:
            "💫 <b>Комфорт — 35 000 ₽</b>\n\n" +
            "• Консультация и подбор студии (аренда оплачивается отдельно)\n" +
            "• Съёмка до результата\n" +
            "• 80 фото в цвете и ч/б + все удачные исходники\n" +
            "• Срок: всего 7 рабочих дней",
          buttons: [[{ text: "✅ Записаться", next: "" }]],
        },
        next: null,
      },
    ],
  },
  {
    id: "package_turnkey",
    group: "packages",
    title: "Пакет «Под ключ» — 115 000 ₽",
    description: "Сообщение с описанием премиум-пакета.",
    build: (g) => [
      {
        id: g("pkg_turnkey"),
        type: "send_message",
        params: {
          text:
            "👑 <b>Под ключ — 115 000 ₽</b>\n\n" +
            "• Консультация, подбор и 3 часа аренды студии\n" +
            "• Макияж, причёска и 3 образа от стилиста\n" +
            "• Видео для Reels/Stories (по запросу)\n" +
            "• 100 фото в цвете и ч/б + все удачные исходники\n" +
            "• Срок: на следующий день",
          buttons: [[{ text: "✅ Записаться", next: "" }]],
        },
        next: null,
      },
    ],
  },
  {
    id: "package_reportage",
    group: "packages",
    title: "Репортажная съёмка — от 8 000 ₽/час",
    description: "Описание репортажа: от 2 часов, от 200 фото за неделю.",
    build: (g) => [
      {
        id: g("pkg_reportage"),
        type: "send_message",
        params: {
          text:
            "🎥 <b>Репортажная съёмка — от 8 000 ₽/час</b>\n\n" +
            "• От 2 часов\n" +
            "• Более 200 фото в течение недели\n" +
            "• Через закрытый Google Drive",
          buttons: [[{ text: "✅ Записаться", next: "" }]],
        },
        next: null,
      },
    ],
  },
  {
    id: "packages_menu",
    group: "packages",
    title: "Меню всех пакетов (кнопки)",
    description:
      "Сообщение со всеми 5 пакетами кнопками + 5 отдельных текстов под них.",
    build: (g) => {
      const menuId = g("packages_menu");
      const pkgs: { key: string; text: string; label: string }[] = [
        {
          key: "express",
          label: "✨ Экспресс — 15к",
          text:
            "✨ <b>Экспресс — 15 000 ₽</b>\n\n• Консультация и подбор студии\n• 1 час съёмки\n• 15 фото в цвете и ч/б (14 раб. дней)\n\n<i>Исходники jpg — +6 000 ₽.</i>",
        },
        {
          key: "light",
          label: "🌿 Лайт — 25к",
          text:
            "🌿 <b>Лайт — 25 000 ₽</b>\n\n• Подбор студии (аренда отдельно)\n• Съёмка до результата\n• 40 фото + все исходники\n• 14 раб. дней",
        },
        {
          key: "comfort",
          label: "💫 Комфорт — 35к",
          text:
            "💫 <b>Комфорт — 35 000 ₽</b>\n\n• Подбор студии (аренда отдельно)\n• Съёмка до результата\n• 80 фото + все исходники\n• 7 раб. дней",
        },
        {
          key: "turnkey",
          label: "👑 Под ключ — 115к",
          text:
            "👑 <b>Под ключ — 115 000 ₽</b>\n\n• 3 часа студии (включена аренда)\n• Стилист, визаж, причёска, 3 образа\n• Reels/Stories по запросу\n• 100 фото + все исходники, на след. день",
        },
        {
          key: "reportage",
          label: "🎥 Репортаж — от 8к/ч",
          text: "🎥 <b>Репортаж — от 8 000 ₽/час</b>\n\nОт 2 часов. 200+ фото за неделю.",
        },
      ];
      const nodes: BlockNode[] = [];
      const ids: Record<string, string> = {};
      for (const p of pkgs) {
        ids[p.key] = g(`pkg_${p.key}`);
      }
      nodes.push({
        id: menuId,
        type: "send_message",
        params: {
          text: "Выбери пакет, чтобы узнать подробности:",
          buttons: pkgs.map((p) => [{ text: p.label, next: ids[p.key] }]),
        },
        next: null,
      });
      for (const p of pkgs) {
        nodes.push({
          id: ids[p.key],
          type: "send_message",
          params: {
            text: p.text,
            buttons: [
              [{ text: "✅ Записаться", url: "https://t.me/marina_photo" }],
              [{ text: "← К пакетам", next: menuId }],
            ],
          },
          next: null,
        });
      }
      return nodes;
    },
  },

  // ---- CONTACTS / RULES ----
  {
    id: "contacts_card",
    group: "contacts",
    title: "Контакты Марины",
    description: "Карточка с телефоном, почтой и ссылками.",
    build: (g) => [
      {
        id: g("contacts"),
        type: "send_message",
        params: {
          text:
            "📍 <b>Марина Заугольникова</b>\n" +
            "Женский и контент-фотограф, Москва\n\n" +
            "📞 +7 (985) 196-30-84\n" +
            "✉️ mzaugolnikova@gmail.com\n\n" +
            "<i>ИП Заугольникова М.В., ИНН 560704286100</i>",
          buttons: [
            [{ text: "🌐 Сайт", url: "https://zaugolnikova.ru/" }],
            [{ text: "💬 Telegram", url: "https://t.me/marina_photo" }],
          ],
        },
        next: null,
      },
    ],
  },
  {
    id: "preparation_stages",
    group: "contacts",
    title: "Этапы подготовки к съёмке",
    description: "Сообщение с 4 этапами: бриф → локация → образы → напоминание.",
    build: (g) => [
      {
        id: g("stages"),
        type: "send_message",
        params: {
          text:
            "🗂 <b>Этапы подготовки</b>\n\n" +
            "1. <b>Бриф и созвон</b> — обсуждаем задачи (для контент-съёмок)\n" +
            "2. <b>Локация</b> — подбираю минималистичные студии с естественным светом\n" +
            "3. <b>Образы</b> — присылаю рекомендации. По запросу даю контакты стилиста и визажиста\n" +
            "4. <b>Напоминание</b> — подтверждаем встречу за день до съёмки",
        },
        next: null,
      },
    ],
  },
  {
    id: "important_terms",
    group: "contacts",
    title: "Важные условия (бронь, ретушь, исходники)",
    description: "Юридический минимум: задаток 6к, перенос ≤2 раз, ретушь, исходники.",
    build: (g) => [
      {
        id: g("terms"),
        type: "send_message",
        params: {
          text:
            "📜 <b>Важные условия</b>\n\n" +
            "<b>Бронирование:</b> по задатку 6 000 ₽. Задаток не возвращается, если студия подобрана и рекомендации отправлены. Перенос даты — не более 2 раз.\n\n" +
            "<b>Стиль и ретушь:</b> естественный свет, лёгкая ретушь без пластики. Выбирая Марину, ты соглашаешься с её авторским стилем.\n\n" +
            "<b>Исходники:</b> фото для обработки отбираю сама. Сырой материал не отдаю (кроме пакетов, где исходники включены).\n\n" +
            "<b>Формат:</b> ссылка на персональную галерею.",
        },
        next: null,
      },
    ],
  },
];

export const TEMPLATE_GROUPS: { id: BlockTemplate["group"]; title: string }[] = [
  { id: "occasion", title: "Поводы съёмок" },
  { id: "outfits", title: "Образы" },
  { id: "courses", title: "Курсы" },
  { id: "packages", title: "Пакеты Марины" },
  { id: "contacts", title: "Контакты и условия" },
];
