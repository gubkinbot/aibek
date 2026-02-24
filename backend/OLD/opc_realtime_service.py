"""
OPC UA Realtime Service
Читает теги из OPC UA и записывает текущие значения в PostgreSQL.
Обновляет таблицу realtime_data каждую секунду.
Держит постоянное подключение к OPC серверу.
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
logger = logging.getLogger("OPCRealtime")


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
    # Отдельный лог-файл для realtime службы
    log_file = os.path.join(SCRIPT_DIR, 'logs/opc_realtime.log')
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

class OPCConnection:
    """Класс для управления постоянным подключением к OPC"""
    
    def __init__(self, config: dict):
        self.config = config
        self.client = None
        self.connected = False
        self.nodes = []
        self.tags = []
    
    def connect(self) -> bool:
        """Подключение к OPC UA серверу"""
        opc_config = self.config.get('opc', {})
        cert_config = self.config.get('certificates', {})
        
        server_url = opc_config.get('server_url')
        cert_file = os.path.join(SCRIPT_DIR, cert_config.get('cert_file', 'certificates/client_cert.der'))
        key_file = os.path.join(SCRIPT_DIR, cert_config.get('key_file', 'certificates/client_key.pem'))
        
        # Проверяем сертификаты
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            logger.error("Сертификаты не найдены")
            return False
        
        logger.info(f"Подключение к {server_url}...")
        
        try:
            self.client = Client(server_url)
            self.client.connect_timeout = opc_config.get('connect_timeout', 10000)
            self.client.session_timeout = opc_config.get('session_timeout', 30000)
            
            self.client.set_security(
                security_policies.SecurityPolicyBasic128Rsa15,
                cert_file,
                key_file,
                None,
                ua.MessageSecurityMode.Sign
            )
            
            self.client.application_uri = "urn:opcua:client"
            self.client.connect()
            
            self.connected = True
            logger.info("Подключено к OPC серверу")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка подключения к OPC: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Отключение от OPC сервера"""
        if self.client and self.connected:
            try:
                self.client.disconnect()
                logger.info("Отключено от OPC сервера")
            except Exception as e:
                logger.warning(f"Ошибка при отключении: {e}")
            finally:
                self.connected = False
    
    def prepare_nodes(self, tags: list):
        """Подготовка узлов для чтения (один раз)"""
        self.tags = tags
        self.nodes = []
        for tag_path in tags:
            node_id = f"ns=2;s={tag_path}"
            node = self.client.get_node(node_id)
            self.nodes.append(node)
        logger.info(f"Подготовлено {len(self.nodes)} узлов")
    
    def read_all(self) -> list:
        """Быстрое чтение всех подготовленных тегов"""
        if not self.connected or not self.nodes:
            return []
        
        results = []
        
        try:
            # Пакетное чтение
            data_values = self.client.uaclient.get_attributes(
                [node.nodeid for node in self.nodes],
                ua.AttributeIds.Value
            )
            
            for tag_path, dv in zip(self.tags, data_values):
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
        
        except Exception as e:
            logger.error(f"Ошибка чтения тегов: {e}")
            self.connected = False  # Помечаем для переподключения
        
        return results


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


# ============== БАЗА ДАННЫХ ==============

class DBConnection:
    """Класс для управления подключением к БД"""
    
    def __init__(self, config: dict):
        self.config = config
        self.conn = None
    
    def connect(self) -> bool:
        """Подключение к PostgreSQL"""
        db_config = self.config.get('database', {})
        
        try:
            self.conn = psycopg2.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 5432),
                database=db_config.get('name'),
                user=db_config.get('user'),
                password=db_config.get('password')
            )
            self.conn.autocommit = False
            logger.info("Подключено к БД")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            return False
    
    def disconnect(self):
        """Отключение от БД"""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
    
    def is_connected(self) -> bool:
        """Проверка соединения"""
        if not self.conn:
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            return False
    
    def update_realtime(self, results: list, schema: str, table: str) -> bool:
        """Обновление таблицы realtime (TRUNCATE + INSERT)"""
        if not results or not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # TRUNCATE быстрее DELETE для полной очистки
            cursor.execute(f"TRUNCATE TABLE {schema}.{table}")
            
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
            self.conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка записи в БД: {e}")
            try:
                self.conn.rollback()
            except:
                pass
            return False


# ============== ОСНОВНОЙ ЦИКЛ ==============

def run_realtime_service(config: dict):
    """Запуск realtime службы"""
    realtime_config = config.get('realtime', {})
    db_config = config.get('database', {})
    
    interval = realtime_config.get('interval', 1)
    schema = db_config.get('schema', 'ohangaron')
    table = realtime_config.get('table', 'realtime_data')
    
    logger.info(f"Запуск realtime службы с интервалом {interval} сек")
    logger.info(f"Таблица: {schema}.{table}")
    
    # Загружаем теги
    tags = load_tags_from_db(config)
    if not tags:
        logger.error("Не удалось загрузить теги")
        return
    
    # Создаём подключения
    opc = OPCConnection(config)
    db = DBConnection(config)
    
    # Счётчики для логирования
    success_count = 0
    error_count = 0
    last_log_time = time.time()
    
    try:
        while True:
            loop_start = time.time()
            
            # Проверяем/восстанавливаем подключение к OPC
            if not opc.connected:
                if opc.connect():
                    opc.prepare_nodes(tags)
                else:
                    time.sleep(5)  # Ждём перед повторной попыткой
                    continue
            
            # Проверяем/восстанавливаем подключение к БД
            if not db.is_connected():
                db.connect()
            
            # Читаем данные
            results = opc.read_all()
            
            if results:
                # Записываем в БД
                if db.update_realtime(results, schema, table):
                    success_count += 1
                else:
                    error_count += 1
            
            # Логируем статистику каждые 60 секунд
            if time.time() - last_log_time >= 60:
                logger.info(f"Статистика за минуту: {success_count} успешно, {error_count} ошибок")
                success_count = 0
                error_count = 0
                last_log_time = time.time()
            
            # Ждём до следующего цикла
            elapsed = time.time() - loop_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    
    finally:
        opc.disconnect()
        db.disconnect()
        logger.info("Realtime служба остановлена")


# ============== MAIN ==============

def main():
    # Загружаем конфиг
    config = load_config()
    
    # Настраиваем логирование
    setup_logging(config)
    
    logger.info("=" * 50)
    logger.info("OPC UA Realtime Service")
    logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Запускаем службу
    run_realtime_service(config)


if __name__ == "__main__":
    main()
