from __future__ import annotations

import argparse
import json

from aiobserve import __version__, get_observer


def main() -> None:
    parser = argparse.ArgumentParser(prog="aiobserve", description="AI usage and cost observability")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("version", help="Show installed version")
    subparsers.add_parser("summary", help="Summarize events recorded in this process")
    args = parser.parse_args()
    if args.command == "version":
        print(__version__)
    elif args.command == "summary":
        print(json.dumps(get_observer().summary(), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
