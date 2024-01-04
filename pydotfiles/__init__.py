import os
import subprocess
import getpass
import sys
import platform
import distro
import pwd
from .loader import Loader
from collections.abc import Callable


class Register:
    def __init__(self):
        """
        self.method = {
            "install": {
                "package_name": func,
                ...
            },
            "uninstall": {
                "package_name": func,
                ...
            },
            "check": {
                "package_name": func,
                ...
            },
        }
        """
        self.methods: dict[str, dict[str, Callable]] = {}
        self.platform = OS_PLATFORM

    def registe_method(self, platform: str, operate: str, package: str):
        def decorator(func):
            if platform not in ALLOW_PALTFORMS:
                print(f"Error: platform {platform} not allowed.")
                sys.exit(1)
            elif operate not in ALLOW_OPERATES:
                print(f"Error: operate {operate} not allowed.")
                sys.exit(1)
            self.methods.setdefault(operate, {}).setdefault(
                platform, {})[package] = func
            return func
        return decorator

    def get_install_methods(self):
        return self.methods.setdefault("install", {}).setdefault(self.platform, {})

    def get_check_methods(self):
        return self.methods.setdefault("check", {}).setdefault(self.platform, {})

    def get_uninstall_methods(self):
        return self.methods.setdefault("uninstall", {}).setdefault(self.platform, {})


def dpkg_check(package):
    return f"ii  {package} " in subprocess.run(["dpkg", "-l"], capture_output=True, text=True, check=True).stdout


def command_check(command):
    return run_command(["which", command], USER).returncode == 0


def get_dependencies(current_dir: str) -> list[str]:
    dependency_path = os.path.join(current_dir, "dependency")
    packages = []
    try:
        with open(dependency_path, 'r') as f:
            packages = f.read().splitlines()
    except FileNotFoundError:
        print(f"Error: file {dependency_path} not found.")
        sys.exit(1)
    return packages


def get_platform_info():
    system_name = platform.system()
    if system_name == 'Linux':
        return distro.name().lower()
    else:
        return system_name.lower()


def get_current_dir():
    return os.path.dirname(os.path.realpath(__file__))


def sudo_command(command):
    # Check if superuser privileges are present
    if os.geteuid() != 0:
        command.insert(0, "sudo")
    return command


def add_sudo_nopasswd():
    # Get the current username
    username = getpass.getuser()

    # Check if superuser privileges are present
    if os.geteuid() == 0:
        print("You already have superuser privileges, no need for sudo.")
    else:
        # Use sudo to add a file in the /etc/sudoers.d directory
        command = f"echo '{username} ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/tmp"
        if subprocess.run(command, shell=True, capture_output=True, text=True).returncode:
            raise Exception(
                "Adding the tmp file in the /etc/sudoers.d directory using sudo failed.")
        else:
            print(
                "Successfully added the tmp file in the /etc/sudoers.d directory using sudo.")


def check_sudo_nopasswd():
    # Execute the sudo -l command
    result = subprocess.run(["sudo", "-l"], capture_output=True, text=True)
    if result.returncode:
        raise Exception("sudo -l failed.")
    # Check if the output contains (ALL) NOPASSWD: ALL
    return "(ALL) NOPASSWD: ALL" in result.stdout


def remove_sudo_nopasswd():
    # sudo rm /etc/sudoers.d/tmp
    if os.path.exists("/etc/sudoers.d/tmp"):
        print("Removing the tmp file from the /etc/sudoers.d directory using sudo.")
        command = ["sudo", "rm", "/etc/sudoers.d/tmp"]
        if subprocess.run(command, capture_output=True, text=True).returncode:
            raise Exception(
                "Removing the tmp file from the /etc/sudoers.d directory using sudo failed.")
        else:
            print(
                "Successfully removed the tmp file from the /etc/sudoers.d directory using sudo.")
    else:
        print("The tmp file does not exist in the /etc/sudoers.d directory.")


def run_command(command: list[str], permision: int):
    if permision == USER:
        command = ["sudo", "-u", USER_NAME] + command
    with open(LOG_FILE, "a") as f:
        return subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, text=True, check=True)


def expanduser(path: str) -> str:
    return os.path.expanduser(path.replace("~", f"~{USER_NAME}"))


def file2set(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return {line.strip() for line in f.readlines() if line.strip() != ""}
    else:
        return set()
    

def user_has_write_permission(path: str) -> bool:
    stat_info = os.stat(path)
    # check if the file is owned by the user
    # or the user is in the group of the file
    # and the file has write permission
    if (ORIGIN_UID == stat_info.st_uid or ORIGIN_UID in os.getgroups()) and stat_info.st_mode & 0o200:
        return True
    else:
        return False


ALLOW_PALTFORMS: list[str] = ["ubuntu", "arch", "windows", "macos"]
ALLOW_OPERATES: list[str] = ["install", "uninstall", "check"]
OS_PLATFORM: str = get_platform_info()
ORIGIN_UID: int
ROOT: int = 0
USER: int = 1

with open('UID', 'r') as file:
    first_line = file.readline().strip()
    ORIGIN_UID = int(first_line)

USER_NAME: str = pwd.getpwuid(ORIGIN_UID).pw_name

LOG_FILE = '.log'
LOGGING_CONFIG: dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s,%(msecs)03d [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': LOG_FILE,
            'mode': 'a'
        }
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

