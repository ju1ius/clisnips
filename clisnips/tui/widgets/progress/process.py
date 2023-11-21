import logging
import multiprocessing
import os
import signal
from collections.abc import Callable
from typing import Any

from .message_queue import MessageQueue

logger = logging.getLogger(__name__)


class Process(multiprocessing.Process):
    # protected props of multiprocessing.Process
    _target: Callable
    _args: tuple[Any]
    _kwargs: dict[str, Any]

    def __init__(self, message_queue: MessageQueue, target, args=(), kwargs=None):
        super().__init__(target=target, args=args, kwargs=kwargs or {})
        self._stop_event = multiprocessing.Event()
        self._message_queue = message_queue

    def stop(self):
        logger.debug('Stopping process %s', self.pid)
        self._stop_event.set()
        # allow garbage collection
        if self._message_queue:
            self._message_queue = None
            if hasattr(self, '_target'):
                self._target.message_queue = None

    def kill(self):
        self.stop()
        if self.is_alive():
            logger.debug('Killing process %s', self.pid)
            assert self.pid, 'Cannot kill a process without a pid'
            try:
                os.killpg(self.pid, signal.SIGKILL)
            except OSError:
                os.kill(self.pid, signal.SIGKILL)

    def run(self):
        logger.debug('Starting process %s', self.pid)
        assert self._message_queue, 'Process was already stopped'
        # pass the queue object to the function object
        self._target.message_queue = self._message_queue
        self._message_queue.start()
        self._message_queue.progress(0.0)
        try:
            self._do_run_task()
        except (KeyboardInterrupt, SystemExit):
            logger.debug('Process %s catched KeyboardInterrupt', self.pid)
            self._message_queue.cancel()
        except Exception as err:
            msg = ' '.join(err.args) if len(err.args) else str(err)
            self._message_queue.error(msg)
        finally:
            self._message_queue.finish()
            self._message_queue.close()

    def _do_run_task(self):
        assert self._message_queue, 'Process was already stopped'
        for msg in self._target(*self._args, **self._kwargs):
            if isinstance(msg, float):
                self._message_queue.progress(msg)
            elif isinstance(msg, str):
                self._message_queue.message(msg)
            if self._stop_event.is_set():
                self._message_queue.cancel()
                logger.debug('Cancelled process %s', self.pid)
                break


class BlockingProcess(Process):
    def _do_run_task(self):
        self._target(*self._args, **self._kwargs)
