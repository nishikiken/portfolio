# Инструкция по добавлению работ в галерею

Галерея работает полностью статически - без сервера и базы данных!

## Как добавить новую работу:

1. **Добавь изображение в папку `uploads/`**
   - Положи файл картинки в папку `C:\Users\Nishiki\Documents\GitHub\portfolio\uploads\`
   - Например: `my-work.jpg`

2. **Обнови файл `gallery.json`**
   - Открой файл `C:\Users\Nishiki\Documents\GitHub\portfolio\gallery.json`
   - Добавь новую запись:
   ```json
   [
     {
       "filename": "my-work.jpg",
       "title": "Название моей работы"
     },
     {
       "filename": "another-work.png",
       "title": "Еще одна работа"
     }
   ]
   ```

3. **Закоммить и запушить изменения**
   ```cmd
   cd C:\Users\Nishiki\Documents\GitHub\portfolio
   git add uploads/ gallery.json
   git commit -m "Add new gallery images"
   git push
   ```

4. **Готово!** Через 1-2 минуты изменения появятся на сайте

## Быстрый способ:

Можешь использовать батник для автоматического копирования и пуша:
1. Добавь картинки в `portfolio/uploads/`
2. Обнови `portfolio/gallery.json`
3. Запусти `portfolio/copy_to_git.bat`

## Формат gallery.json:

```json
[
  {
    "filename": "имя-файла.jpg",
    "title": "Название работы (опционально)"
  }
]
```

- `filename` - имя файла в папке uploads/
- `title` - название работы (можно оставить пустым: `"title": ""`)

## Поддерживаемые форматы:
- JPG/JPEG
- PNG
- GIF
- WebP

## Советы:
- Оптимизируй изображения перед загрузкой (рекомендуемый размер: до 2MB)
- Используй понятные имена файлов (латиница, без пробелов)
- Добавляй описательные названия в `title` для лучшего UX
