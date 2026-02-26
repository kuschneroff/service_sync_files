import os
import time
import hashlib
from pathlib import Path
from typing import Dict, Set
from datetime import datetime
from loguru import logger

from cloud_storage import YandexDiskStorage


class FileSyncService:
    """Сервис синхронизации файлов."""

    def __init__(self, config, logger):
        """
        Инициализация сервиса синхронизации.

        Args:
            config: Объект конфигурации
            logger: Объект логгера
        """
        self.config = config
        self.logger = logger
        self.sync_folder = Path(config.sync_folder_path)

        # Инициализация облачного хранилища
        self.cloud_storage = YandexDiskStorage(
            token=config.yandex_token,
            cloud_folder=config.cloud_folder_name
        )

        # Кэш локальных файлов
        self.local_files_cache = {}

        self.logger.info(f"Запуск программы синхронизации")
        self.logger.info(f"Синхронизируемая папка: {config.sync_folder_path}")

    def get_file_hash(self, file_path: Path) -> str:
        """
        Вычисление хеша файла для отслеживания изменений.

        Args:
            file_path: Путь к файлу

        Returns:
            Хеш файла или пустую строку при ошибке
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError) as e:
            self.logger.error(f"Ошибка чтения файла {file_path}: {str(e)}")
            return ""

    def scan_local_folder(self) -> Dict[str, dict]:
        """
        Сканирование локальной папки и получение информации о файлах.

        Returns:
            Словарь с информацией о локальных файлах
        """
        local_files = {}

        try:
            for item in self.sync_folder.iterdir():
                if item.is_file():
                    file_hash = self.get_file_hash(item)
                    if file_hash:  # Только успешно прочитанные файлы
                        local_files[item.name] = {
                            'name': item.name,
                            'path': item,
                            'hash': file_hash,
                            'size': item.stat().st_size,
                            'modified': item.stat().st_mtime
                        }
        except PermissionError as e:
            self.logger.error(f"Ошибка доступа к папке {self.sync_folder}: {str(e)}")

        return local_files

    def perform_initial_sync(self):
        """Выполнение первоначальной синхронизации."""
        self.logger.info("Начало первоначальной синхронизации")

        try:
            # Получаем информацию о файлах в облаке
            cloud_files = self.cloud_storage.get_info()
            local_files = self.scan_local_folder()

            # Загружаем все локальные файлы в облако
            for file_name, file_info in local_files.items():
                try:
                    self.cloud_storage.load(str(file_info['path']))
                    self.logger.info(f"Файл загружен: {file_name}")
                except Exception as e:
                    self.logger.error(f"Ошибка загрузки файла {file_name}: {str(e)}")

            # Обновляем кэш
            self.local_files_cache = local_files.copy()

            self.logger.info("Первоначальная синхронизация завершена")

        except Exception as e:
            self.logger.error(f"Ошибка при первоначальной синхронизации: {str(e)}")

    def sync_files(self):
        """Синхронизация файлов."""
        try:
            # Получаем текущее состояние
            current_local_files = self.scan_local_folder()
            cloud_files = self.cloud_storage.get_info()

            # Поиск новых и измененных файлов
            for file_name, local_info in current_local_files.items():
                cached_info = self.local_files_cache.get(file_name)

                # Новый файл
                if cached_info is None:
                    try:
                        self.cloud_storage.load(str(local_info['path']))
                        self.logger.info(f"Новый файл загружен: {file_name}")
                    except Exception as e:
                        self.logger.error(f"Ошибка загрузки нового файла {file_name}: {str(e)}")

                # Измененный файл
                elif cached_info['hash'] != local_info['hash']:
                    try:
                        self.cloud_storage.reload(str(local_info['path']))
                        self.logger.info(f"Файл обновлен: {file_name}")
                    except Exception as e:
                        self.logger.error(f"Ошибка обновления файла {file_name}: {str(e)}")

            # Поиск удаленных файлов
            for file_name in self.local_files_cache:
                if file_name not in current_local_files:
                    try:
                        self.cloud_storage.delete(file_name)
                        self.logger.info(f"Файл удален из облака: {file_name}")
                    except Exception as e:
                        self.logger.error(f"Ошибка удаления файла {file_name}: {str(e)}")

            # Обновляем кэш
            self.local_files_cache = current_local_files.copy()

        except Exception as e:
            self.logger.error(f"Ошибка при синхронизации: {str(e)}")

    def run(self):
        """Запуск сервиса синхронизации."""
        try:
            # Первоначальная синхронизация
            self.perform_initial_sync()

            # Основной цикл синхронизации
            while True:
                time.sleep(self.config.sync_period)
                self.sync_files()

        except KeyboardInterrupt:
            self.logger.info("Программа остановлена пользователем")
        except Exception as e:
            self.logger.error(f"Критическая ошибка: {str(e)}")
            raise