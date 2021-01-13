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

import glob
import json
import os
import re


non_stable = []
stable = []
other = []

stable_pattern = re.compile(r".*/v\d+/.*")
unstable_pattern = re.compile(r".*/v\d+[^/]+/.*")

for file in sorted(glob.glob("breaks/*.json"), reverse=True):
    with open(file, "r") as fp:
        data = json.load(fp)
    
    breaks = data["breaks"]
    sha = data["sha"]
    date = os.path.basename(file).replace(".json", "")
    files = set([b["location"]["proto_file_name"] for b in breaks])
    is_stable = False
    is_unstable = False
    is_other = False
    for proto in files:
        if stable_pattern.match(proto):
            is_stable = True
        elif unstable_pattern.match(proto):
            is_unstable = True
        else:
            is_other = True

    if is_stable:
        stable.append(data)
    
    if is_unstable:
        non_stable.append(data)

    if is_other:
        other.append(data)

print("Stable Breaks:")
for data in stable:
    print(f"{data['date']} - {data['sha']}")
    for b in data['breaks']:
        print(f"\t{b['location']['proto_file_name']}\t{b['message']}")

print("Non-Stable Breaks:")
for data in non_stable:
    print(f"{data['date']} - {data['sha']}")
    for b in data['breaks']:
        print(f"\t{b['location']['proto_file_name']}\t{b['message']}")

print("Other Breaks:")
for data in other:
    print(f"{data['date']} - {data['sha']}")
    for b in data['breaks']:
        print(f"\t{b['location']['proto_file_name']}\t{b['message']}")

