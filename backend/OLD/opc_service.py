"""
OPC UA Tag Reader Service
Читает теги из OPC UA и записывает в PostgreSQL.
Может работать как Windows служба.
"""

import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone, timedelta

import yaml
import psycopg2
from psycopg2.extras import execute_values
from opcua import Client, ua
from opcua.crypto import security_policies

# ============== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==============

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.yaml")
TASHKENT_TZ = timezone(timedelta(hours=5))

# Логгер
logger = logging.getLogger("OPCReader")


# ============== КОНФИГУРАЦИЯ ==============

def load_config() -> dict:
    """Загрузка конфигурации из YAML"""
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"Файл конфигурации не найден: {CONFIG_FILE}")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def setup_logging(config: dict):
    """Настройка логирования"""
    log_config = config.get('logging', {})
    log_file = os.path.join(SCRIPT_DIR, log_config.get('file', 'logs/opc_reader.log'))
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    max_size = log_config.get('max_size_mb', 10) * 1024 * 1024
    backup_count = log_config.get('backup_count', 5)
    
    # Создаём папку для логов
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Файловый хендлер с ротацией
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Настраиваем логгер
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# ============== РАБОТА С ТЕГАМИ ==============

def load_tags_from_db(config: dict) -> list:
    """Загрузка списка тегов из PostgreSQL"""
    db_config = config.get('database', {})
    try:
        conn = psycopg2.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            dbname=db_config.get('name', 'CS'),
            user=db_config.get('user', 'postgres'),
            password=db_config.get('password', '')
        )
        cur = conn.cursor()
        schema = db_config.get('schema', 'ohangaron')
        cur.execute(f"SELECT fullname FROM {schema}.tags ORDER BY fullname")
        tags = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        logger.info(f"Загружено {len(tags)} тегов из БД")
        return tags
    except Exception as e:
        logger.error(f"Ошибка при загрузке тегов из БД: {e}")
        return []


# ============== OPC UA ==============

def connect_opc(config: dict) -> Client:
    """Подключение к OPC UA серверу"""
    opc_config = config.get('opc', {})
    cert_config = config.get('certificates', {})
    
    server_url = opc_config.get('server_url')
    cert_file = os.path.join(SCRIPT_DIR, cert_config.get('cert_file', 'certificates/client_cert.der'))
    key_file = os.path.join(SCRIPT_DIR, cert_config.get('key_file', 'certificates/client_key.pem'))
    
    # Проверяем сертификаты
    if not os.path.exists(cert_file):
        logger.error(f"Сертификат не найден: {cert_file}")
        return None
    if not os.path.exists(key_file):
        logger.error(f"Ключ не найден: {key_file}")
        return None
    
    logger.info(f"Подключение к {server_url}...")
    
    try:
        client = Client(server_url)
        client.connect_timeout = opc_config.get('connect_timeout', 10000)
        client.session_timeout = opc_config.get('session_timeout', 30000)
        
        client.set_security(
            security_policies.SecurityPolicyBasic128Rsa15,
            cert_file,
            key_file,
            None,
            ua.MessageSecurityMode.Sign
        )
        
        client.application_uri = "urn:opcua:client"
        client.connect()
        
        logger.info("Подключено к OPC серверу")
        return client
    
    except ConnectionRefusedError:
        logger.error(f"OPC сервер отклонил соединение: {server_url}")
        return None
    except Exception as e:
        logger.error(f"Ошибка подключения к OPC: {e}")
        return None


def disconnect_opc(client: Client):
    """Отключение от OPC сервера"""
    if client:
        try:
            client.disconnect()
            logger.info("Отключено от OPC сервера")
        except Exception as e:
            logger.warning(f"Ошибка при отключении: {e}")


