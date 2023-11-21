import enum
import multiprocessing
import multiprocessing.queues
import queue
import threading

import urwid

from clisnips.tui.loop import idle_add


class MessageType(enum.Enum):
    STARTED = 'started'
    FINISHED = 'finished'
    CANCELED = 'canceled'
    ERROR = 'error'
    MESSAGE = 'message'
    PROGRESS = 'progress'
    PULSE = 'pulse'


class MessageQueue(multiprocessing.queues.Queue):
    def __init__(self):
        super().__init__(0, ctx=multiprocessing)

    def start(self):
        self.put((MessageType.STARTED,))

    def finish(self):
        self.put((MessageType.FINISHED,))

    def progress(self, fraction):
        self.put((MessageType.PROGRESS, fraction))

    def pulse(self):
        self.put((MessageType.PULSE,))

    def message(self, msg):
        self.put((MessageType.MESSAGE, msg))

    def error(self, err):
        self.put((MessageType.ERROR, err))

    def cancel(self):
        self.put((MessageType.CANCELED,))


class MessageQueueListener:
    def __init__(self, message_queue: MessageQueue):
        self._message_queue = message_queue
        self._stop_event = multiprocessing.Event()
        self._thread = threading.Thread(target=self.run, args=())
        urwid.register_signal(self.__class__, list(MessageType))
        self._emitter = self

    def emit(self, signal, *args):
        """Ensures signal is emitted in main thread"""
        idle_add(lambda *x: urwid.emit_signal(self, signal, *args))

    def connect(self, signal, callback, *args):
        urwid.connect_signal(self, signal, callback, user_args=args)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        # allow garbage collection
        if self._message_queue:
            self._message_queue = None

    def join(self):
        self._thread.join()

    def run(self):
        while not self._stop_event.is_set():
            # Listen for results on the queue and process them accordingly
            try:
                data = self._poll_queue()
            except queue.Empty:
                continue
            message_type, *args = data
            self.emit(message_type, *args)
            if message_type in (MessageType.FINISHED, MessageType.CANCELED, MessageType.ERROR):
                self.stop()

    def _poll_queue(self):
        return self._message_queue.get()


class IndeterminateMessageQueueListener(MessageQueueListener):
    def _poll_queue(self):
        try:
            return self._message_queue.get(True, 0.1)
        except queue.Empty:
            return MessageType.PULSE, None
