#Сервис синхронизации файлов с Яндекс.Диском.

import sys
from config import Config
from logger_config import setup_logger
from sync_service import FileSyncService


def main():
    """Основная функция запуска приложения."""
    try:
        # Загрузка конфигурациив
        config = Config()

        # Настройка логирования
        logger = setup_logger(config.log_file_path)

        # Создание и запуск сервиса синхронизации
        sync_service = FileSyncService(config, logger)
        sync_service.run()

    except (ValueError, FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"Ошибка конфигурации: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}", file=sys.stderr)
        sys.exit(1)

print('Сервис синхронизации файлов с Яндекс.Диском запущен...')
print('Ctrl + C - прервать процесс.')
if __name__ == "__main__":
    main()