"""
A parser for the top level command line tool.

"""


import argparse

def parse_args():
    parser = argparse.ArgumentParser(prog="pyesm")
    subparsers = parser.add_subparsers(help="sub-command help")

    # Create a parser for downloading
    parser_downloader = subparsers.add_parser("downloader", help="Downloads Fortran or C code for ESM Components")
    parser_downloader.add_argument("name", type=str, help="Name of the ESM Component you want to download")

    return parser.parse_args()

def main():
    args = parse_args()
    print(args)

if __name__ == "__main__":
    main()
