"""
This module provides functions for converting kroki diagrams file to Kroki URLs in markdown.
"""

import argparse
import base64
import zlib
from typing import Any

from termcolor import colored

# Kroki API Docs URL: https://docs.kroki.io/kroki/setup/usage/

korki_url_format = "https://kroki.io/{type}/{format}/{data}"

markdown_format = "![{file_name}]({url})\n"

diagram_types = {
    ".mmd": "mermaid",
}

kroki_output_formats = ["svg"]


def parse() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Convert kroki diagrams file to Kroki URLs in markdown"
    )
    parser.add_argument(
        "--input",
        "-i",
        help="input file-name of kroki diagram files",
        action="append",
        required=True,
    )
    parser.add_argument(
        "--format",
        "-f",
        help="format to convert to",
        choices=kroki_output_formats,
        default="svg",
        required=False,
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        help="to return only what needs to be updated without updating the file",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="increase verbosity of the output",
        required=False,
    )
    parser.add_argument(
        "--silent",
        "-s",
        action="store_true",
        help="silence the console log(s) output",
        required=False,
    )
    parser.add_argument(
        "output",
        help="output file-name of the markdown file to be updated",
    )
    return parser.parse_args()


def convert(file_names: list[str], format: str, verbosity: int) -> dict[str, str]:
    """
    Convert a list of kroki diagram files to a dictionary of Kroki URLs.

    Args:
        file_names (list[str]): The list of input file names of the kroki diagram files.
        format (str): The format to convert to.
        verbosity (int): The verbosity level.

    Returns:
        dict[str, str]: A dictionary containing the file names as keys and the corresponding Kroki URLs as values.
    """
    replacements = dict()
    warnings = 0
    if verbosity >= 1:
        print(colored("Calculating conversions", "blue"))
    for file_name in file_names:
        fname = file_name.split("/")[-1]
        ftype = "." + fname.split(".")[-1]
        if ftype in diagram_types:
            replacements[fname] = convert_file(
                file_name, diagram_types[ftype], format, verbosity
            )
        else:
            warnings += 1
            if verbosity >= 1:
                msg = f"\tSkipping {file_name} as it is not a supported diagram file"
            else:
                msg = f"Skipping {file_name} as it is not a supported diagram file"
            print(
                colored(
                    msg,
                    "yellow",
                )
            )
    if verbosity >= 1 and warnings == 0:
        print(colored("Conversion completed", "green"))
        print()
    elif verbosity >= 1 and warnings > 0:
        print(colored("Conversion completed with warnings", "yellow"))
        print()
    elif warnings > 0:
        print()
    return replacements


def convert_file(file_name: str, ftype: str, format: str, verbosity: int) -> str:
    """
    Convert a kroki diagram file to a Kroki URL.

    Args:
        file_name (str): The input file name of the kroki diagram file.
        format (str): The format to convert to.
        verbosity (int): The verbosity level.

    Returns:
        str: The generated Kroki URL.
    """
    with open(file_name, "r") as f:
        data = f.read()
        encoded = base64.urlsafe_b64encode(
            zlib.compress(data.encode("utf-8"), 9)
        ).decode("ascii")
        if verbosity >= 2:
            print(colored(f"\tProcessed file: {file_name}", "green"))
        return korki_url_format.format(type=ftype, format=format, data=encoded)


def update_markdown_file(
    file_name: str, replacements: dict[str, str], dry_run: bool, verbosity: int
) -> None:
    """
    Update a markdown file with the Kroki URLs.

    Args:
        file_name (str): The input file name of the markdown file.
        replacements (dict[str, str]): The dictionary containing the file names as keys and the
            corresponding Kroki URLs as values.
        dry_run (bool): Whether to update the file or not.
        verbosity (int): The verbosity level.
    """
    final = list[str]()
    if verbosity >= 1:
        print(colored(f"Finding Update Points in {file_name}:", "blue"))
    with open(file_name, "r") as f:
        data = f.readlines()
    for index, line in enumerate(data):
        req = check_line(line, index, replacements, verbosity)
        print(req)
        final.append(req)
    if verbosity >= 1:
        print(colored(f"Found {len(replacements)} Update Points", "blue"))
        print()
    if not dry_run:
        if verbosity >= 1:
            print(colored(f"Updating {file_name}", "blue"))
        with open(file_name, "w") as f:
            f.writelines(final)
        if verbosity >= 1:
            print(colored(f"Updated {file_name}", "green"))
            print()
    else:
        print(
            colored(
                "This was a dry run.\n\tPlease run the same command without '-d' flag",
                "yellow",
            )
        )
        print()
    pass


def check_line(
    line: str, index: int, replacements: dict[str, str], verbosity: int
) -> str:
    """
    Check a line in the markdown file and replace the image file names with corresponding Kroki URLs.

    Args:
        line (str): The line to check.
        index (int): The index of the line.
        replacements (dict[str, str]): The dictionary containing the file names as keys and the
            corresponding Kroki URLs as values.
        verbosity (int): The verbosity level.

    Returns:
        str: The modified line with replaced image file names.
    """
    for key, value in replacements.items():
        if "![" + key + "]" in line:
            # print("Found ", key)
            req = markdown_format.format(file_name=key, url=value)
            if verbosity >= 2:
                print(colored(f"@Line {index+1}:", "blue"))
            if verbosity >= 3:
                print(colored(f"-- {line}", "red"))
                print(colored(f"++ {req}", "green"))
            break
        else:
            req = line
    return req


def print_configuration(dictargs: dict[str, Any]) -> None:
    """
    Print the configuration settings.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
    print(colored("Configuration Selected:", "blue"))
    print(colored("\tInput File(s):", "blue"))
    for index, value in enumerate(dictargs["input"]):
        print(colored(f"\t\t{index}: {value}", "blue"))
    print(colored(f"\tOutput File: {dictargs['output']}", "blue"))
    print(colored(f"\tFormat: {dictargs['format']}", "blue"))
    print(colored(f"\tDry Run: {dictargs['dry_run']}", "blue"))
    print(colored(f"\tVerbose: {dictargs['verbose']}", "blue"))
    print(colored(f"\tSilent: {dictargs['silent']}", "blue"))
    print()
    pass


def main() -> None:
    """
    Entry point of the program.
    """
    dictargs = vars(parse())
    if dictargs["silent"]:
        verbosity = -1
    elif dictargs["verbose"] == 0:
        verbosity = 1
    else:
        verbosity = dictargs["verbose"]
    if verbosity >= 1:
        print_configuration(dictargs)
    replacements = convert(dictargs["input"], dictargs["format"], verbosity)
    update_markdown_file(
        dictargs["output"], replacements, dictargs["dry_run"], verbosity
    )
    pass


if __name__ == "__main__":
    main()
