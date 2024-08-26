import os
import re
import json
from typing import Dict, List
from tqdm import tqdm
from pathlib import Path
import subprocess
from unidiff import PatchSet, PatchedFile
from pydantic import BaseModel
from argparse import ArgumentParser


class Patch(BaseModel):
    diff: str
    source_file: str
    target_file: str
    is_rename: bool
    is_added_file: bool
    is_removed_file: bool
    is_modified_file: bool
    package_name: str = None

    @property
    def is_java(self):
        return self.source_file.endswith(".java") or self.target_file.endswith(".java")

    @property
    def path(self) -> str:
        if self.is_rename:
            assert self.source_file.startswith(
                "a/"
            ), f"renamed patch source_file({self.source_file}) does not start with 'a/'"
            assert self.target_file.startswith(
                "b/"
            ), f"renamed patch target_file({self.target_file}) does not start with 'b/'"
            assert (
                self.source_file[2:] != self.target_file[2:]
            ), f"renamed patch source_file({self.source_file}) and target_file({self.target_file}) are same"

            return self.target_file[2:]

        elif self.is_added_file:
            return self.target_file[2:]

        elif self.is_removed_file:
            assert self.source_file.startswith(
                "a/"
            ), f"removed patch source_file({self.source_file}) does not start with 'a/'"

            return self.source_file[2:]

        elif self.is_modified_file:
            assert self.source_file.startswith(
                "a/"
            ), f"modified patch source_file({self.source_file}) does not start with 'a/'"
            assert self.target_file.startswith(
                "b/"
            ), f"modified patch target_file({self.target_file}) does not start with 'b/'"
            assert (
                self.source_file[2:] == self.target_file[2:]
            ), f"modified patch source_file({self.source_file}) and target_file({self.target_file}) are different"

            return self.source_file[2:]

        else:
            raise ValueError("unknown patch type")

    def patch_dump(self):
        return {
            "diff": self.diff,
            "file_path": self.path,
        }

    def test_patch_dump(self):
        if not self.is_java:
            return self.patch_dump()

        file_path = self.path

        assert self.package_name is not None, f"package_name is None, patch: {self}"

        return {
            "diff": self.diff,
            "file_path": file_path,
            "module_name": file_path.split("/")[0],
            "base_name": file_path.split("/")[-1],
            "package_name": self.package_name,
        }


class Commit(BaseModel):
    sha: str
    parents_sha: List[str]


class CommitsUrl(BaseModel):
    pull_number: int
    url: str
    commits: List[Commit] = []
    base_commit: str | List[str] = None


def get_commits_urls(file_path: Path) -> List[CommitsUrl]:
    commits_urls: List[CommitsUrl] = []

    with file_path.open("r") as f:
        for line in f:
            if line.strip() == "":
                continue
            data = json.loads(line)
            commits_url = CommitsUrl.model_validate(data)
            commits_urls.append(commits_url)

    return commits_urls


def get_package_name(file_content):
    package_pattern = re.compile(
        r"^[\s\+]*package\s+([a-zA-Z_][a-zA-Z0-9_\.]*);", re.MULTILINE
    )
    match = package_pattern.search(file_content)
    if match:
        return match.group(1)
    return None


def get_current_branch():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def read_file_from_commit(repo_path, commit_hash, file_path):
    original_path = os.getcwd()
    os.chdir(repo_path)

    try:
        current_branch = get_current_branch()

        subprocess.run(
            ["git", "checkout", commit_hash], capture_output=True, text=True, check=True
        )

        with open(file_path, "r") as file:
            content = file.read()

    except subprocess.CalledProcessError as e:
        return ""
        # raise ValueError(f"An error occurred while running git command({repo_path}: {commit_hash}): {e}")
    except FileNotFoundError:
        return ""
        # raise ValueError(f"The file {file_path} does not exist in the specified commit({repo_path}: {commit_hash}).")
    finally:
        subprocess.run(
            ["git", "checkout", current_branch],
            capture_output=True,
            text=True,
            check=True,
        )

        os.chdir(original_path)

    return content


