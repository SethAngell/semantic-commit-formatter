# Semantic Commit Formatter

A [pre-commit](https://pre-commit.com) hook for parsing git branch names and prefixing them with valid headers as per the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standards.

This hook supports commit message creation from the command line in two ways:

1. `git commit` - which will pull in a commit message template if one exists
2. `git commit -m '<message>`

`git commit -f` _should_ work, but is untested. If you use this hook _and_ use that method, let me know.

## Installation

> [!NOTE]
> If you have run `pre-commit install` but are still not seeing the hook run before every commit, try running `pre-commit install --hook-type prepare-commit-msg`

1. In order to use this pre-commit hook, you first need to install the pre-commit library. [More info here](https://pre-commit.com/#installation)

2. In the root of the project you're interested in working in, create a `.pre-commit-config.yaml` file.

3. Run `pre-commit install` to install the githook in your repository

4. Enjoy!

### Sample .pre-commit-config.yaml

```yaml
default_install_hook_types: [pre-commit, prepare-commit-msg]
repos:
  - repo: https://github.com/SethAngell/semantic-commit-formatter
    rev: v1
    hooks:
      - id: semantic_commit
        stages: [prepare-commit-msg]
```

## Configuration Options

### Prefix Mappings

There are a number of prefix types defined in the conventional commit standard. This hook comes preloaded with the following mappings:

```json
{
  "bug": "fix",
  "pdi": "fix",
  "tech-debt": "fix",
  "story": "feat",
  "tech-task": "chore"
}
```

If you'd like to configure your own mappings, you can create a json file at `~/.config/pre-commit-type-mappings.json` in the format of `<YOUR BRANCH PREFIX> : <CONVENTIONAL COMMIT TYPE>`.

### Runtime Arguments

#### Strict

If you want to really lean into the semantic commit standards, you can add the `--strict` arg to your config file. This will cause errors to be thrown when commits and branches don't adhere closely to the semantic configuration standard

### Log

If you're experiencing issues with the hook, adding the arg `--log` to your config will generate a log file with further information as to what's happening within the hook. This file is created at `~/Library/Logs/prepare-commit-message-hook/hook.log`.

## Errors

### 01

This hook expects that branch names will be written in the following format: `<branch_type>/<ticket_name>`. If you have enabled the strict setting the hook will fail if your branch does not conform to this format.

### 02

Conventional Commits are traditionally capped at a 72 character line length. If you have enabled the strict setting the hook will fail if your commit message ends up being longer than 72 characters.
