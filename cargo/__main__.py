"""Usage: python -m cargo onboard CLIENT_FILE MAPPING_FILE OUT_DIR   or   python -m cargo sample DATA_DIR"""
import json
import sys

from . import pipeline, sample


def main(argv):
    if len(argv) == 5 and argv[1] == "onboard":
        report = pipeline.onboard(argv[2], argv[3], argv[4])
        print(json.dumps(report, indent=2))
        return 0 if report["decision"] == "GO" else 2
    if len(argv) == 3 and argv[1] == "sample":
        planted = sample.write(argv[2])
        print(json.dumps(planted, indent=2))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
