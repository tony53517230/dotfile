from .config import appList, register, run_command, ROOT, logger

operate = 'install'


def install_func_factory(app):
    @register.registe_method('ubuntu', operate, app)
    def ubuntu_install():
        logger.info(f"Installing {app}...")
        command = ["apt-get", "install", "-y", app]
        run_command(command, ROOT)


for app in appList:
    install_func_factory(app)
