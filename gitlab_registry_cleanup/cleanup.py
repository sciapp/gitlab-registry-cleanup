from .registry import LocalRegistry, DEFAULT_REGISTRY_ROOT
from gitlab_registry_usage import GitLabRegistry, AuthTokenError, ImageDeleteError
from typing import Callable, Optional


def soft_delete_untagged_imagehashes(
    gitlab_url: str,
    registry_url: str,
    admin_username: str,
    admin_auth_token: str,
    local_registry_root: str = DEFAULT_REGISTRY_ROOT,
    dry_run: bool = False,
    notify_callback: Optional[Callable[[str, str, bool], None]] = None
) -> None:
    local_registry = LocalRegistry(local_registry_root)
    gitlab_registry = GitLabRegistry(gitlab_url, registry_url, admin_username, admin_auth_token)
    repositories = sorted(local_registry.repository_paths)
    for repository in repositories:
        untagged_imagehashes = local_registry.repository_untagged_imagehashes[repository]
        for untagged_imagehash in untagged_imagehashes:
            try:
                if not dry_run:
                    gitlab_registry.delete_image(repository, untagged_imagehash)
                successful = True
            except (AuthTokenError, ImageDeleteError):
                successful = False
            if notify_callback is not None:
                notify_callback(repository, untagged_imagehash, successful)
