import signal
import sys

from django.core.management.commands.runserver import Command as BaseRunserverCommand
import os
import shutil
import subprocess
import atexit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import platform
import threading
import time


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
        parser.add_argument('--ftml-release', action='store_true', dest='ftml_release', help='Build FTML in release mode')
        parser.add_argument('--internal-run', action='store_true', dest='internal_run', help='This starts the actual server')

    def handle(self, *args, **options):
        if not options['watch'] or options['internal_run']:
            super().handle(*args, **options)
            return

        self.watch_js()
        self.watch_ftml(options['ftml_release'])

    def watch_js(self):
        global _ALREADY_WATCHING
        if _ALREADY_WATCHING or os.environ.get('RUN_MAIN') == 'true':
            return
        print('Will watch JS '+repr(self))
        base_project_dir = os.path.dirname(__file__) + '/../..'
        p = subprocess.Popen(['yarn', 'run', 'watch'], shell=True, cwd=base_project_dir+'/js')
        atexit.register(lambda: _safe_kill(p))
        _ALREADY_WATCHING = True

    # Runs this command but with --internal-run
    def run_child(self):
        return subprocess.Popen([sys.executable] + sys.argv + ['--internal-run'])

    def watch_ftml(self, ftml_release=False) -> bool:
        # You cannot reload a PYD file. For this reason, entire watcher will restart.
        global _ALREADY_WATCHING_RUST
        if _ALREADY_WATCHING_RUST or os.environ.get('RUN_MAIN') == 'true':
            return True
        print('Will watch FTML '+repr(self))
        base_project_dir = os.path.dirname(__file__) + '/../../../ftml'

        observer = Observer()

        class FtmlWatcher(FileSystemEventHandler):
            def __init__(self):
                super().__init__()
                self.lock = threading.RLock()
                self.is_updated = False
                self.child_pid = 0
                self.should_continue_normally = False
                self.updated(base_project_dir)

            def on_moved(self, event):
                super().on_moved(event)
                self.updated(event.dest_path)

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

        w = FtmlWatcher()
        observer.schedule(w, base_project_dir+'/src', recursive=True)
        observer.start()
        current_child = self.run_child()
        while observer.is_alive():
            time.sleep(1)
            with w.lock:
                is_updated = w.is_updated
                w.is_updated = False
            if not is_updated:
                continue
            rel_cmdline = ['--release'] if ftml_release else []
            p = subprocess.Popen(['cargo', 'build'] + rel_cmdline, shell=True, cwd=base_project_dir)
            code = p.wait()
            if code != 0:
                print('FTML compilation failed; skipping')
                continue
            filename, new_filename = w.filenames()
            target_dir = '/target/release/' if ftml_release else '/target/debug/'
            if os.path.exists(base_project_dir + target_dir + filename):
                # Kill child
                if current_child:
                    print('Interrupting child process...')
                    current_child.terminate()
                    current_child.wait()
                    current_child = None
                print('Copying FTML library')
                shutil.copy(base_project_dir + target_dir + filename, base_project_dir + '/' + new_filename)
                # Create another instance of runserver
                print('Reloading...')
                current_child = self.run_child()
        return w.should_continue_normally
