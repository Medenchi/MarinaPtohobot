# 🚀 Wisp Startup Command — авто-pull при каждом рестарте

## Проблема

Текущая команда старта в Wisp **клонирует репо только если папки `.git` нет**:
```bash
if [[ ! -d .git ]] && [[ "0" != "1" ]]; then git clone ...; fi
```

После первого клона `.git` уже есть → клон не повторяется → код остаётся **навсегда замороженным** на первой версии. Любые мои фиксы в Github не попадают в бота, даже после Restart.

## Решение

Замени стартовую команду в **Wisp Panel → Startup** на:

```bash
if [[ -d .git ]]; then
  git pull origin main 2>&1 || true
else
  if [[ -n "${USERNAME}" ]] && [[ -n "${ACCESS_TOKEN}" ]]; then
    git clone -b main "https://${USERNAME}:${ACCESS_TOKEN}@github.com/Medenchi/MarinaPtohobot.git" .
  else
    git clone -b main https://github.com/Medenchi/MarinaPtohobot.git .
  fi
fi
pip install -r requirements.txt
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
python -u backend/app/bot/main.py
```

Что делает:
1. **Если `.git` есть** → `git pull origin main` (тянет последние коммиты)
2. **Если нет** → клонирует впервые
3. `|| true` — даже если pull упадёт (например конфликт), бот всё равно запустится
4. Дальше — стандартный `pip install` + запуск

После замены команды:
- Restart контейнера в Wisp = автоматически pull последнего кода с GitHub
- Не нужно никаких ручных действий

## Где это поменять

1. Открой [Wisp Panel](https://wispbyte.com) → твой сервер
2. Слева **Settings** → **Startup** (или **Stop & Start Parameters**)
3. Найди поле **Startup Command** (длинная команда с pip install)
4. Полностью замени её на блок выше
5. **Save**
6. Restart сервера

Готово. Теперь после каждого моего push в main — твой Restart подтянет фикс.
