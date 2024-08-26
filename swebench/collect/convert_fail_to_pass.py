import json
from pathlib import Path
from argparse import ArgumentParser
from typing import List


def main(base_dir: Path, repo: str, input_suffix: str, output_suffix: str):
    splited_repo: List[str] = repo.split("/")
    assert len(splited_repo) == 2, f"repo should be in form of 'owner/repo', got {repo}"

    repo_dir = base_dir / repo.replace("/", "__")
    base_name = splited_repo[-1]
    input_file = repo_dir / f"{base_name}-task-instances-{input_suffix}.jsonl"
    output_file = repo_dir / f"{base_name}-task-instances-{output_suffix}.json"

    with open(input_file, "r") as f:
        lines = f.readlines()
        data = []
        for line in lines:
            d = json.loads(line)
            pkg_list = []
            for test_patch in d["test_patches"]:
                if (
                    test_patch.get("package_name") is None
                    or test_patch.get("base_name") is None
                ):
                    continue
                pkg_list.append(
                    f"{test_patch.get('module_name')}:{test_patch.get('package_name')}.{test_patch.get('base_name').split('.')[0]}"
                )
            if len(pkg_list) == 0:
                continue
            pkgs_str = '", "'.join(pkg_list)
            d["FAIL_TO_PASS"] = f'["{pkgs_str}"]'
            d["PASS_TO_PASS"] = "[]"
            d["version"] = "0.1"
            d.pop("test_patches")
            d.pop("patches")
            data.append(d)
        with open(output_file, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument(
        "--base_dir",
        "-d",
        type=Path,
        help="Base directory for storing data.",
    )
    parser.add_argument(
        "--repo",
        "-r",
        type=str,
        required=True,
        help="Repository name to fetch commits from.",
    )
    parser.add_argument(
        "--input_suffix",
        "-i",
        type=str,
        default="with_package",
        help="Input file name suffix.",
    )
    parser.add_argument(
        "--output_suffix",
        "-s",
        type=str,
        default="fail_to_pass",
        help="Output file name suffix.",
    )

    args = parser.parse_args()
    main(**vars(args))
