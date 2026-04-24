from src.core.log import init_logging
from core.server import Server
from threading import Thread

if __name__ == "__main__":
    logger = init_logging()
    control = Server(logger)
    run_thread = Thread(target = control.run)
    run_thread.start()

