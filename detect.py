# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import glob
import json
import requests
import subprocess
import os

from pathlib import Path
from typing import List, Optional


class GitHub:
    def __init__(self, api_key: str):
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
    
    def list_commits(self, owner: str, repo: str, sha: Optional[str] = None):
        params = {}
        if sha:
            params = {"sha": sha}
        return self._get(f"https://api.github.com/repos/{owner}/{repo}/commits", params=params)

    
    def get_commit(self, owner: str, repo: str, sha: str):
        return self._get(f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}")


    def _get(self, url, params=None):
        resp = requests.get(url, headers=self.headers, params=params)
        return resp.json()

api_key = os.environ["API_KEY"]
starting_sha = os.environ.get("SHA")
gh = GitHub(api_key)
googleapis1 = Path("./googleapis1/")
googleapis2 = Path("./googleapis2/")
start_page = 1
end_page = 50

def glob_files(root: Path, directories: List[str]):
    list_of_lists = [glob.glob(str(root / dir / "*.proto")) for dir in directories]
    return [str(Path(item).relative_to(root)) for sublist in list_of_lists for item in sublist]


def compare_proto_files(sha: str, parent_sha: str, proto_files: List[str], commit):
    subprocess.run(["git", "checkout", sha], cwd=googleapis1, capture_output=True)
    subprocess.run(["git", "checkout", parent_sha], cwd=googleapis2, capture_output=True)

    proto_dirs = [os.path.dirname(file) for file in proto_files]
    proto_dirs = set(proto_dirs)
    original_proto_files = glob_files(googleapis2, proto_dirs)
    update_proto_files = glob_files(googleapis1, proto_dirs)

    if not original_proto_files:
        # print(f"{sha} ----> all new files - ignoring")
        return
    if not update_proto_files:
        print(f"{sha} ---> removed all protos - ignoring")
        return

    output = f"out/{sha}.json"
    subprocess.run(["touch", output], capture_output=True)
    args = [
        "proto-breaking-change-detector",
        "--original_api_definition_dirs", googleapis2,
        "--update_api_definition_dirs", googleapis1,
        "--original_proto_files", ",".join(original_proto_files),
        "--update_proto_files", ",".join(update_proto_files),
        "--output_json_path", output,
        "--human_readable_message",
    ]
    ret = subprocess.run(args, capture_output=True)
    if ret.returncode != 0:
        print("command failed")
        print(ret.stdout)
        print(ret.stderr)
        return

    with open(output, "r") as f:
        data = json.load(f)

    date = commit["commit"]["committer"]["date"]
    dateobj = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    breaks = [diff for diff in data if diff["change_type"] == "MAJOR"]
    datestr = dateobj.strftime("%Y%m%d%H%M%S")
    output_file = f"breaks/{datestr}.json"
    if breaks:
        print(f"-------------- {sha} ---------------------------------")
        print(f"found {len(breaks)} breaking changes")
        with open(output_file, "w") as f:
            output = {
                "breaks": breaks,
                "sha": sha,
                "date": date
            }
            json.dump(output, f, sort_keys=True, indent=2)

def detect_breaking_changes(sha: str, parent_sha: str):
    commit = gh.get_commit("googleapis", "googleapis", sha)
    # print(f"{sha} -> {parent_sha}")

    proto_files = [
        file["filename"] for file in commit["files"] if file["filename"].endswith(".proto")
    ]
    if not proto_files:
        return

    # print(proto_files)
    compare_proto_files(sha, parent_sha, proto_files, commit)

before = starting_sha
for page in range(start_page, end_page):
    print(f"commits before {before}")
    commits = gh.list_commits("googleapis", "googleapis", before)
    before = commits[-1]["sha"]
    for commit in commits:
        sha = commit["sha"]
        parent_sha = commit["parents"][0]["sha"]
        detect_breaking_changes(sha, parent_sha)