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

import unittest
from test.tools.mock_descriptors import make_field
from src.comparator.field_comparator import FieldComparator
from src.findings.finding_container import FindingContainer


class FieldComparatorTest(unittest.TestCase):
    def tearDown(self):
        FindingContainer.reset()

    def test_field_removal(self):
        field_foo = make_field("Foo")
        FieldComparator(field_foo, None).compare()
        finding = FindingContainer.getAllFindings()[0]
        self.assertEqual(finding.message, "An existing field `Foo` is removed.")
        self.assertEqual(finding.category.name, "FIELD_REMOVAL")
        self.assertEqual(finding.location.proto_file_name, "foo")

    def test_field_addition(self):
        field_foo = make_field("Foo")
        FieldComparator(None, field_foo).compare()
        finding = FindingContainer.getAllFindings()[0]
        self.assertEqual(finding.message, "A new field `Foo` is added.")
        self.assertEqual(finding.category.name, "FIELD_ADDITION")

    def test_primitive_type_change(self):
        field_int = make_field(proto_type="TYPE_INT32")
        field_string = make_field(proto_type="TYPE_STRING")
        FieldComparator(field_int, field_string).compare()
        finding = FindingContainer.getAllFindings()[0]
        self.assertEqual(
            finding.message,
            "Type of an existing field `my_field` is changed from `TYPE_INT32` to `TYPE_STRING`.",
        )
        self.assertEqual(finding.category.name, "FIELD_TYPE_CHANGE")

    def test_message_type_change(self):
        field_message = make_field(type_name=".example.v1.Enum")
        field_message_update = make_field(type_name=".example.v1beta1.EnumUpdate")
        FieldComparator(field_message, field_message_update).compare()
        finding = FindingContainer.getAllFindings()[0]
        self.assertEqual(
            finding.message,
            "Type of an existing field `my_field` is changed from `.example.v1.Enum` to `.example.v1beta1.EnumUpdate`.",
        )
        self.assertEqual(finding.category.name, "FIELD_TYPE_CHANGE")

    def test_repeated_label_change(self):
        field_repeated = make_field(repeated=True)
        field_non_repeated = make_field(repeated=False)
        FieldComparator(field_repeated, field_non_repeated).compare()
        finding = FindingContainer.getAllFindings()[0]
        self.assertEqual(
            finding.message,
            "Repeated state of an existing field `my_field` is changed from `LABEL_REPEATED` to `LABEL_OPTIONAL`.",
        )
        self.assertEqual(finding.category.name, "FIELD_REPEATED_CHANGE")

    def test_name_change(self):
        field_foo = make_field("Foo")
        field_bar = make_field("Bar")
        FieldComparator(field_foo, field_bar).compare()
        finding = FindingContainer.getAllFindings()[0]
        self.assertEqual(
            finding.message,
            "Name of an existing field is changed from `Foo` to `Bar`.",
        )
        self.assertEqual(finding.category.name, "FIELD_NAME_CHANGE")

    def test_oneof_change(self):
        field_oneof = make_field(name="Foo", oneof=True)
        field_not_oneof = make_field(name="Foo")
        FieldComparator(field_oneof, field_not_oneof).compare()
        findings = {f.message: f for f in FindingContainer.getAllFindings()}
        finding = findings["An existing field `Foo` is moved out of One-of."]
        self.assertEqual(finding.category.name, "FIELD_ONEOF_REMOVAL")


if __name__ == "__main__":
    unittest.main()
