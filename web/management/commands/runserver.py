import signal
import sys

import psutil
from django.core.management.commands.runserver import Command as BaseRunserverCommand
import os
import shutil
import subprocess
import atexit

from django.core.servers.basehttp import WSGIServer, WSGIRequestHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import platform
import threading
import time


_ALREADY_WATCHING = False
_ALREADY_WATCHING_SYSTEM = False
_ALREADY_WATCHING_RUST = False

_SHELL = platform.system() == "Windows"


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


class WSGIRequestHandlerWithRawURL(WSGIRequestHandler):
    def get_environ(self):
        env_base = super().get_environ()
        env_base['RAW_PATH'] = self.path
        return env_base


class WSGIServerWithRawURL(WSGIServer):
    def __init__(self, address, _handler, **kwargs):
        super().__init__(address, WSGIRequestHandlerWithRawURL, **kwargs)


class Command(BaseRunserverCommand):
    server_cls = WSGIServerWithRawURL

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
        self.watch_system()
        self.watch_ftml(options['ftml_release'])

    def watch_js(self):
        global _ALREADY_WATCHING
        if _ALREADY_WATCHING or os.environ.get('RUN_MAIN') == 'true':
            return
        print('Will watch JS '+repr(self))
        base_project_dir = os.path.dirname(__file__) + '/../..'
        p = subprocess.Popen(['yarn', 'run', 'watch'], shell=_SHELL, cwd=base_project_dir+'/js')
        atexit.register(lambda: _safe_kill(p))
        _ALREADY_WATCHING = True

    def watch_system(self):
        global _ALREADY_WATCHING_SYSTEM
        if _ALREADY_WATCHING_SYSTEM or os.environ.get('RUN_MAIN') == 'true':
            return
        print('Will watch System JS ' + repr(self))
        base_project_dir = os.path.dirname(__file__) + '/../../../system'
        p = subprocess.Popen(['yarn', 'run', 'watch'], shell=_SHELL, cwd=base_project_dir + '/js')
        atexit.register(lambda: _safe_kill(p))
        _ALREADY_WATCHING_SYSTEM = True

    # Runs this command but with --internal-run
    def run_child(self, second=False):
        add_args = ['--skip-checks']
        # with shell=False it does NOT interrupt as intended
        c = subprocess.Popen([sys.executable] + sys.argv + ['--internal-run', '--noreload'] + add_args, shell=_SHELL)
        return c

    def watch_ftml(self, ftml_release=False):
        # You cannot reload a PYD file. For this reason, entire watcher will restart.
        global _ALREADY_WATCHING_RUST
        if _ALREADY_WATCHING_RUST or os.environ.get('RUN_MAIN') == 'true':
            return True
        print('Will watch FTML '+repr(self))
        base_project_dir = './ftml'

        observer = Observer()

        class FtmlWatcher(FileSystemEventHandler):
            def __init__(self):
                super().__init__()
                self.lock = threading.RLock()
                self.is_updated = False
                self.updated_rust = False
                self.should_continue_normally = False
                self.updated(base_project_dir + '/src')

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
                    filename = ('ftml.dll',)
                    new_filename = 'ftml.pyd'
                else:
                    filename = ('ftml.so', 'libftml.so', 'libftml.dylib')
                    new_filename = filename[0]
                return filename, new_filename

            def updated(self, filename):
                filename = filename.replace('\\', '/')
                # filename must start with ./
                if filename.endswith('.py') or filename.startswith(base_project_dir + '/src/') or filename == base_project_dir + '/src':
                    with self.lock:
                        self.is_updated = True
                        self.updated_rust = not filename.endswith('.py')

        w = FtmlWatcher()
        observer.schedule(w, '.', recursive=True)
        observer.start()
        current_child = self.run_child()
        while observer.is_alive():
            time.sleep(0.25)
            s = current_child.poll()
            if s is not None:
                print('Child process died with status %d' % s)
                return
            with w.lock:
                is_updated = w.is_updated
                updated_rust = w.updated_rust
                w.is_updated = False
            if not is_updated:
                continue
            if not updated_rust:
                # This branch means we just have .py updates; restart child, don't do anything else
                print('Interrupting child process...')
                parent = psutil.Process(current_child.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                _safe_kill(current_child)
                print('Reloading...')
                current_child = self.run_child(True)
            else:
                rel_cmdline = ['--release'] if ftml_release else []
                p = subprocess.Popen(['cargo', 'build'] + rel_cmdline, cwd=base_project_dir)
                code = p.wait()
                if code != 0:
                    print('FTML compilation failed; skipping')
                    continue
                filename, new_filename = w.filenames()
                target_dir = '/target/release/' if ftml_release else '/target/debug/'
                for file in filename:
                    if os.path.exists(base_project_dir + target_dir + file):
                        # Kill child
                        if current_child:
                            print('Interrupting child process...')
                            # KILL everything in the child tree
                            # Otherwise we have hanging processes that prevent us from copying into PYD/so
                            parent = psutil.Process(current_child.pid)
                            for child in parent.children(recursive=True):
                                child.kill()
                            _safe_kill(current_child)
                        print('Copying FTML library')
                        copied = False
                        for i in range(30):
                            try:
                                shutil.copy(base_project_dir + target_dir + file, base_project_dir + '/' + new_filename)
                                copied = True
                                break
                            except PermissionError:
                                print('Could not replace FTML library, retrying...')
                            time.sleep(1)
                        if not copied:
                            print('Fatal: could not unlock FTML dynamic library, reloading is not possible. Is this the only instance running?')
                            return
                        # Create another instance of runserver
                        print('Reloading...')
                        current_child = self.run_child(True)
                        break
