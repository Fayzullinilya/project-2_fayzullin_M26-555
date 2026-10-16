#!/usr/bin/env python3
from primitive_db import engine


def main() -> None:
    print("DB project is running!")
    engine.welcome()

if __name__ == "__main__":
    main()