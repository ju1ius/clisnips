import os
import signal
import multiprocessing
import multiprocessing.queues
import threading
import inspect

import glib
import gobject
import gtk

from .error_dialog import ErrorDialog

gtk.gdk.threads_init()


(
    START,
    FINISH,
    ERROR,
    UPDATE,
    PULSE,
    MESSAGE,
    CANCEL
) = range(7)


class MessageQueue(multiprocessing.queues.Queue):

    def start(self):
        self.put((START,))

    def finish(self):
        self.put((FINISH,))

    def update(self, fraction):
        self.put((UPDATE, fraction))

    def pulse(self):
        self.put((PULSE,))

    def message(self, msg):
        self.put((MESSAGE, msg))

    def error(self, err):
        self.put((ERROR, err))

    def cancel(self):
        self.put((CANCEL,))


class Listener(gobject.GObject):

    __gsignals__ = {
        'start': (
            gobject.SIGNAL_RUN_LAST,
            None,
            ()
        ),
        'finish': (
            gobject.SIGNAL_RUN_LAST,
            None,
            ()
        ),
        'update': (
            gobject.SIGNAL_RUN_LAST,
            None,
            (gobject.TYPE_FLOAT,)
        ),
        'pulse': (
            gobject.SIGNAL_RUN_LAST,
            None,
            ()
        ),
        'message': (
            gobject.SIGNAL_RUN_LAST,
            None,
            (gobject.TYPE_STRING,)
        ),
        'error': (
            gobject.SIGNAL_RUN_LAST,
            None,
            (gobject.TYPE_PYOBJECT,)
        ),
        'cancel': (
            gobject.SIGNAL_RUN_LAST,
            None,
            ()
        )
    }

    def __init__(self, queue=None):
        gobject.GObject.__init__(self)
        if queue:
            self.set_queue(queue)
        self.stopevent = multiprocessing.Event()
        self.thread = threading.Thread(target=self.run, args=())

    def set_queue(self, queue):
        if not isinstance(queue, MessageQueue):
            raise RuntimeError(
                'Listener must be associated with a progress.MessageQueue'
            )
        self.queue = queue

    def emit(self, *args):
        """Ensures signals are emitted in the main thread"""
        glib.idle_add(gobject.GObject.emit, self, *args)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopevent.set()
        # allow garbage collection
        if self.queue:
            self.queue = None

    def join(self):
        self.thread.join()

    def run(self):
        while not self.stopevent.is_set():
            # Listen for results on the queue and process them accordingly
            try:
                data = self.queue.get()
            except:
                continue
            msg_t = data[0]
            if msg_t == START:
                self.emit('start')
            elif msg_t == FINISH:
                self.emit('finish')
                self.stop()
            elif msg_t == CANCEL:
                self.emit('cancel')
                self.stop()
            elif msg_t == ERROR:
                self.emit('error', data[1])
                self.stop()
            elif msg_t == UPDATE:
                self.emit('update', data[1])
            elif msg_t == MESSAGE:
                self.emit('message', data[1])


gobject.type_register(Listener)


class IndeterminateListener(Listener):

    def run(self):
        while not self.stopevent.is_set():
            # Listen for results on the queue and process them accordingly
            try:
                data = self.queue.get(True, 0.1)
            except:
                self.emit('pulse')
                continue
            msg_t = data[0]
            if msg_t == START:
                self.emit('start')
            elif msg_t == FINISH:
                self.emit('finish')
                self.stop()
            elif msg_t == CANCEL:
                self.emit('cancel')
                self.stop()
            elif msg_t == ERROR:
                self.emit('error', data[1])
                self.stop()
            elif msg_t == MESSAGE:
                self.emit('message', data[1])


