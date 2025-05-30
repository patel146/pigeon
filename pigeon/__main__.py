import os
import logging
import argparse
import queue

from pigeon import log, settings
from pigeon.ui import UI
from pigeon.image import Watcher
from pigeon.comms.uav import UAV

__version__ = "2.0.3"


class GroundStation:

    def __init__(self):
        super().__init__()
        self.im_queue = queue.Queue()
        self.msg_queue = queue.Queue()
        self.statustext_queue = queue.Queue()

        self.loadSettings()
        self.image_watcher = Watcher()
        device = self.settings_data.get("UAV Device")
        self.uav = UAV(device, self.im_queue, self.msg_queue,
                       self.statustext_queue)

        about_text = """Pigeon

Pigeon is UAARG's ground imaging software. It is used to monitor and control
imaging processes running on the drone.

Running in "%(run_directory)s"

Version: %(version)s

Copyright (c) 2023 UAARG
""" % {
            "version": __version__,
            "run_directory": os.getcwd()
        }

        self.ui = UI(uav=self.uav,
                     save_settings=self.saveSettings,
                     load_settings=self.loadSettings,
                     image_in_queue=self.im_queue,
                     message_in_queue=self.msg_queue,
                     statustext_in_queue=self.statustext_queue,
                     about_text=about_text)

    def loadSettings(self):
        self.settings_data = settings.load()
        return self.settings_data

    def saveSettings(self, settings_data):
        settings.save(settings_data)

    def run(self):
        if self.settings_data["Load Existing Images"]:
            pass
        self.uav.try_connect()
        self.image_watcher.start()

        self.ui.run()  # This runs until the user exits the GUI

        self.image_watcher.stop()
        self.uav.disconnect()


def get_args():
    parser = argparse.ArgumentParser(
        description=
        "pigeon ground imaging software. For analyzing and geo-referencing aerial imagery"
    )
    parser.add_argument(
        "-b",
        "--ivy-bus",
        type=str,
        default=None,
        help=
        "The subnet and port number to use when connecting to other pigeon instances through ivybus (default: '127:2010')"
    )
    parser.add_argument(
        "-ub",
        "--uav-ivy-bus",
        type=str,
        default="127:2011",
        help=
        "The subnet and port number to use when connecting to the uav through ivybus (default: '127:2011')"
    )

    args = parser.parse_args()
    args.ivy_bus = args.ivy_bus or os.environ.get("IVYBUS")
    return args


def main():
    log.initialize()
    logger = logging.getLogger("pigeon")
    logger.info('\n')
    logger.info("Started")
    logger.info("Version: %s" % __version__)

    args = get_args()
    logger.info("Arguments: %s" % args)
    ground_pigeon = GroundStation()
    ground_pigeon.run()

    logger.info("Finished")


if __name__ == "__main__":
    main()
