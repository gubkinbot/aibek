"""
Windows Service wrapper для OPC UA Realtime Service.
Обновляет текущие значения каждую секунду.

Установка:
    python opc_realtime_windows_service.py install

Запуск:
    python opc_realtime_windows_service.py start

Остановка:
    python opc_realtime_windows_service.py stop

Удаление:
    python opc_realtime_windows_service.py remove
"""

import os
import sys
import time
import logging

# Добавляем путь к скрипту
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Путь к Python из venv основного проекта CS
PYTHON_EXE = r'C:\Users\Administrator\CS\venv\Scripts\python.exe'

import win32serviceutil
import win32service
import win32event
import servicemanager

# Импортируем наш основной модуль
import opc_realtime_service


class OPCRealtimeService(win32serviceutil.ServiceFramework):
    """Windows служба для OPC Realtime"""
    
    _svc_name_ = "OPCTagReaderRealtime"
    _svc_display_name_ = "OPC UA Tag Reader Realtime Service"
    _svc_description_ = "Читает текущие значения из OPC UA и записывает в PostgreSQL каждую секунду"
    
    # Указываем путь к Python из venv
    _exe_name_ = PYTHON_EXE
    _exe_args_ = f'"{os.path.join(SCRIPT_DIR, "opc_realtime_windows_service.py")}"'
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
    
    def SvcStop(self):
        """Остановка службы"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
    
    def SvcDoRun(self):
        """Основной цикл службы"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        # Меняем рабочую директорию на папку скрипта
        os.chdir(SCRIPT_DIR)
        
        # Загружаем конфиг
        config = opc_realtime_service.load_config()
        opc_realtime_service.setup_logging(config)
        
        logger = logging.getLogger("OPCRealtime")
        logger.info("Windows служба Realtime запущена")
        
        # Загружаем теги
        tags = opc_realtime_service.load_tags_from_db(config)
        if not tags:
            logger.error("Не удалось загрузить теги")
            return
        
        realtime_config = config.get('realtime', {})
        db_config = config.get('database', {})
        
        interval = realtime_config.get('interval', 1)
        schema = db_config.get('schema', 'ohangaron')
        table = realtime_config.get('table', 'realtime_data')
        
        # Создаём подключения
        opc = opc_realtime_service.OPCConnection(config)
        db = opc_realtime_service.DBConnection(config)
        
        # Счётчики
        success_count = 0
        error_count = 0
        last_log_time = time.time()
        
        while self.running:
            loop_start = time.time()
            
            # Проверяем/восстанавливаем подключение к OPC
            if not opc.connected:
                if opc.connect():
                    opc.prepare_nodes(tags)
                else:
                    time.sleep(5)
                    continue
            
            # Проверяем/восстанавливаем подключение к БД
            if not db.is_connected():
                db.connect()
            
            # Читаем данные
            results = opc.read_all()
            
            if results:
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
        
        opc.disconnect()
        db.disconnect()
        logger.info("Windows служба Realtime остановлена")


def main():
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(OPCRealtimeService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(OPCRealtimeService)


if __name__ == "__main__":
    main()
