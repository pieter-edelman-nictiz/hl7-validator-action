#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET
from optparse import OptionParser

levels = {
    "error": 0,
    "warning": 1,
    "information": 2
}

class Result:
    def __init__(self, file_path):
        self.file_path = file_path

        self.issues = []

    def addIssue(self, line, col, severity, text):
        if severity not in ["error", "warning", "information"]:
            raise Exception(f"Unknown severity '{severity}' when validating file {self.file_path}")
        self.issues.append({
            "line": line,
            "col": col,
            "severity": severity,
            "text": text
        })

if __name__ == "__main__":
    parser = OptionParser("usage: %prog [options] validator_result.xml")
    parser.add_option("-l", "--allow-level", type = "int", default = 1,
        help="The level from which issues are considered not fatal (0 = error, 1 = warning, 2 = information). If issues below the specified level occur, this script will exit with a non-zero status.")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("Exactly one argument expected")

    tree = ET.parse(args[0])
    ns = {"f": "http://hl7.org/fhir"}

    results = []
    if tree.getroot().tag == "{http://hl7.org/fhir}OperationOutcome":
        outcomes = [tree.getroot()]
    else:
        outcomes = tree.getroot().findall(".//f:OperationOutcome", ns)
    for outcome in outcomes:
        file_name = outcome.find("f:extension[@url='http://hl7.org/fhir/StructureDefinition/operationoutcome-file']/f:valueString", ns).attrib["value"]
        result = Result(file_name)

        for issue in outcome.findall("f:issue", ns):
            line     = issue.find("f:extension[@url='http://hl7.org/fhir/StructureDefinition/operationoutcome-issue-line']/f:valueInteger", ns).attrib["value"]
            col      = issue.find("f:extension[@url='http://hl7.org/fhir/StructureDefinition/operationoutcome-issue-col']/f:valueInteger", ns).attrib["value"]
            severity = issue.find("f:severity", ns).attrib["value"]
            text     = issue.find("f:details/f:text", ns).attrib["value"]
            result.addIssue(line, col, severity, text)
        results.append(result)

    success = True
    for result in results:
        if len(result.issues) > 0:
            print(f"== {result.file_path}")
            for issue in result.issues:
                if levels[issue["severity"]] < options["allow-level"]:
                    success = False
                print(f"  -  {issue['severity']} ({issue['line']}, {issue['col']}):")
                print(f"     {issue['text']}")
            print()

    if not success:
        print("There were errors during validation")
        sys.exit(1)
    print("All well")
