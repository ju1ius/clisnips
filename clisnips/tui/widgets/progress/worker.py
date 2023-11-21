from inspect import isgenerator, isgeneratorfunction

from .message_queue import IndeterminateMessageQueueListener, MessageQueue, MessageQueueListener
from .process import BlockingProcess, Process


class Worker:
    @classmethod
    def from_job(cls, job, args=(), kwargs=None):
        queue = MessageQueue()
        if isgeneratorfunction(job) or isgenerator(job):
            process = Process(queue, job, args=args, kwargs=kwargs)
            listener = MessageQueueListener(queue)
        else:
            process = BlockingProcess(queue, job, args=args, kwargs=kwargs)
            listener = IndeterminateMessageQueueListener(queue)
        return cls(process, listener, queue)

    def __init__(self, process: Process, listener: MessageQueueListener, queue: MessageQueue):
        self.queue = queue
        self.listener = listener
        self.process = process
        self._destroyed = False

    def start(self):
        if self._destroyed:
            raise RuntimeError('Cannot reuse a Worker object.')
        self.listener.start()
        self.process.start()

    def stop(self):
        if self._destroyed:
            return
        if self.process.is_alive():
            self.process.stop()
            self.process.join(1)
        self.listener.stop()
        self.listener.join()
        self.queue.close()
        self.cleanup()

    def is_running(self):
        return not self._destroyed and self.process.is_alive()

    def kill(self):
        if self._destroyed:
            return
        self.process.kill()
        self.listener.stop()
        self.listener.join()
        self.queue.close()
        self.cleanup()

    def cleanup(self):
        if self.listener:
            self.listener = None
        if self.queue:
            self.queue = None
        if self.process:
            self.process = None
        self._destroyed = True

    def __del__(self):
        self.cleanup()
