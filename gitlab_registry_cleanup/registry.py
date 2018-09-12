import os
from typing import Dict, List, Optional  # noqa: F401 pylint: disable=unused-import

DEFAULT_REGISTRY_ROOT = "/var/opt/gitlab/gitlab-rails/shared/registry"
RELATIVE_REPOSITORIES_ROOT = "docker/registry/v2/repositories"
MANIFESTS_DIRECTORY = "_manifests"
REVISIONS_DIRECTORY = "_manifests/revisions/sha256"
TAGS_DIRECTORY = "_manifests/tags"
TAG_CURRENT_DIRECTORY = "current"
LINK_FILENAME = "link"


class LocalRegistry:
    def __init__(
        self, registry_root: str = DEFAULT_REGISTRY_ROOT, relative_repositories_root: str = RELATIVE_REPOSITORIES_ROOT
    ) -> None:
        self._docker_repositories_root = os.path.join(registry_root, relative_repositories_root)
        self._repository_paths = None  # type: Optional[List[str]]
        self._repository_imagehashes = None  # type: Optional[Dict[str, List[str]]]
        self._repository_tags = None  # type: Optional[Dict[str, List[str]]]
        self._repository_tagged_imagehashes = None  # type: Optional[Dict[str, List[str]]]
        self._repository_untagged_imagehashes = None  # type: Optional[Dict[str, List[str]]]

    def _find_all_repository_paths(self) -> List[str]:
        def on_error(error: OSError) -> None:
            raise error

        repository_paths = [
            os.path.relpath(root, self._docker_repositories_root)
            for root, directories, files in os.walk(self._docker_repositories_root, onerror=on_error)
            if os.path.isdir(os.path.join(root, MANIFESTS_DIRECTORY))
        ]
        return repository_paths

    def _find_repository_imagehashes(self) -> Dict[str, List[str]]:
        repository_imagehashes = {}  # type: Dict[str, List[str]]
        for repository_path in self.repository_paths:
            imagehashes = []  # type: List[str]
            try:
                for image_hash in os.listdir(
                    os.path.join(self._docker_repositories_root, repository_path, REVISIONS_DIRECTORY)
                ):
                    try:
                        with open(
                            os.path.join(
                                self._docker_repositories_root,
                                repository_path,
                                REVISIONS_DIRECTORY,
                                image_hash,
                                LINK_FILENAME,
                            ),
                            "r",
                        ) as f:
                            image = f.readline()
                        imagehashes.append(image)
                    except OSError:
                        pass
            except OSError:
                pass
            repository_imagehashes[repository_path] = imagehashes
        return repository_imagehashes

    def _find_repository_tags(self) -> Dict[str, List[str]]:
        repository_tags = {}  # type: Dict[str, List[str]]
        for repository_path in self.repository_paths:
            try:
                tags = os.listdir(os.path.join(self._docker_repositories_root, repository_path, TAGS_DIRECTORY))
            except OSError:
                tags = []
            repository_tags[repository_path] = tags
        return repository_tags

    def _find_repository_tagged_imagehashes(self) -> Dict[str, List[str]]:
        repository_tagged_imagehashes = {}  # type: Dict[str, List[str]]
        for repository_path in self.repository_paths:
            tagged_imagehashes = []  # type: List[str]
            for tag in self.repository_tags[repository_path]:
                try:
                    with open(
                        os.path.join(
                            self._docker_repositories_root,
                            repository_path,
                            TAGS_DIRECTORY,
                            tag,
                            TAG_CURRENT_DIRECTORY,
                            LINK_FILENAME,
                        )
                    ) as f:
                        tagged_imagehash = f.readline()
                    tagged_imagehashes.append(tagged_imagehash)
                except OSError:
                    pass
            repository_tagged_imagehashes[repository_path] = tagged_imagehashes
        return repository_tagged_imagehashes

    def _find_repository_untagged_imagehashes(self) -> Dict[str, List[str]]:
        repository_untagged_imagehashes = {
            repository_path: list(
                set(self.repository_imagehashes[repository_path])
                - set(self.repository_tagged_imagehashes[repository_path])
            )
            for repository_path in self.repository_paths
        }
        return repository_untagged_imagehashes

    @property
    def repository_paths(self) -> List[str]:
        if self._repository_paths is None:
            self._repository_paths = self._find_all_repository_paths()
        return self._repository_paths

    @property
    def repository_imagehashes(self) -> Dict[str, List[str]]:
        if self._repository_imagehashes is None:
            self._repository_imagehashes = self._find_repository_imagehashes()
        return self._repository_imagehashes

    @property
    def repository_tags(self) -> Dict[str, List[str]]:
        if self._repository_tags is None:
            self._repository_tags = self._find_repository_tags()
        return self._repository_tags

    @property
    def repository_tagged_imagehashes(self) -> Dict[str, List[str]]:
        if self._repository_tagged_imagehashes is None:
            self._repository_tagged_imagehashes = self._find_repository_tagged_imagehashes()
        return self._repository_tagged_imagehashes

    @property
    def repository_untagged_imagehashes(self) -> Dict[str, List[str]]:
        if self._repository_untagged_imagehashes is None:
            self._repository_untagged_imagehashes = self._find_repository_untagged_imagehashes()
        return self._repository_untagged_imagehashes