def to_tashkent_time(utc_dt) -> datetime:
    """Конвертация UTC времени в время Ташкента"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(TASHKENT_TZ)


def to_float(value) -> float:
    """Приведение значения к float"""
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def read_all_tags(client: Client, tags: list) -> list:
    """Пакетное чтение всех тегов"""
    results = []
    
    # Формируем список узлов
    nodes = []
    for tag_path in tags:
        node_id = f"ns=2;s={tag_path}"
        node = client.get_node(node_id)
        nodes.append(node)
    
    try:
        # Пакетное чтение
        data_values = client.uaclient.get_attributes(
            [node.nodeid for node in nodes],
            ua.AttributeIds.Value
        )
        
        for tag_path, dv in zip(tags, data_values):
            if dv.StatusCode.is_good():
                raw_value = dv.Value.Value if dv.Value else None
                value = to_float(raw_value)
                health = True
            else:
                value = None
                health = False
            
            source_ts = to_tashkent_time(dv.SourceTimestamp)
            
            results.append({
                'datetime': source_ts,
                'point': tag_path,
                'value': value,
                'health': health
            })
        
        logger.info(f"Прочитано {len(results)} тегов")
        
    except Exception as e:
        logger.error(f"Ошибка чтения тегов: {e}")
    
    return results


# ============== БАЗА ДАННЫХ ==============

def get_db_connection(config: dict):
    """Подключение к PostgreSQL"""
    db_config = config.get('database', {})
    
    try:
        conn = psycopg2.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            database=db_config.get('name'),
            user=db_config.get('user'),
            password=db_config.get('password')
        )
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return None


def save_to_database(config: dict, results: list) -> bool:
    """Сохранение результатов в PostgreSQL"""
    if not results:
        logger.warning("Нет данных для сохранения")
        return False
    
    db_config = config.get('database', {})
    schema = db_config.get('schema', 'ohangaron')
    table = db_config.get('table', 'raw_data')
    
    conn = get_db_connection(config)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Подготавливаем данные
        data = [
            (r['datetime'], r['point'], r['value'], r['health'])
            for r in results
            if r['datetime'] is not None
        ]
        
        # Массовая вставка
        query = f"""
            INSERT INTO {schema}.{table} (datetime, point, value, health)
            VALUES %s
        """
        
        execute_values(cursor, query, data)
        conn.commit()
        
        logger.info(f"Сохранено {len(data)} записей в БД")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка записи в БД: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


# ============== ОСНОВНОЙ ЦИКЛ ==============

def run_once(config: dict, tags: list) -> bool:
    """Один цикл опроса"""
    logger.info("=" * 50)
    logger.info("Начало цикла опроса")
    
    # Подключаемся к OPC
    client = connect_opc(config)
    if not client:
        logger.warning("Пропуск цикла - OPC недоступен")
        return False
    
    try:
        # Читаем теги
        results = read_all_tags(client, tags)
        
        if results:
            # Сохраняем в БД
            save_to_database(config, results)
        
        return True
        
    finally:
        disconnect_opc(client)


def run_service(config: dict):
    """Запуск в режиме службы (бесконечный цикл)"""
    polling_config = config.get('polling', {})
    interval = polling_config.get('interval', 300)
    
    logger.info(f"Запуск службы с интервалом {interval} секунд")
    
    # Загружаем теги один раз
    tags = load_tags_from_db(config)
    if not tags:
        logger.error("Не удалось загрузить теги. Остановка.")
        return
    
    while True:
        try:
            run_once(config, tags)
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
            break
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
        
        # Ждём до следующего цикла
        logger.info(f"Ожидание {interval} секунд до следующего опроса...")
        time.sleep(interval)
    
    logger.info("Служба остановлена")


# ============== MAIN ==============

def main():
    # Загружаем конфиг
    config = load_config()
    
    # Настраиваем логирование
    setup_logging(config)
    
    logger.info("=" * 50)
    logger.info("OPC UA Tag Reader Service")
    logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверяем аргументы
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Однократный запуск
        tags = load_tags_from_db(config)
        if tags:
            run_once(config, tags)
    else:
        # Режим службы
        run_service(config)


if __name__ == "__main__":
    main()
