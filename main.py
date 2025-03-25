
from common import logger
import psutil
from uvicorn import run
from settings import settings

def kill_and_run_serviceapp(port, workers, host):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            connection_info = proc.net_connections()
            for conn in connection_info:
                if conn.laddr.port == port:
                    proc.kill()
                    print(f"Process with PID {proc.pid} killed.")
                    return
        except Exception as e:
            logger.error(e)
    logger.info(f"No process found running on port: {port}")

    run('app:app', workers=workers, host=host, port=port)



if __name__ == '__main__':
    kill_and_run_serviceapp(settings.APP_PORT, settings.APP_WORKERS, settings.APP_HOST)

