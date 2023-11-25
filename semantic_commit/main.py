import os
import sys
import argparse
import json
from subprocess import Popen, PIPE
import logging

valid_semantic_commit_types = [
    "fix",
    "feat",
    "build",
    "chore",
    "ci",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
]

logging_enabled = False


def _configure_logging():
    log_file_directory = os.path.join(
        os.path.expanduser("~"), "Library/Logs/prepare-commit-message-hook"
    )
    log_file_path = os.path.join(log_file_directory, "hooks.log")

    if os.path.exists(log_file_directory) is not True:
        os.makedirs(log_file_directory)

    logging.basicConfig(filename=log_file_path, encoding="utf-8", level=logging.DEBUG)


def _handle_logging(message, warning=False, error=False):
    if not logging_enabled:
        return

    if error:
        logging.error(message)
    elif warning:
        logging.warning(message)
    else:
        logging.debug(message)


def _log_environment_details(
    message_path: str, strictness: bool, inline_commit_message: str
):
    logging.warning(
        "Currently logging due to your pre-commit-config.yaml config. See https://github.com/SethAngell/semantic-commit-formatter for more information."
    )
    logging.debug(f"{message_path=}")
    logging.debug(f"{strictness=}")
    logging.debug(f"{inline_commit_message= }")
    logging.debug(f'{os.getenv("PRE_COMMIT_COMMIT_MSG_SOURCE")= }')
    logging.debug(f'{os.getenv("PRE_COMMIT_COMMIT_OBJECT_NAME")= }')


def _get_branch_details() -> list[str]:
    process = Popen(
        ["git", "symbolic-ref", "--short", "HEAD"], stdout=PIPE, stderr=PIPE
    )
    stdout, stderr = process.communicate()
    branch = stdout.decode(sys.stdout.encoding).strip()

    return branch.split("/")


def _generate_context_and_type(branch_parts: list[str]) -> tuple[str, str]:
    if len(branch_parts) == 1:
        branch_context = branch_parts[0]
        branch_type = None
    elif len(branch_parts) > 1:
        branch_context = branch_parts[-1]
        branch_type = branch_parts[-2].lower()
    else:
        print("Invalid branch naming convention for hook")
        sys.exit(1)

    _handle_logging(f"{branch_type=}, {branch_context=}")

    return (branch_type, branch_context)


def _generate_prefix_map() -> dict[str, str]:
    config_location = os.path.join(
        os.path.expanduser("~"), ".config/pre-commit-type-mappings.json"
    )
    if os.path.exists(config_location):
        with open(config_location, "r") as ifile:
            mappings = {key.lower(): value for key, value in json.load(ifile).items()}
        _handle_logging("Prefix mappings pulled from user config file.")
    else:
        mappings = {
            "bug": "fix",
            "pdi": "fix",
            "tech-debt": "fix",
            "story": "feat",
            "tech-task": "chore",
        }
        _handle_logging("Default prefix mappings used")

    _handle_logging(f"{mappings=}")

    return mappings


def _generate_semantic_commit_header(
    branch_type: str,
    branch_context: str,
    mappings: dict[str, str],
    strict: bool = False,
) -> str:
    potentially_semantic = branch_type in mappings
    semantic_commit_header = ""

    if branch_type in valid_semantic_commit_types:
        semantic_commit_header = f"{branch_type}({branch_context}): <description>\n"
    elif potentially_semantic:
        semantic_commit_header = (
            f"{mappings[branch_type]}({branch_context}): <description>\n"
        )
    elif strict:
        raise ValueError(
            "Error 01: Pre-commit hook has been run in strict mode without a proper branch type. See https://github.com/SethAngell/semantic-commit-formatter#01 for more information."
        )
    else:
        semantic_commit_header = f"fix({branch_context}): <description>\n"

    _handle_logging(f"{semantic_commit_header=}")
    return semantic_commit_header


def _update_commit_message_template(semantic_header: str, msg_filepath: str):
    semantic_prefix = [
        semantic_header,
        "\n# Wrap at 72 chars. ################################# which is here ->|\n",
    ]

    with open(msg_filepath, "r") as commit_message:
        semantic_prefix.append(commit_message.read())

    with open(msg_filepath, "w+") as commit_message:
        commit_message.writelines(semantic_prefix)


def _modify_commit_message_to_meet_semantic_standards(
    semantic_header: str, msg_filepath: str, strict=False
):
    header = f'{semantic_header.split(":")[0]}: '
    prefix_length = len(header)

    message = ""
    with open(msg_filepath, "r") as commit_message:
        message = commit_message.read().strip()

    if strict and prefix_length + len(message) > 72:
        raise ValueError(
            "Error 02: Pre-commit hook has been run in strict mode and generated a header longer than 72 characters. See https://github.com/SethAngell/semantic-commit-formatter#02 for more information."
        )

    new_header = f"{header}{message}"

    with open(msg_filepath, "w") as commit_message:
        commit_message.write(new_header)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("message_path", nargs=1)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    inline_commit_message = os.getenv("PRE_COMMIT_COMMIT_MSG_SOURCE", "template")

    if args.log:
        global logging_enabled
        logging_enabled = True
        _configure_logging()
        _log_environment_details(args.message_path, args.strict, inline_commit_message)

    branch_elements = _get_branch_details()
    branch_type, branch_context = _generate_context_and_type(branch_elements)
    mappings = _generate_prefix_map()
    commit_header = _generate_semantic_commit_header(
        branch_type, branch_context, mappings, args.strict
    )

    if inline_commit_message == "template":
        _update_commit_message_template(commit_header, args.message_path[0])
    else:
        _modify_commit_message_to_meet_semantic_standards(
            commit_header, args.message_path[0], args.strict
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
