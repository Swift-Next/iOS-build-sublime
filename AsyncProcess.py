import os
import subprocess
import sys
import threading
import codecs
import time
import signal

class AsyncProcess:
    """
    Encapsulates subprocess.Popen, forwarding stdout to a supplied
    ProcessListener (on a separate thread)
    """

    def __init__(self, cmd, shell_cmd, env, listener, path="", shell=False, cwd="~"):
        """ "path" and "shell" are options in build systems """

        if not shell_cmd and not cmd:
            raise ValueError("shell_cmd or cmd is required")

        if shell_cmd and not isinstance(shell_cmd, str):
            raise ValueError("shell_cmd must be a string")

        self.listener = listener
        self.killed = False

        self.start_time = time.time()

        # Hide the console window on Windows
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            # Set temporary PATH to locate executable in cmd
            if path:
                old_path = os.environ["PATH"]
                # The user decides in the build system whether he wants to append
                # $PATH or tuck it at the front: "$PATH;C:\\new\\path",
                # "C:\\new\\path;$PATH"
                os.environ["PATH"] = os.path.expandvars(path)

            proc_env = os.environ.copy()
            proc_env.update(env)
            for k, v in proc_env.items():
                proc_env[k] = os.path.expandvars(v)

            if sys.platform == "win32":
                preexec_fn = None
            else:
                preexec_fn = os.setsid

            if shell_cmd:
                if sys.platform == "win32":
                    # Use shell=True on Windows, so shell_cmd is passed through
                    # with the correct escaping
                    cmd = shell_cmd
                    shell = True
                elif sys.platform == "darwin":
                    # Use a login shell on OSX, otherwise the users expected env
                    # vars won't be setup
                    cmd = ["/usr/bin/env", "bash", "-l", "-c", shell_cmd]
                    shell = False
                elif sys.platform == "linux":
                    # Explicitly use /bin/bash on Linux, to keep Linux and OSX as
                    # similar as possible. A login shell is explicitly not used for
                    # linux, as it's not required
                    cmd = ["/usr/bin/env", "bash", "-c", shell_cmd]
                    shell = False

            self.proc = subprocess.Popen(
                cmd,
                bufsize=0,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                startupinfo=startupinfo,
                env=proc_env,
                preexec_fn=preexec_fn,
                shell=shell,
                cwd=cwd)

        finally:
            # Make sure this is always run, otherwise we're leaving the PATH set
            # permanently
            if path:
                os.environ["PATH"] = old_path

        self.stdout_thread = threading.Thread(
            target=self.read_fileno,
            args=(self.proc.stdout, True)
        )

    def start(self):
        self.stdout_thread.start()

    def kill(self):
        if not self.killed:
            self.killed = True
            if sys.platform == "win32":
                # terminate would not kill process opened by the shell cmd.exe,
                # it will only kill cmd.exe leaving the child running
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen(
                    "taskkill /PID %d /T /F" % self.proc.pid,
                    startupinfo=startupinfo)
            else:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.terminate()

    def poll(self):
        return self.proc.poll() is None

    def exit_code(self):
        return self.proc.poll()

    def read_fileno(self, file, execute_finished):
        decoder = \
            codecs.getincrementaldecoder(self.listener.encoding)('replace')

        while True:
            data = decoder.decode(file.read(2**16))
            data = data.replace('\r\n', '\n').replace('\r', '\n')

            if len(data) > 0 and not self.killed:
                self.listener.on_data(self, data)
            else:
                if execute_finished:
                    self.listener.on_finished(self)
                break