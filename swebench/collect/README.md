# Introduction

Our **collect** section is based on the [SWE-bench](https://github.com/princeton-nlp/SWE-bench) collect module, with several modifications:

1. **More accurate base commit identification**: We discovered that the collect module in SWE-bench occasionally identifies incorrect base commits, causing issues when applying patches to pull requests. To address this, we introduced `commits_scraper.py` to accurately identify the correct base commit. In the future, we may revise the collect module code to retrieve the correct base commit directly.

2. **Script for extracting Java test classes**: To correctly run specific tests in Java, we need to extract test class information. Therefore, we added `parse_mvn.py` to extract Java test class details.

# Usage

## Retrieve Pull Request Information

```bash
export GITHUB_TOKENS="token1,token2,...,tokenN"

python get_tasks_pipeline.py \
    --repos '<repo1>', '<repo2>', ..., <repoM> \
    --path_prs '<path to folder to save PRs to>' \
    --path_tasks '<path to folder to save tasks to>'
```

This command fetches pull request information from specified repositories and saves it to a designated folder. It generates three files:
    - `<repo>-prs.jsonl` file containing the [metadata for every pull request](https://docs.github.com/rest/reference/pulls#list-pull-requests) from the repository.
    - `<repo>-task-instances.jsonl.all` file containing all *valid* task instances (has associated issues + gold patch).
        * This file's values can be used for fine tuning purposes.
    - `<repo>-task-instances.jsonl` file containing *valid* task instances that also has associated *tests*.
        * This file's values are candidate task instances. Once validated, they can be used for evaluation purposes.
        * The `.json.all` includes these task instances as well.


## Retrieve Base Commit

```bash
python commits_scraper.py \
    --base_dir '<path to folder of the saved data>' \
    --repo '<repo>'
```

This command retrieves the base commit information for each pull request based on the `<repo>` folder within `base_dir` (formatted as `owner/repo`) and saves it to the `<repo>-commits.jsonl` file, which contains the base commit information for each pull request.

## Extract Information

```bash
python parse_mvn.py -r "$repo" --output_suffix with_package

python convert_fail_to_pass.py -r "$repo"
```

These commands generate two files: 
    - `<repo>-task-instances-with_package.jsonl` file containing the names of packages that need testing for each pull request.
    - `<repo>-task-instances-fail_to_pass.json` file containing all necessary information for testing.
