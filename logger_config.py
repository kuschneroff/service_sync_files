import sys
from loguru import logger


def setup_logger(log_file_path: str):
    """
    Настройка логгера.

    Args:
        log_file_path: Путь к файлу лога
    """
    # Удаляем стандартный обработчик
    logger.remove()

    # Добавляем обработчик для файла
    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="1 month"
    )

    # Добавляем обработчик для консоли (только ошибки)
    logger.add(
        sys.stderr,
        format="<level>{level}: {message}</level>",
        level="ERROR"
    )

    return logger