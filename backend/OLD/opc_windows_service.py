"""
Windows Service wrapper для OPC UA Tag Reader.
Использует библиотеку pywin32.

Установка:
    python opc_windows_service.py install

Запуск:
    python opc_windows_service.py start
    или через services.msc

Остановка:
    python opc_windows_service.py stop

Удаление:
    python opc_windows_service.py remove
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
import opc_service


class OPCReaderService(win32serviceutil.ServiceFramework):
    """Windows служба для OPC Reader"""
    
    _svc_name_ = "OPCTagReader"
    _svc_display_name_ = "OPC UA Tag Reader Service"
    _svc_description_ = "Читает данные из OPC UA и записывает в PostgreSQL"
    
    # Указываем путь к Python из venv
    _exe_name_ = PYTHON_EXE
    _exe_args_ = f'"{os.path.join(SCRIPT_DIR, "opc_windows_service.py")}"'
    
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
        config = opc_service.load_config()
        opc_service.setup_logging(config)
        
        logger = logging.getLogger("OPCReader")
        logger.info("Windows служба запущена")
        
        # Загружаем теги
        tags = opc_service.load_tags_from_db(config)
        if not tags:
            logger.error("Не удалось загрузить теги")
            return
        
        polling_config = config.get('polling', {})
        interval = polling_config.get('interval', 300)
        
        while self.running:
            try:
                opc_service.run_once(config, tags)
            except Exception as e:
                logger.error(f"Ошибка в цикле: {e}")
            
            # Ждём с проверкой на остановку
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)
        
        logger.info("Windows служба остановлена")


def main():
    if len(sys.argv) == 1:
        # Запуск без аргументов - попытка запустить как службу
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(OPCReaderService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Управление службой через командную строку
        win32serviceutil.HandleCommandLine(OPCReaderService)


if __name__ == "__main__":
    main()
