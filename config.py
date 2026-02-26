import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Класс для загрузки и валидации конфигурации из .env файла."""

    def __init__(self):
        load_dotenv()
        self.sync_folder_path = self._get_env_var('SYNC_FOLDER_PATH')
        self.cloud_folder_name = self._get_env_var('CLOUD_FOLDER_NAME')
        self.yandex_token = self._get_env_var('YANDEX_TOKEN')
        self.sync_period = int(self._get_env_var('SYNC_PERIOD'))
        self.log_file_path = self._get_env_var('LOG_FILE_PATH')

        self._validate_config()

    def _get_env_var(self, var_name: str) -> str:
        """Получение переменной окружения."""
        value = os.getenv(var_name)
        if value is None:
            raise ValueError(f"Отсутствует переменная окружения: {var_name}")
        return value

    def _validate_config(self):
        """Валидация параметров конфигурации."""
        # Проверка существования синхронизируемой папки
        sync_path = Path(self.sync_folder_path)
        if not sync_path.exists():
            raise FileNotFoundError(
                f"Синхронизируемая папка не существует: {self.sync_folder_path}\n"
                f"Пожалуйста, создайте эту папку или укажите другой путь в файле .env"
            )
        if not sync_path.is_dir():
            raise NotADirectoryError(
                f"Указанный путь не является папкой: {self.sync_folder_path}\n"
                f"Пожалуйста, укажите путь к папке в файле .env"
            )

        # Проверка периода синхронизации
        if self.sync_period <= 0:
            raise ValueError(
                f"Период синхронизации должен быть положительным числом: {self.sync_period}\n"
                f"Пожалуйста, укажите корректное значение в файле .env"
            )

        # Проверка пути к файлу лога
        log_path = Path(self.log_file_path)
        log_dir = log_path.parent
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise PermissionError(
                    f"Нет прав на создание директории для лога: {log_dir}\n"
                    f"Пожалуйста, укажите другой путь в файле .env"
                )