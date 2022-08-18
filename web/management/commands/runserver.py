from django.core.management.commands.runserver import Command as BaseRunserverCommand
import os
import sys
import shutil
import subprocess
import atexit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import platform
import threading
import time
import psutil


_ALREADY_WATCHING = False
_ALREADY_WATCHING_RUST = False


def _safe_kill(p):
    try:
        p.terminate()
        p.wait(5)
    except:
        pass
    try:
        p.kill()
    except:
        pass


class Command(BaseRunserverCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--watch', action='store_true', dest='watch', help='Runs JS build in development mode')
        parser.add_argument('--no-first-reload', action='store_true', dest='no_first_reload', help='Internal parameter for FTML reloading')

    def handle(self, *args, **options):
        if options['no_first_reload']:
            time.sleep(1)
        if options['watch']:
            self.watch_js()
            self.watch_ftml(options['no_first_reload'])
        super().handle(*args, **options)

    def watch_js(self):
        global _ALREADY_WATCHING
        if _ALREADY_WATCHING or os.environ.get('RUN_MAIN') == 'true':
            return
        print('Will watch JS '+repr(self))
        base_project_dir = os.path.dirname(__file__) + '/../..'
        p = subprocess.Popen(['yarn', 'run', 'watch'], shell=True, cwd=base_project_dir+'/js')
        atexit.register(lambda: _safe_kill(p))
        _ALREADY_WATCHING = True

    def watch_ftml(self, no_first_reload=False):
        # You cannot reload a PYD file. For this reason, entire watcher will restart.
        global _ALREADY_WATCHING_RUST
        if _ALREADY_WATCHING_RUST or os.environ.get('RUN_MAIN') == 'true':
            return
        print('Will watch FTML '+repr(self))
        base_project_dir = os.path.dirname(__file__) + '/../../../ftml'

        class FtmlWatcher(FileSystemEventHandler):
            def __init__(self):
                super().__init__()
                self.lock = threading.RLock()
                self.is_updated = False
                self.thread = threading.Thread(target=self.reload)
                self.thread.daemon = True
                self.thread.start()
                if not no_first_reload:
                    self.updated(base_project_dir)

            def on_moved(self, event):
                super().on_moved(event)
                self.updated(event.dst_path)

            def on_created(self, event):
                super().on_created(event)
                self.updated(event.src_path)

            def on_deleted(self, event):
                super().on_deleted(event)
                self.updated(event.src_path)

            def on_modified(self, event):
                super().on_modified(event)
                self.updated(event.src_path)

            def filenames(self):
                if platform.system() == 'Windows':
                    filename = 'ftml.dll'
                    new_filename = 'ftml.pyd'
                else:
                    filename = 'ftml.so'
                    new_filename = filename
                return filename, new_filename

            def updated(self, filename):
                with self.lock:
                    self.is_updated = True

            def reload(self):
                while True:
                    time.sleep(1)
                    with self.lock:
                        is_updated = self.is_updated
                        self.is_updated = False
                    if not is_updated:
                        continue
                    p = subprocess.Popen(['cargo', 'build', '--release'], shell=True, cwd=base_project_dir)
                    code = p.wait()
                    if code != 0:
                        continue
                    filename, new_filename = self.filenames()
                    if os.path.exists(base_project_dir + '/target/debug/' + filename):
                        print('Copying FTML library')
                        # move FTML library to another location (on Windows this fixes permissions)
                        if os.path.exists(base_project_dir + '/' + new_filename):
                            if os.path.exists(base_project_dir + '/' + new_filename + '.old'):
                                os.remove(base_project_dir + '/' + new_filename + '.old')
                            os.rename(base_project_dir + '/' + new_filename, base_project_dir + '/' + new_filename + '.old')
                        shutil.copy(base_project_dir + '/target/debug/' + filename, base_project_dir + '/' + new_filename)
                        # reload this script
                        print('Reloading...')
                        nofr = ['--no-first-reload'] if not no_first_reload else []
                        os.execv(sys.executable, ['python'] + sys.argv + nofr)

        observer = Observer()
        observer.schedule(FtmlWatcher(), base_project_dir+'/src', recursive=True)
        observer.start()

