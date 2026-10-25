#!/usr/bin/env python3
from primitive_db import engine


def main() -> None:
    engine.print_help()
    engine.run()

if __name__ == "__main__":
    main()