def parse_mvn(all_commit_urls: Dict[int, CommitsUrl], data, repos_dir: Path):
    repo_name = data["repo"].split("/")[-1]
    repo_path = repos_dir / repo_name

    commit_urls = all_commit_urls[data["pull_number"]]
    if not isinstance(commit_urls.base_commit, str):
        # raise ValueError(f"base_commit is not a string, got {commit_urls}")
        return None
    data["base_commit"] = commit_urls.base_commit
    commit_hash = data["base_commit"]

    test_patches: List[Patch] = data["test_patches"]
    for patch in test_patches:
        if not patch.is_java:
            continue

        if patch.is_rename:
            package_name = get_package_name(str(patch.diff))
            if package_name:
                patch.package_name = package_name
            else:
                assert patch.source_file.startswith(
                    "a/"
                ), f"renamed patch source_file({patch.source_file}) does not start with 'a/'"
                assert patch.target_file.startswith(
                    "b/"
                ), f"renamed patch target_file({patch.target_file}) does not start with 'b/'"
                assert (
                    patch.source_file[2:] != patch.target_file[2:]
                ), f"renamed patch source_file({patch.source_file}) and target_file({patch.target_file}) are same"

                file_path = patch.source_file[2:]
                content = read_file_from_commit(repo_path, commit_hash, file_path)
                if content == "":
                    return None
                package_name = get_package_name(content)
                if package_name is None:
                    return None
                assert (
                    package_name is not None
                ), f"renamed patch package_name is None, patch: {patch.diff}"

                patch.package_name = package_name

        elif patch.is_added_file:
            package_name = get_package_name(str(patch.diff))
            if package_name:
                patch.package_name = package_name
            else:
                assert patch.target_file.startswith(
                    "b/"
                ), f"modified patch target_file({patch.target_file}) does not start with 'b/'"

                file_path = patch.target_file[2:]
                content = read_file_from_commit(repo_path, commit_hash, file_path)
                if content == "":
                    return None
                package_name = get_package_name(content)
                if package_name is None:
                    return None
                assert (
                    package_name is not None
                ), f"added patch package_name is None, patch: {patch.diff}"

                patch.package_name = package_name

        elif patch.is_removed_file:
            assert patch.source_file.startswith(
                "a/"
            ), f"removed patch source_file({patch.source_file}) does not start with 'a/'"

            file_path = patch.source_file[2:]
            content = read_file_from_commit(repo_path, commit_hash, file_path)
            if content == "":
                return None
            package_name = get_package_name(content)
            if package_name is None:
                return None
            assert (
                package_name is not None
            ), f"removed patch package_name is None, patch: {patch.diff}"

            patch.package_name = package_name

        elif patch.is_modified_file:
            package_name = get_package_name(str(patch.diff))
            if package_name:
                patch.package_name = package_name
            else:
                assert patch.source_file.startswith(
                    "a/"
                ), f"modified patch source_file({patch.source_file}) does not start with 'a/'"
                assert patch.target_file.startswith(
                    "b/"
                ), f"modified patch target_file({patch.target_file}) does not start with 'b/'"
                assert (
                    patch.source_file[2:] == patch.target_file[2:]
                ), f"modified patch source_file({patch.source_file}) and target_file({patch.target_file}) are different"

                file_path = patch.source_file[2:]
                content = read_file_from_commit(repo_path, commit_hash, file_path)
                if content == "":
                    return None
                package_name = get_package_name(content)
                if package_name is None:
                    return None
                assert (
                    package_name is not None
                ), f"modified patch package_name is None, patch: {patch.diff}"

                patch.package_name = package_name

        else:
            raise ValueError("unknown patch type")

    return data


def split_patch(patch: str):
    patches = PatchSet(patch)

    patches = [
        Patch(
            diff=str(patch),
            source_file=patch.source_file,
            target_file=patch.target_file,
            is_rename=patch.is_rename,
            is_added_file=patch.is_added_file,
            is_removed_file=patch.is_removed_file,
            is_modified_file=patch.is_modified_file,
        )
        for patch in patches
    ]

    return patches


# def main(input_file_path: str, output_file_path: str, repos_dir: Path):
def main(
    base_dir: Path, repos_dir: Path, repo: str, output_dir: Path, output_suffix: str
):
    splited_repo: List[str] = repo.split("/")
    assert len(splited_repo) == 2, f"repo should be in form of 'owner/repo', got {repo}"

    repo_dir = base_dir / repo.replace("/", "__")
    base_name = splited_repo[-1]
    input_file_path = repo_dir / f"{base_name}-task-instances.jsonl"
    output_file_path = (
        output_dir
        / repo.replace("/", "__")
        / f"{base_name}-task-instances-{output_suffix}.jsonl"
    )
    commits_jsonl = repo_dir / f"{base_name}-commits.jsonl"

    all_commit_urls = get_commits_urls(commits_jsonl)
    all_commit_urls = {commit.pull_number: commit for commit in all_commit_urls}

    with open(input_file_path, "r", encoding="utf-8") as infile, open(
        output_file_path, "w", encoding="utf-8"
    ) as outfile:
        for line in tqdm(infile, desc="Processing"):
            data = json.loads(line.strip())

            patch = data["patch"]
            test_patch = data["test_patch"]

            if patch == "" or test_patch == "":
                raise ValueError("patch or test_patch is empty")

            patches = split_patch(patch)
            test_patches = split_patch(test_patch)

            data["patches"] = patches
            data["test_patches"] = test_patches

            data = parse_mvn(all_commit_urls, data, repos_dir)

            if data == None:
                continue

            data["patches"] = [patch.patch_dump() for patch in data["patches"]]
            data["test_patches"] = [
                patch.test_patch_dump() for patch in data["test_patches"]
            ]
            data["instance_id"] = data["instance_id"].lower()
            data["repo"] = data["repo"].lower()

            outfile.write(json.dumps(data, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument(
        "--base_dir",
        "-d",
        type=Path,
        help="Base directory for storing data.",
    )
    parser.add_argument(
        "--repos_dir",
        type=Path,
        help="Directory for storing repositories.",
    )
    parser.add_argument(
        "--repo",
        "-r",
        type=str,
        required=True,
        help="Repository name to fetch commits from.",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=Path,
        help="Output directory for output file.",
    )
    parser.add_argument(
        "--output_suffix",
        "-s",
        type=str,
        default="with_package",
        help="Output file name suffix.",
    )

    args = parser.parse_args()
    main(**vars(args))
