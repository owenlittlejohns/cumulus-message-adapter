---
description: 'Instructions for building Python projects.'
applyTo: '**/*.py, **/pyproject.toml'
---

# Python Development

## Project Structure
- Follow a basic project structure with a `src` directory for code and a `tests` directory for unit and integration tests
- Documentation for the project other than the README.md should reside in a `docs` directory
- Any scripts used to manage the project, like scripts used for CI/CD builds, linting, etc should reside in the `bin` directory
- If the project has infrastructure as code deployment code for deploying the application to the cloud like terraform or k8 yaml, the code should reside in the `deploy` directory.
- The project must have a `LICENSE` file denoting the software license
- The project must have a `CHANGELOG.md` file for changelog information that follows the [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) format
- The project must have a `README.md` file that contains basic project information.
- If the project provides an interface, a `CONTRACT.md` file is required.
- The project should follow semantic versioning as defined in [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

### README.md file format
The `README.md` file must contain the following sections and information based on the code template below. Text enclosed in `<>` symbols is meant to be replaced by actual information and contains a description of the information that should replace the string and symbols.

```md
# <Application Name>

<Extended description of what the task does along with any unique use cases, corner cases, or functionality explained.>

## Usage

<Usage information for the application which may include CLI commands and examples, or links to more detailed API information for the application.>

### Configuration

<This section provides information on the configuration along with a schema for valid configuration settings, and an example of a valid configuration that is expected for the application.>

### Input

<This section provides information on the application input along with a schema for valid input values and an example of a valid input if needed for the application.>

### Output

<This section provides information on the application output. This section may include a schema for a valid output, and example of a message output, and any other example artifacts and/or descriptions related to the final products and functionality of the application.>

### Examples

<This section provides examples on how the application is used with valid inputs, outputs and configurations for the various use cases. Ideally, this section contains links to more robust examples and usages that reside in the docs folder.>

## Architecture

<This section should provide a brief description of the application architecture. Ideally, an architectural drawing should be provided if able. A mermaid diagram for the architecture that GitHub renders natively should be used. See the mermaid documentation on rendering various diagrams at https://mermaid.js.org/intro/syntax-reference.html An Architecture or C4 diagraming style should be used.>


### Internal Dependencies

<This section should describe any internal dependencies the application relies on. Examples may include a database, file or object storage, etc.>

### External Dependencies

<This section should describe any external dependencies the task relies on. Examples include external API calls to other services or an external user interaction.>

## Development and Deployment

<This section is optional and provides any specifics that are unique to developing with this application. This may include specific use cases and unit tests, test files, or development strategies. This section may also contain instructions for deploying the application. Ideally, this section should contain links to more in depth information located in the docs directory and provide a high level summary for developers here.>

## Contributing

<This section should also provide information on contributing to the project. This includes coding standards, issue creation and escalation, code contribution rules, project run rules, and other information and processes that are need to be known to actively add to the project. Ideally, this section should contain links to more in depth information located in the docs directory and provide a high level summary for contributers here.>

## About Cumulus

Cumulus is a cloud-based data ingest, archive, distribution and management prototype for NASA's future Earth science data streams.

[Cumulus Documentation](https://nasa.github.io/cumulus)
```

## Tools
- The project should use **uv** for project management
- The project should use **ruff** for formatting and linting
- The project should use **mypy** for type linting and validation
- The project should use **uv-secure** to check code security
- The project should use **pytest** for testing and **pytest-cov** for code coverage reports
- The project should use **pre-commit** to enforce coding standards for developers.
- Whenever possible, all tool configuration information should reside in the `pyproject.toml` file.

### uv
- **uv** should manage all aspects of the project including versioning and builds whenever possible.
- The `pyproject.toml` file should contain at a minimum the following information about the project.
  - Under [project]
    - name
    - version
    - description
    - readme
    - license
    - authors
    - requires-python
  - Under [project.urls]
    - homepage = A link to the projects homepage or github repository
    - documentation = A link to the projects documentation or the README.md file
    - repository = A link to the repository for cloning the repository locally.

### ruff

Ruff formatting and linting should be configured with the following rules as a beginning.

```toml
[tool.ruff.lint]
# https://docs.astral.sh/ruff/rules/
select = [
  # pycodestyle errors, ignore lints that are covered by the ruff formatter
  "E4", "E7", "E9",
  # line-too-long - the formatter doesn't always fix these
  "E501",
  # Pyflakes
  "F",
  # isort
  "I",
  # pylint
  "PL",
  # pyupgrade
  "UP",
  # bandit
  "S",
  # pep8-naming
  "N",
  # pydoclint
  "DOC",
  # pydocstyle
  "D",
]

ignore = [
  # undocumented-magic-method
  "D105",
  # blank-line-after-function
  "D202",
  # incorrect-blank-line-before-class - incompatible with D211
  "D203",
  # missing-blank-line-after-summary - false positives
  "D205",
  # multi-line-summary-second-line - incompatible with D212
  "D213",
  # error-suffix-on-exception-name
  "N818",
  # assert
  "S101",
  # start-process-with-partial-path
  "S607",
  # logging-too-many-args - false positives
  "PLE1205",
]


[tool.ruff.lint.per-file-ignores]
# Ignore missing docstring rules for non-exported python code
"**/tests/**.py" = ["D1", "PLR0913"]
```

### mypy

Mypy should be configured with the following rules as a beginning.

```toml
[tool.mypy]
check_untyped_defs = true
disallow_any_unimported = true
follow_untyped_imports = true
local_partial_types = true
strict_bytes = true
strict_equality = true
warn_redundant_casts = true
warn_unreachable = true
warn_unused_ignores = true
```

### pytest and pytest-cov

Pytest should be configured with the following rules as a beginning.

```toml
[tool.pytest]
minversion = "9.0"
addopts = [
    "--cov=<project module>",
    "--cov-report=lcov",
]
pythonpath = ["src"]
testpaths = [
    "tests",
]
```

## Best Practices
- Use the latest compatible versions of Python and third party libraries whenever possible
- Always use type hints for all functions and variables whenever possible
- Use Pydantic models or TypedDicts for structured tool inputs, outputs, and configurations whenever possible
- Keep tool functions focused on single responsibilities
- Provide clear docstrings - they become tool descriptions
- Use descriptive parameter names with type hints
- Validate inputs using Pydantic Field descriptions or valid JSON schemas
- Implement proper error handling with try-except blocks
- Use async functions for I/O-bound operations
- Clean up resources in lifespan context managers
- Log to stderr to avoid interfering with stdio transport (when using stdio)
- Use environment variables for configuration
- Test tools independently before integration
- Consider security when exposing file system or network access
- Use structured output for machine-readable data
- Provide both content and structured data for backward compatibility
- Use early returns for error conditions