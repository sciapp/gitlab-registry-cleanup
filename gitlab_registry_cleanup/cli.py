#!/usr/bin/env python3

import argparse
import getpass
import os
import re
import subprocess
import sys
from typing import cast, Any, Callable
from .cleanup import soft_delete_untagged_imagehashes
from .registry import DEFAULT_REGISTRY_ROOT
from ._version import __version__, __version_info__  # noqa: F401 pylint: disable=unused-import

__author__ = "Ingo Heimbach"
__email__ = "i.heimbach@fz-juelich.de"
__copyright__ = "Copyright © 2018 Forschungszentrum Jülich GmbH. All rights reserved."
__license__ = "MIT"

DEFAULT_ORDER = "name"
DEFAULT_USER = "root"


class MissingServerNameError(Exception):
    pass


class InvalidServerNameError(Exception):
    pass


class CredentialsReadError(Exception):
    pass


def has_terminal_color() -> bool:
    try:
        return os.isatty(sys.stderr.fileno()) and int(subprocess.check_output(["tput", "colors"])) >= 8
    except subprocess.CalledProcessError:
        return False


class TerminalColorCodes:
    if has_terminal_color():
        RED = "\033[31;1m"
        GREEN = "\033[32;1m"
        YELLOW = "\033[33;1m"
        BLUE = "\033[34;1m"
        PURPLE = "\033[35;1m"
        CYAN = "\033[36;1m"
        GRAY = "\033[36;1m"
        RESET = "\033[0m"
    else:
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        PURPLE = ""
        CYAN = ""
        GRAY = ""
        RESET = ""


class AttributeDict(dict):
    def __getattr__(self, attr: str) -> Any:
        return self[attr]

    def __setattr__(self, attr: str, value: Any) -> None:
        self[attr] = value


def get_argumentparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
%(prog)s is a utility for cleaning up a GitLab registry by soft deleting untagged images.
""",
    )
    parser.add_argument(
        "-g",
        "--gitlab-server",
        action="store",
        dest="gitlab_server",
        help="GitLab server hostname (for example `mygitlab.com`)",
    )
    parser.add_argument(
        "-r",
        "--registry-server",
        action="store",
        dest="registry_server",
        help="GitLab registry server hostname (for example `registry.mygitlab.com`)",
    )
    parser.add_argument(
        "-p",
        "--registry-path",
        action="store",
        dest="local_registry_root",
        default=DEFAULT_REGISTRY_ROOT,
        help="Path to the registry directory on the GitLab server (default: %(default)s)",
    )
    parser.add_argument(
        "-c",
        "--credentials-file",
        action="store",
        dest="credentials_file",
        type=cast(Callable[[str], str], os.path.abspath),
        help="path to a file containing username and password/access token (on two separate lines)",
    )
    parser.add_argument(
        "-u",
        "--user",
        action="store",
        dest="username",
        default=DEFAULT_USER,
        help="user account for querying the GitLab API (default: %(default)s)",
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true", dest="dry_run", help="only print which images would be deleted"
    )
    parser.add_argument(
        "-V", "--version", action="store_true", dest="print_version", help="print the version number and exit"
    )
    return parser


def parse_arguments() -> AttributeDict:
    parser = get_argumentparser()
    args = AttributeDict({key: value for key, value in vars(parser.parse_args()).items()})
    if not args.print_version and (args.gitlab_server is None or args.registry_server is None):
        if args.gitlab_server is None and args.registry_server is None:
            raise MissingServerNameError("Neither a GitLab server nor a registry server is given.")
        elif args.gitlab_server is None:
            raise MissingServerNameError("No GitLab server is given.")
        else:
            raise MissingServerNameError("No registry server is given.")
    if not args.print_version:
        for server in ("gitlab_server", "registry_server"):
            match_obj = re.match(r"(?:https?//)?(.+)/?", args[server])
            if match_obj:
                args[server] = match_obj.group(1)
            else:
                raise InvalidServerNameError("{} is not a valid server name.".format(server))
        if args.credentials_file is not None:
            try:
                with open(args.credentials_file, "r") as f:
                    for key in ("username", "password"):
                        args[key] = f.readline().strip()
            except IOError:
                raise CredentialsReadError("Could not read credentials file {}.".format(args.credentials_file))
        elif args.username is not None:
            args["password"] = getpass.getpass()
        else:
            raise CredentialsReadError("Could not get credentials for the GitLab web api.")

    return args


def cleanup_gitlab_registry(
    gitlab_server: str, registry_server: str, local_registry_root: str, username: str, password: str, dry_run: bool
) -> None:
    gitlab_base_url = "https://{}/".format(gitlab_server)
    registry_base_url = "https://{}/".format(registry_server)

    def console_output(repository: str, image_hash: str, successful: bool) -> None:
        if not dry_run:
            if successful:
                print(
                    "Deleted image {}{}{} in repository {}{}{}.".format(
                        TerminalColorCodes.BLUE,
                        image_hash,
                        TerminalColorCodes.RESET,
                        TerminalColorCodes.CYAN,
                        repository,
                        TerminalColorCodes.RESET,
                    )
                )
            else:
                print(
                    "Could not delete image {}{}{} in repository {}{}{}.".format(
                        TerminalColorCodes.BLUE,
                        image_hash,
                        TerminalColorCodes.RESET,
                        TerminalColorCodes.CYAN,
                        repository,
                        TerminalColorCodes.RESET,
                    )
                )
        else:
            if successful:
                print(
                    "Would delete image {}{}{} in repository {}{}{}.".format(
                        TerminalColorCodes.BLUE,
                        image_hash,
                        TerminalColorCodes.RESET,
                        TerminalColorCodes.CYAN,
                        repository,
                        TerminalColorCodes.RESET,
                    )
                )
            else:
                print(
                    "Would delete image {}{}{} in repository {}{}{} {}but without success{}.".format(
                        TerminalColorCodes.BLUE,
                        image_hash,
                        TerminalColorCodes.RESET,
                        TerminalColorCodes.CYAN,
                        repository,
                        TerminalColorCodes.RESET,
                        TerminalColorCodes.RED,
                        TerminalColorCodes.RESET,
                    )
                )

    soft_delete_untagged_imagehashes(
        gitlab_base_url,
        registry_base_url,
        username,
        password,
        local_registry_root,
        dry_run=dry_run,
        notify_callback=console_output,
    )


def main() -> None:
    args = parse_arguments()
    if args.print_version:
        print("{}, version {}".format(os.path.basename(sys.argv[0]), __version__))
    else:
        cleanup_gitlab_registry(
            args.gitlab_server,
            args.registry_server,
            args.local_registry_root,
            args.username,
            args.password,
            args.dry_run,
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
