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

import subprocess
import os
from typing import Sequence
from google.protobuf import descriptor_pb2 as desc


class Loader:
    # This loader is a wrapper of protoc command.
    # It takes in protoc command arguments (e.g. proto files,
    # descriptor_set_out and proto directories), executes the command
    # and cleans up the generated descriptor_set file.
    # This also works as the **temporary** solution of loading FileDescriptorSet
    # from API definition files that ussers pass in from the command line.
    _CURRENT_DIR = os.getcwd()
    PROTOC_BINARY = os.path.join(_CURRENT_DIR, "test/tools/protoc")
    COMMON_PROTOS_DIR = os.path.join(_CURRENT_DIR, "api-common-protos")
    PROTOBUF_PROTOS_DIR = os.path.join(_CURRENT_DIR, "protobuf/src")
    DESCRIPTOR_SET = "generated_descriptor_set.pb"

    def __init__(
        self,
        proto_dirs: Sequence[str],
        proto_files: Sequence[str] = None,
    ):
        # Check the passing in proto directory is existing or not.
        for path in proto_dirs:
            if not os.path.isdir(path):
                raise TypeError(
                    f"The directory {path} passed in is not existing. Please check the path."
                )
        self.proto_dirs = [dir for dir in proto_dirs]
        if not proto_files:
            self.proto_files = self._get_proto_files(self.proto_dirs)
        else:
            self.proto_files = proto_files

    def get_descriptor_set(self) -> desc.FileDescriptorSet:
        # Construct the protoc command with proper argument prefix.
        protoc_command = [self.PROTOC_BINARY]
        for directory in self.proto_dirs:
            protoc_command.append(f"--proto_path={directory}")
        protoc_command.append(f"--proto_path={self.COMMON_PROTOS_DIR}")
        protoc_command.append(f"--proto_path={self.PROTOBUF_PROTOS_DIR}")
        protoc_command.append(f"-o{self.DESCRIPTOR_SET}")
        protoc_command.append("--include_source_info")
        # Include the imported dependencies.
        protoc_command.append("--include_imports")
        protoc_command.extend(pf for pf in self.proto_files)

        # Run protoc command to get pb file that contains serialized data of
        # the proto files.
        process = subprocess.run(protoc_command)
        if process.returncode != 0:
            raise _ProtocInvokerException(
                f"Protoc command to load the descriptor set fails: {protoc_command}"
            )
        # Create FileDescriptorSet from the serialized data.
        desc_set = desc.FileDescriptorSet()
        with open(self.DESCRIPTOR_SET, "rb") as f:
            desc_set.ParseFromString(f.read())
        # Clean up the generated descriptor set file.
        if os.path.exists(self.DESCRIPTOR_SET):
            os.remove(self.DESCRIPTOR_SET)
        return desc_set

    def _get_proto_files(self, proto_dirs: Sequence[str]):
        proto_files = []
        for directory in proto_dirs:
            files = os.listdir(directory)
            for file_name in files:
                if file_name.endsWith(".proto"):
                    proto_files.append(file_name)
        return proto_files


class _ProtocInvokerException(Exception):
    pass
