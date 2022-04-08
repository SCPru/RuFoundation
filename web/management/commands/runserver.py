from django.core.management.commands.runserver import Command as BaseRunserverCommand
import os
import subprocess
import atexit


_ALREADY_WATCHING = False


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
        parser.add_argument('--watch', action='store_true', dest='watch_js', help='Runs JS build in development mode')

    def handle(self, *args, **options):
        if options['watch_js']:
            self.watch_js()
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