class Process(multiprocessing.Process):

    def __init__(self, target, args=(), kwargs=None, queue=None):
        self.stopevent = multiprocessing.Event()
        super(Process, self).__init__(target=target, args=args, kwargs=kwargs)
        if queue:
            self.set_queue(queue)

    def set_queue(self, queue):
        if not isinstance(queue, MessageQueue):
            raise RuntimeError(
                'Process must be associated with a progress.MessageQueue'
            )
        self.queue = queue

    def stop(self):
        print("Stopping process %s" % self.pid)
        self.stopevent.set()
        # allow garbage collection
        if self.queue:
            self.queue = None

    def kill(self):
        self.stop()
        if self.is_alive():
            print('Killing process %s' % self.pid)
            try:
                os.killpg(self.pid, signal.SIGKILL)
            except OSError as err:
                os.kill(self.pid, signal.SIGKILL)

    def run(self):
        if not isinstance(self.queue, MessageQueue):
            raise RuntimeError(
                'Process must be associated with a progress.MessageQueue'
            )
        print("Starting process %s" % self.pid)
        # pass the queue object to the function object 
        self._target.message_queue = self.queue
        self.queue.start()
        self.queue.update(0.0)
        try:
            self._do_run_task()
        except KeyboardInterrupt as e:
            print("Process catched KeyboardInterrupt")
            self.queue.cancel()
        except Exception as e:
            self.queue.error(e)
        finally:
            self.queue.finish()
            self.queue.close()

    def _do_run_task(self):
        for msg in self._target(*self._args, **self._kwargs):
            if isinstance(msg, float):
                self.queue.update(msg)
            elif isinstance(msg, str):
                self.queue.message(msg)
            if self.stopevent.is_set():
                self.queue.cancel()
                print("Cancelled process %s" % self.pid)
                break


class BlockingProcess(Process):

    def _do_run_task(self):
        self._target(*self._args, **self._kwargs)


class Worker(object):

    @classmethod
    def from_job(kls, job, args=(), kwargs=None):
        queue = MessageQueue() 
        if inspect.isgeneratorfunction(job) or inspect.isgenerator(job):
            process = Process(job, args=args, kwargs=kwargs, queue=queue)
            listener = Listener(queue)
        else:
            process = BlockingProcess(job, args=args, kwargs=kwargs,
                                      queue=queue)
            listener = IndeterminateListener(queue)
        return kls(process, listener, queue)

    def __init__(self, process, listener, queue):
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


class ProgressDialog(gtk.MessageDialog):

    def __init__(self, message='', parent=None):
        super(ProgressDialog, self).__init__(
            parent=parent,
            flags=gtk.DIALOG_MODAL,
            type=gtk.MESSAGE_INFO,
            message_format=message
        )
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_APPLY)
        self.apply_btn = self.get_widget_for_response(gtk.RESPONSE_APPLY)

        self.progressbar = gtk.ProgressBar()
        self.progressbar.set_pulse_step(0.05)
        self.get_message_area().pack_end(self.progressbar, True, True, 0)

        # SIGNALS
        self.connect("destroy", self.on_close)
        self.connect("response", self.on_response)
        self.connect("close", self.on_close)

        # LOGIC
        self.worker = None
        self.show_all()

    def run(self, task, *args, **kwargs):
        self.worker = Worker.from_job(task, args, kwargs)
        # Connecting Listener
        listener = self.worker.listener
        listener.connect("update", self._on_update)
        listener.connect("pulse", self._on_pulse)
        listener.connect("finish", self._on_finish)
        listener.connect("error", self._on_error)
        #
        #gtk.gdk.threads_enter()
        self.apply_btn.set_sensitive(False)
        self.worker.start()
        response = super(ProgressDialog, self).run()
        #gtk.gdk.threads_leave()
        return response

    def _close(self):
        self.worker.stop()
        self.destroy()

    def on_response(self, widget, response_id, data=None):
        if self.worker.process.is_alive():
            return
        self._close()

    def on_close(self, widget, data=None):
        if self.worker.is_running():
            return
        self._close()

    def _on_update(self, listener, fraction):
        self.progressbar.set_fraction(fraction)

    def _on_pulse(self, listener):
        self.progressbar.pulse()

    def _on_message(self, listener, msg):
        self.progressbar.set_text(msg)

    def _on_error(self, listener, err):
        ErrorDialog().run(err)
        self._close()

    def _on_finish(self, listener):
        self.progressbar.set_fraction(1.0)
        self.progressbar.set_text("Done")
        self.apply_btn.set_sensitive(True)
