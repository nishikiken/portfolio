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

# =========================================================================
# Finding Token License Synchronization API
# =========================================================================

VAULT_BIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finding_token_vault.bin')

@app.route('/api/license/vault', methods=['GET'])
def get_license_vault():
    """Serves the encrypted AES-256-GCM vault directly."""
    if os.path.exists(VAULT_BIN_PATH):
        return send_from_directory(
            os.path.dirname(VAULT_BIN_PATH),
            os.path.basename(VAULT_BIN_PATH),
            mimetype='application/octet-stream'
        )
    return jsonify({'error': 'Vault file not found'}), 404

@app.route('/api/license/activate', methods=['POST'])
def handle_license_activation():
    """Binds client HWID, re-encrypts vault, and triggers automatic Git deployment."""
    data = request.get_json(silent=True) or request.form.to_dict()
    code = data.get('code', '').strip().upper().replace('-', '').replace(' ', '')
    hwid = data.get('hwid', '').strip()
    client_name = data.get('client_name', 'Player').strip()

    if not code or not hwid:
        return jsonify({'error': 'Missing code or hwid'}), 400

    try:
        from crypto_vault import decrypt_vault, encrypt_vault
        if not os.path.exists(VAULT_BIN_PATH):
            return jsonify({'error': 'Vault not found'}), 500

        with open(VAULT_BIN_PATH, 'rb') as f:
            vault_data = decrypt_vault(f.read())

        licenses = vault_data.get('licenses', [])
        entry = next((l for l in licenses if l.get('code', '').upper().replace('-', '').replace(' ', '') == code), None)

        if not entry:
            return jsonify({'error': 'License key not found'}), 404

        if not entry.get('active', True):
            return jsonify({'error': 'License is inactive'}), 403

        # Check existing binding
        bound = entry.get('bound_hwid')
        if bound and bound.strip() and bound.strip().upper() != hwid.upper():
            return jsonify({'error': 'License already bound to another hardware ID', 'bound_hwid': bound}), 409

        # Update binding
        entry['bound_hwid'] = hwid
        entry['activated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        vault_data['updated_at'] = datetime.now().isoformat()

        # Re-encrypt vault
        new_bytes = encrypt_vault(vault_data)
        with open(VAULT_BIN_PATH, 'wb') as f:
            f.write(new_bytes)

        # Trigger auto deploy to GitHub
        auto_deploy()

        # Forward to ntfy relay so admin panel receives notification too
        try:
            import urllib.request
            payload = json.dumps({
                'code': code,
                'hwid': hwid,
                'client_name': client_name,
                'time': datetime.now().isoformat()
            }).encode('utf-8')
            for relay_url in ['https://ntfy.sh/ft_activations_nishikiken', 'https://ntfy.sh/ft_act_nishikiken_backup']:
                try:
                    req = urllib.request.Request(
                        relay_url,
                        data=payload,
                        headers={'Title': 'ft_activation', 'Priority': 'high', 'User-Agent': 'FindingToken-Server/1.1'}
                    )
                    urllib.request.urlopen(req, timeout=3.0)
                except Exception:
                    pass
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'License HWID successfully bound and saved to vault', 'hwid': hwid})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print('🚀 Сервер запущен на http://localhost:5000')
    print('📁 Загруженные файлы будут сохранены в папку:', UPLOAD_FOLDER)
    print('🖼️  Галерея доступна через API: /api/gallery')
    if AUTO_DEPLOY:
        print('🔄 Автоматический деплой на GitHub: ВКЛЮЧЕН')
    else:
        print('💡 Для автодеплоя установите: AUTO_DEPLOY=true')
    app.run(debug=True, port=5000)
