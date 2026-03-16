#!/usr/bin/env python
"""Cumulus Message Adapter CLI entry point."""

import json
import signal
import sys

from message_adapter.message_adapter import MessageAdapter


def call_message_adapter_function(function_name, all_input):
    """Handle a single CMA function call and return the result.

    Parameters
    ----------
    function_name : str
        CMA function to run (one of loadAndUpdateRemoteEvent, loadNestedEvent,
        and createNextEvent).
    all_input : dict
        Dict object representing a parsed cumulus message.

    Returns
    -------
    result:
        JSON response to pass to the next event.

    """
    if "schemas" in all_input:
        schemas = all_input["schemas"]
    else:
        schemas = None
    transformer = MessageAdapter(schemas)
    event = all_input["event"]
    context = all_input.get("context")
    result = None
    if function_name == "loadAndUpdateRemoteEvent":
        result = transformer.load_and_update_remote_event(event, context)
    elif function_name == "loadNestedEvent":
        result = transformer.load_nested_event(event)
    elif function_name == "createNextEvent":
        handler_response = all_input["handler_response"]
        if "message_config" in all_input:
            message_config = all_input["message_config"]
        else:
            message_config = None
        result = transformer.create_next_event(handler_response, event, message_config)
    else:
        raise ValueError(f"Unknown function name {function_name}")
    return result


def handle_exit():
    """Flush stderr/stdout and exit with code 1."""
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(1)


def stream_commands():
    """Read and execute CMA commands from STDIN in streaming mode.

    Reads messages on STDIN in the format:

    FunctionName
    JSON string
    <EOC>

    Writes responses back to STDOUT in the following format:

    JSON string
    <EOC>

    A single line "<EXIT>" input will cause the program to exit.
    """
    cont = True
    buffer = ""
    command = ""
    json_obj = {}

    while cont:
        next_line = sys.stdin.readline().rstrip("\n")
        if next_line == "<EXIT>":
            cont = False
        elif next_line == "<EOC>":
            json_obj = json.loads(buffer)
            result = call_message_adapter_function(command, json_obj)
            sys.stdout.write(json.dumps(result) + "\n")
            sys.stdout.write("<EOC>\n")
            sys.stdout.flush()
            buffer = ""
            command = ""
        elif not command:
            command = next_line.strip()
            sys.stderr.write(f"warning setting command to {command}\n")
        else:
            buffer += next_line


def single_command(function_name):
    """Execute a single CMA command."""
    all_input = json.loads(input())
    return call_message_adapter_function(function_name, all_input)


def cma_cli():
    """Run the CMA CLI, dispatching to stream or single command mode."""
    exit_code = 1
    function_name = sys.argv[1]
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    try:
        if function_name == "stream":
            stream_commands()
            exit_code = 0
        else:
            result = single_command(function_name)
            if result is not None and len(result) > 0:
                sys.stdout.write(json.dumps(result))
                sys.stdout.flush()
                exit_code = 0

    except LookupError as le:
        sys.stderr.write("Lookup error: " + str(le))
    except Exception:  # pylint: disable=broad-except
        sys.stderr.write(
            f"Unexpected Error {str(sys.exc_info()[0])}. {str(sys.exc_info()[1])}"
        )
    sys.exit(exit_code)


if __name__ == "__main__":
    cma_cli()
