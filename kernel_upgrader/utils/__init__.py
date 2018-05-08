from datetime import datetime
from threading import Thread, enumerate

from kernel_upgrader.utils.Singleton import Singleton
from kernel_upgrader.utils.colors import *
from kernel_upgrader.utils.anim import *
from kernel_upgrader.utils.Singleton import *


def getHomeDir():
    # type: () -> str
    return "/home/kernel_upgrader"


def getLinuxVersion():
    # type: () -> str
    import subprocess
    from kernel_upgrader.values.Constants import UNAME

    command_execution = subprocess.run(UNAME.split(), stdout=subprocess.PIPE)
    return command_execution.stdout.decode("utf-8")


def getCPUCount():
    # type: () -> int
    from psutil import cpu_count
    return cpu_count()


def returnToHomeDir():
    import os
    os.chdir(getHomeDir())


def isDEBSystem():
    # type: () -> bool
    import subprocess
    from kernel_upgrader.values.Constants import RPM_OR_DEB

    try:
        process = subprocess.Popen(RPM_OR_DEB.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
        return_code = process.returncode
        if return_code != 0:
            return True
        else:
            return False
    except FileNotFoundError:
        return True


def removeOldKernels():
    import subprocess
    from kernel_upgrader.values.Constants import CLEAN_KERNELS

    subprocess.run(CLEAN_KERNELS.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)


def cleanupOldLogs():
    from kernel_upgrader.values.Constants import FILE_PATH, FILENAME, COMPILER_FILENAME, TARFILE_FILENAME,\
        TARFILE_COMPILER_FILENAME
    import tarfile
    import os

    kernel_log_filename = FILE_PATH + FILENAME
    compiler_log_filename = FILE_PATH + COMPILER_FILENAME

    tar_log_filename = FILE_PATH + TARFILE_FILENAME
    tar_compiler_log_filename = FILE_PATH + TARFILE_COMPILER_FILENAME

    if os.path.exists(kernel_log_filename):
        if os.path.exists(tar_log_filename):
            os.remove(tar_log_filename)
        with tarfile.open(tar_log_filename, "w:gz") as tar:
            tar.add(kernel_log_filename, arcname=os.path.basename(kernel_log_filename))
            tar.close()
            os.remove(kernel_log_filename)
    if os.path.exists(compiler_log_filename):
        if os.path.exists(tar_compiler_log_filename):
            os.remove(tar_compiler_log_filename)
        with tarfile.open(tar_compiler_log_filename, "w:gz") as tar:
            tar.add(compiler_log_filename, arcname=os.path.basename(compiler_log_filename))
            tar.close()
            os.remove(compiler_log_filename)


def isRunningLinux():
    import platform
    return platform.system() == "Linux"


def isUserAdmin():
    import os
    # type: () -> bool
    try:
        return os.getuid() == 0
    except AttributeError:
        return False


def getFreeSpaceAvailable():
    # type: () -> float
    import os
    home_dir = getHomeDir()
    if not os.path.exists(home_dir):
        os.makedirs(home_dir)
    st = os.statvfs(home_dir)
    return "%.2f" % (st.f_bavail * st.f_frsize / 1024 / 1024 / 1024)


def isRunningInBackground():
    # type: () -> bool
    import os
    import sys

    try:
        if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()):
            return False
        else:
            return True
    except OSError:
        return True


def cleanupSpace():
    import subprocess
    from kernel_upgrader.values.Constants import CLEAN_DOWNLOADS
    from kernel_upgrader.utils.colors import OutputColors as Colors

    command = CLEAN_DOWNLOADS.format(getHomeDir() + "/*")
    clean_process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    clean_process.communicate()
    return_code = clean_process.returncode
    if return_code != 0:
        log = Log.instance()
        log.e("There was an error while trying to clean data in \"" + getHomeDir() + "\"")
        raise RuntimeError(Colors.FAIL + "We were not able to clean data in \"" + getHomeDir() + "\". Please, clean it"
                                                                                                 " up manually"
                           + Colors.ENDC)


@Singleton
class Log:
    def __init__(self):
        import os
        from kernel_upgrader.values.Constants import FILE_PATH, FILENAME
        cleanupOldLogs()
        if not os.path.exists(FILE_PATH):
            os.makedirs(FILE_PATH)
        self.__fileLog = open(FILE_PATH + FILENAME, "w")

    def d(self, message=None):
        thread = Thread(target=self.__write, args=("DEBUG", message,))
        thread.start()

    def i(self, message=None):
        thread = Thread(target=self.__write, args=("INFO", message,))
        thread.start()

    def e(self, message=None):
        thread = Thread(target=self.__write, args=("ERROR", message,))
        thread.start()

    def w(self, message=None):
        thread = Thread(target=self.__write, args=("WARNING", message,))
        thread.start()

    def __write(self, typo=None, message=None):
        log_date = datetime.now().strftime("%H:%M:%S@%d/%m/%Y [" + typo + "]: ")
        self.__fileLog.write(log_date + message + "\n")
        self.__fileLog.flush()

    def finish(self):
        current_threads = enumerate()
        if len(current_threads) != 1:
            for active_thread in current_threads:
                try:
                    active_thread.join()
                except RuntimeError:
                    continue
        self.__fileLog.close()


class CompilerLog:
    def __init__(self):
        from kernel_upgrader.values.Constants import FILE_PATH, COMPILER_FILENAME
        self.__fileLog = open(FILE_PATH + COMPILER_FILENAME, "w")

    def add(self, message):
        thread = Thread(target=self.__write, args=(message,))
        thread.start()

    def __write(self, message):
        log_date = datetime.now().strftime("%H:%M:%S@%d/%m/%Y [COMPILER]: ")
        self.__fileLog.write(log_date + message + "\n")
        self.__fileLog.flush()

    def finish(self):
        current_threads = enumerate()
        if len(current_threads) != 1:
            for active_thread in current_threads:
                try:
                    active_thread.join()
                except RuntimeError:
                    continue
        self.__fileLog.close()