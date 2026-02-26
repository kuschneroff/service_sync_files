import os
import requests
from typing import Dict, List, Optional
from pathlib import Path


class YandexDiskStorage:
    """Класс для работы с Яндекс.Диском."""

    BASE_URL = "https://cloud-api.yandex.net/v1/disk"

    def __init__(self, token: str, cloud_folder: str):
        """
        Инициализация хранилища Яндекс.Диска.

        Args:
            token: Токен доступа к Яндекс.Диску
            cloud_folder: Путь к папке в облачном хранилище

        Raises:
            ValueError: Если токен недействителен или папка недоступна
        """
        self.token = token
        self.cloud_folder = cloud_folder
        self.headers = {
            'Authorization': f'OAuth {token}',
            'Content-Type': 'application/json'
        }

        self._validate_connection()
        self._ensure_folder_exists()

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Выполнение HTTP запроса с обработкой ошибок."""
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Нет подключения к интернету")
        except requests.exceptions.Timeout:
            raise TimeoutError("Превышен таймаут подключения к Яндекс.Диску")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError("Недействительный токен доступа к Яндекс.Диску")
            elif response.status_code == 404:
                raise FileNotFoundError(f"Ресурс не найден на Яндекс.Диске")
            else:
                raise RuntimeError(f"Ошибка HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ошибка при запросе к Яндекс.Диску: {str(e)}")

    def _validate_connection(self):
        """Проверка валидности токена и доступности API."""
        try:
            response = self._make_request('GET', f"{self.BASE_URL}")
        except Exception as e:
            raise ValueError(f"Не удалось подключиться к Яндекс.Диску: {str(e)}")

    def _ensure_folder_exists(self):
        """Создание папки в облаке, если она не существует."""
        try:
            self._make_request(
                'PUT',
                f"{self.BASE_URL}/resources",
                params={'path': self.cloud_folder}
            )
        except RuntimeError as e:
            # Если папка уже существует, игнорируем ошибку
            if "409" not in str(e):
                raise

    def load(self, file_path: str) -> bool:
        """
        Загрузка файла в облачное хранилище.

        Args:
            file_path: Путь к локальному файлу

        Returns:
            True если загрузка успешна, False в противном случае
        """
        try:
            file_name = os.path.basename(file_path)
            cloud_path = f"{self.cloud_folder}/{file_name}"

            # Получаем URL для загрузки
            response = self._make_request(
                'GET',
                f"{self.BASE_URL}/resources/upload",
                params={'path': cloud_path, 'overwrite': 'true'}
            )

            upload_url = response.json().get('href')
            if not upload_url:
                raise RuntimeError("Не удалось получить URL для загрузки")

            # Загружаем файл
            with open(file_path, 'rb') as f:
                upload_response = requests.put(upload_url, files={'file': f})
                upload_response.raise_for_status()

            return True

        except (IOError, OSError) as e:
            raise IOError(f"Ошибка чтения файла {file_path}: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки файла {file_path}: {str(e)}")

    def reload(self, file_path: str) -> bool:
        """
        Перезапись файла в облачном хранилище.

        Args:
            file_path: Путь к локальному файлу

        Returns:
            True если перезапись успешна, False в противном случае
        """
        # Для Яндекс.Диска load и reload работают одинаково с параметром overwrite=true
        return self.load(file_path)

    def delete(self, filename: str) -> bool:
        """
        Удаление файла из облачного хранилища.

        Args:
            filename: Имя файла для удаления

        Returns:
            True если удаление успешно, False в противном случае
        """
        try:
            cloud_path = f"{self.cloud_folder}/{filename}"
            self._make_request(
                'DELETE',
                f"{self.BASE_URL}/resources",
                params={'path': cloud_path, 'permanently': 'true'}
            )
            return True
        except FileNotFoundError:
            # Файл уже удален
            return True
        except Exception as e:
            raise RuntimeError(f"Ошибка удаления файла {filename}: {str(e)}")

    def get_info(self) -> Dict[str, dict]:
        """
        Получение информации о файлах в облачном хранилище.

        Returns:
            Словарь с информацией о файлах: {имя_файла: информация}
        """
        try:
            response = self._make_request(
                'GET',
                f"{self.BASE_URL}/resources",
                params={'path': self.cloud_folder, 'limit': 1000}
            )

            items = response.json().get('_embedded', {}).get('items', [])

            files_info = {}
            for item in items:
                if item['type'] == 'file':
                    files_info[item['name']] = {
                        'name': item['name'],
                        'size': item.get('size', 0),
                        'modified': item.get('modified', '')
                    }

            return files_info

        except Exception as e:
            raise RuntimeError(f"Ошибка получения информации о файлах: {str(e)}")