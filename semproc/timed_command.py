import subprocess
import threading

'''
see: www.ostricher.com/2015/01/python-subprocess-with-timeout/
and: https://gist.github.com/kirpit/1306188
'''


class TimedCmd(object):
    out, err = '', ''
    status = None
    process = None
    command = None

    def __init__(self, cmd):
        self.command = cmd

    def run(self, timeout=None):
        def target():
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.out, self.err = self.process.communicate()
            self.status = self.process.returncode

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            try:
                self.process.terminate()
                thread.join()
            except OSError, e:
                return -1, '', e
            raise RuntimeError('Subprocess timed out')
        return self.status, self.out, self.err
