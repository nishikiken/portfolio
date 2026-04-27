"""
Скрипт для автоматического деплоя изображений на GitHub
Запускается после загрузки новых изображений через админ-панель
"""

import os
import subprocess
import json
from datetime import datetime

def git_auto_commit():
    """Автоматически коммитит и пушит изменения в галерее"""
    
    try:
        # Проверяем, есть ли изменения
        result = subprocess.run(
            ['git', 'status', '--porcelain'], 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if not result.stdout.strip():
            print('✓ Нет изменений для коммита')
            return False
        
        print('📝 Обнаружены изменения в галерее')
        
        # Добавляем файлы
        subprocess.run(['git', 'add', 'uploads/*'], check=True)
        subprocess.run(['git', 'add', 'gallery_data.json'], check=True)
        
        # Коммитим
        commit_message = f'🖼️ Update gallery - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Пушим
        print('🚀 Загружаем изменения на GitHub...')
        subprocess.run(['git', 'push'], check=True)
        
        print('✓ Галерея успешно обновлена на GitHub!')
        return True
        
    except subprocess.CalledProcessError as e:
        print(f'✗ Ошибка при работе с Git: {e}')
        return False
    except Exception as e:
        print(f'✗ Неожиданная ошибка: {e}')
        return False

def setup_git_credentials():
    """Настройка Git credentials для автоматического пуша"""
    print("""
    Для автоматического деплоя настройте Git:
    
    1. Создайте Personal Access Token на GitHub:
       https://github.com/settings/tokens
       
    2. Выполните команды:
       git config --global user.name "Ваше имя"
       git config --global user.email "ваш@email.com"
       
    3. При первом пуше введите токен вместо пароля
       Git запомнит его для будущих пушей
    """)

if __name__ == '__main__':
    print('=== Auto Deploy Script ===')
    git_auto_commit()
