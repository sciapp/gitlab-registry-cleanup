# GitLab-Registry-Cleanup

## Introduction

*GitLab-Registry-Cleanup* is a Python package for finding and (soft) deleting untagged Docker images in a GitLab Docker
registry. Currently (April 2018), Docker registries only cleanup data if the removal of an image is requested explicitly
by the user. Therefore, **the registry will keep on growing** if users only push new images. **Overwriting existing tags
is not sufficient** since images could be referenced by their SHA256 hash by an external resource. This tool assumes
that untagged images are not needed any more and deletes them explicitly. It can only be used for the embedded registry
of a GitLab server.

## Installation

The latest version is available from PyPI and needs Python 3.3+:

```bash
python3 -m pip install gitlab-registry-cleanup
```

This package can only be used on a GitLab server, since it needs read access to the Docker registry files stored on
disk. The script needs root privileges, so either use the root account or the `sudo` utility. The actual deletion of
images is done via the GitLab web api to prevent any data loss.

If you use the recommended operating system for GitLab (Ubuntu Server), you can install Python 3 and `pip` with

```bash
apt install python3-pip
```

if not already installed.

## Usage

### Command Line Interface

After installing with `pip`, a `gitlab-registry-cleanup` command is available:

```
usage: gitlab-registry-cleanup [-h] [-g GITLAB_SERVER] [-r REGISTRY_SERVER]
                               [-p LOCAL_REGISTRY_ROOT] [-c CREDENTIALS_FILE]
                               [-u USERNAME] [-n] [-V]

gitlab-registry-cleanup is a utility for cleaning up a GitLab registry by soft deleting untagged images.

optional arguments:
  -h, --help            show this help message and exit
  -g GITLAB_SERVER, --gitlab-server GITLAB_SERVER
                        GitLab server hostname (for example `mygitlab.com`)
  -r REGISTRY_SERVER, --registry-server REGISTRY_SERVER
                        GitLab registry server hostname (for example
                        `registry.mygitlab.com`)
  -p LOCAL_REGISTRY_ROOT, --registry-path LOCAL_REGISTRY_ROOT
                        Path to the registry directory on the GitLab server
                        (default: /var/opt/gitlab/gitlab-
                        rails/shared/registry)
  -c CREDENTIALS_FILE, --credentials-file CREDENTIALS_FILE
                        path to a file containing username and password/access
                        token (on two separate lines)
  -u USERNAME, --user USERNAME
                        user account for querying the GitLab API (default:
                        root)
  -n, --dry-run         only print which images would be deleted
  -V, --version         print the version number and exit
```

You should specify a GitLab server hostname (`-g`), a GitLab registry server hostname (`-r`) and either a credentials
file (`-c`) or username (`-u`) and password (read from stdin).

### Final disk cleanup

`gitlab-registry-cleanup` only *soft* deletes images. As a result, images are removed but their data (the image layers)
are still stored on disk. To delete unused image layers, you must run the Docker registry garbage collector. If you have
installed the GitLab omnibus package, you can run the following commands:

```bash
sudo gitlab-ctl registry-garbage-collect
```
