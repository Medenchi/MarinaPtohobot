export function getTelegram(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

export function isTelegramWebApp(): boolean {
  return !!getTelegram()?.initData;
}

export function telegramReady(): void {
  const tg = getTelegram();
  if (tg) {
    tg.ready();
    tg.expand();
  }
}
