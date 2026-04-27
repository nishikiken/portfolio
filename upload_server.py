from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import subprocess

app = Flask(__name__)
CORS(app)

# Настройки
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
GALLERY_DATA_FILE = 'gallery_data.json'
AUTO_DEPLOY = os.environ.get('AUTO_DEPLOY', 'false').lower() == 'true'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Создаем папку для загрузок если её нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_gallery_data():
    if os.path.exists(GALLERY_DATA_FILE):
        with open(GALLERY_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_gallery_data(data):
    with open(GALLERY_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def auto_deploy():
    """Автоматически деплоит изменения на GitHub"""
    if not AUTO_DEPLOY:
        return
    
    try:
        subprocess.run(['python', 'auto_deploy.py'], check=True)
        print('✓ Изменения автоматически загружены на GitHub')
    except Exception as e:
        print(f'⚠️ Не удалось автоматически задеплоить: {e}')

@app.route('/api/gallery/upload', methods=['POST'])
def upload_gallery_image():
    if 'image' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400
    
    file = request.files['image']
    title = request.form.get('title', '')
    
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Добавляем timestamp для уникальности
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Сохраняем данные изображения
        gallery_data = load_gallery_data()
        new_id = max([item['id'] for item in gallery_data], default=0) + 1
        gallery_data.append({
            'id': new_id,
            'filename': filename,
            'title': title,
            'created_at': datetime.now().isoformat()
        })
        save_gallery_data(gallery_data)
        
        # Автоматический деплой
        auto_deploy()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'Изображение успешно загружено'
        })
    
    return jsonify({'error': 'Недопустимый тип файла'}), 400

@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    return jsonify(load_gallery_data())

@app.route('/api/gallery/<int:item_id>', methods=['DELETE'])
def delete_gallery_item(item_id):
    gallery_data = load_gallery_data()
    item = next((item for item in gallery_data if item['id'] == item_id), None)
    
    if item:
        # Удаляем файл
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], item['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Удаляем из данных
        gallery_data = [item for item in gallery_data if item['id'] != item_id]
        save_gallery_data(gallery_data)
        
        # Автоматический деплой
        auto_deploy()
        
        return jsonify({'success': True, 'message': 'Изображение удалено'})
    
    return jsonify({'error': 'Изображение не найдено'}), 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    print('🚀 Сервер запущен на http://localhost:5000')
    print('📁 Загруженные файлы будут сохранены в папку:', UPLOAD_FOLDER)
    print('🖼️  Галерея доступна через API: /api/gallery')
    if AUTO_DEPLOY:
        print('🔄 Автоматический деплой на GitHub: ВКЛЮЧЕН')
    else:
        print('💡 Для автодеплоя установите: AUTO_DEPLOY=true')
    app.run(debug=True, port=5000)
