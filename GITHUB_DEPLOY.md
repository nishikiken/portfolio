# Деплой портфолио на GitHub Pages

## Вариант 1: Статичная галерея (рекомендуется для GitHub Pages)

Этот вариант позволяет хранить изображения прямо в репозитории GitHub.

### Шаг 1: Подготовка файлов

1. Создайте папку `gallery_images` в папке `portfolio`
2. Поместите туда все изображения для галереи
3. Создайте файл `gallery_data.json` с данными:

```json
[
  {
    "id": 1,
    "filename": "image1.jpg",
    "title": "Название работы 1",
    "created_at": "2026-04-27T10:00:00"
  },
  {
    "id": 2,
    "filename": "image2.jpg",
    "title": "Название работы 2",
    "created_at": "2026-04-27T10:00:00"
  }
]
```

### Шаг 2: Обновите portfolio.html

Замените в скрипте:
```javascript
const API_URL = 'http://localhost:5000/api';
```

На:
```javascript
const API_URL = './api'; // Для локальных файлов
const USE_STATIC_MODE = true; // Включить статичный режим
```

### Шаг 3: Загрузка на GitHub

```bash
git add .
git commit -m "Add portfolio with gallery"
git push origin main
```

### Шаг 4: Включите GitHub Pages

1. Зайдите в Settings репозитория
2. Перейдите в Pages
3. Выберите ветку `main` и папку `/portfolio` (или root)
4. Сохраните

Сайт будет доступен по адресу: `https://ваш-username.github.io/название-репо/portfolio.html`

### Обновление галереи

Чтобы добавить новые изображения:
1. Добавьте файлы в папку `gallery_images`
2. Обновите `gallery_data.json`
3. Закоммитьте и запушьте изменения

---

## Вариант 2: Динамическая галерея с внешним сервером

Для полноценной админ-панели нужен отдельный сервер.

### Опция A: Vercel (бесплатно)

1. Установите Vercel CLI:
```bash
npm install -g vercel
```

2. Создайте `vercel.json` в папке portfolio:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "upload_server.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "upload_server.py"
    }
  ]
}
```

3. Деплой:
```bash
cd portfolio
vercel
```

4. Обновите API_URL в portfolio.html на URL от Vercel

### Опция B: Railway (бесплатно)

1. Зарегистрируйтесь на railway.app
2. Создайте новый проект из GitHub репозитория
3. Railway автоматически определит Python и запустит сервер
4. Получите URL и обновите API_URL в portfolio.html

### Опция C: PythonAnywhere (бесплатно)

1. Зарегистрируйтесь на pythonanywhere.com
2. Загрузите файлы через Files
3. Настройте Web App с Flask
4. Обновите API_URL на ваш pythonanywhere URL

---

## Вариант 3: Гибридный подход (лучший для вас)

Используйте GitHub Pages для сайта + отдельный сервер для админки.

### Настройка:

1. **Сайт на GitHub Pages** - статичные файлы
2. **Сервер на Railway/Vercel** - только для загрузки
3. **Изображения в GitHub** - автоматически коммитятся

### Создайте скрипт auto_commit.py:

```python
import os
import json
import subprocess
from datetime import datetime

def auto_commit_images():
    # Проверяем новые файлы
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    
    if result.stdout:
        # Есть изменения
        subprocess.run(['git', 'add', 'portfolio/gallery_images/*'])
        subprocess.run(['git', 'add', 'portfolio/gallery_data.json'])
        subprocess.run(['git', 'commit', '-m', 
                       f'Auto: Update gallery {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
        subprocess.run(['git', 'push'])
        print('✓ Изменения загружены на GitHub')
    else:
        print('Нет изменений')

if __name__ == '__main__':
    auto_commit_images()
```

Добавьте в upload_server.py после сохранения файла:
```python
# После успешной загрузки
os.system('python auto_commit.py')
```

---

## Рекомендация

Для вашего случая лучше всего:

1. **Сайт** - GitHub Pages (бесплатно, быстро)
2. **Админка** - Railway (бесплатно, автодеплой)
3. **Изображения** - GitHub репозиторий (автокоммит)

Это даст вам:
- ✓ Бесплатный хостинг
- ✓ Автоматические обновления
- ✓ Работающую админ-панель
- ✓ Быстрый сайт
