"""
Tests for cumulus-message-adapter command-line interface
"""
import json
import os
import subprocess
import pytest


def execute_command(cmd, input_message):
    """
    execute an external command command, and returns command exit status, stdout and stderr
    """
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    outstr, errorstr = process.communicate(input=input_message.encode())
    exitstatus = process.poll()
    if errorstr:
        print(errorstr.decode())  # pylint: disable=superfluous-parens
    return exitstatus, outstr.decode(), errorstr.decode()


def read_streaming_output(stream_process):
    """
    Given a subprocess, read stdout from that process until <EOC> line received
    """
    proc_stdout = stream_process.stdout
    buffer = ''
    itercount = 0
    eoc_count = 0
    while not stream_process.poll() and itercount < 1000:
        itercount += 1
        next_line = proc_stdout.readline().decode('utf-8').rstrip('\n')
        if next_line != '<EOC>':
            buffer += next_line
        else:
            eoc_count += 1
            return json.loads(buffer)
    err_string = ''.join([x.decode('utf-8') for x in stream_process.stderr.readlines()])
    raise RuntimeError(err_string)


def write_streaming_input(command, proc_input, p_stdin):
    """
    Given a stdin pipe for a subprocess, write command/proc input to CMA subprocess
    """
    p_stdin.write((command + "\n").encode('utf-8'))
    p_stdin.write(json.dumps(proc_input).encode('utf-8'))
    p_stdin.write('\n'.encode('utf-8'))
    p_stdin.write('<EOC>\n'.encode('utf-8'))
    p_stdin.flush()


def place_remote_message(in_msg, test_folder, s3):
    """
    Place the remote message on S3 before test
    """
    bucket_name = in_msg['replace']['Bucket']
    key_name = in_msg['replace']['Key']
    data_filename = os.path.join(test_folder, key_name)
    with open(data_filename, 'r', encoding='utf-8') as data_file:
        datasource = json.load(data_file)
    s3.Bucket(bucket_name).create()
    s3.Object(bucket_name, key_name).put(Body=json.dumps(datasource))
    return {'bucket_name': bucket_name, 'key_name': key_name}


def clean_up_remote_message(bucket_name, key_name, s3):
    """
    cleans up the remote message from the s3 bucket
    """
    delete_objects_object = {'Objects': [{'Key': key_name}]}
    s3.Bucket(bucket_name).delete_objects(Delete=delete_objects_object)
    s3.Bucket(bucket_name).delete()


def transform_messages_streaming(params, test_folder, s3):  # pylint: disable=too-many-locals
    """
    Given a testcase, run 'streaming' interface against input and check if outputs are correct
    """
    schemas = {
        'input': 'schemas/examples-messages.input.json',
        'output': 'schemas/examples-messages.output.json',
        'config': 'schemas/examples-messages.config.json'
    }
    context = params.get('context', {})
    schemas = params.get('schemas', schemas)
    testcase = params['testcase']

    inp = open(os.path.join(test_folder, f'{testcase}.input.json'), encoding='utf-8')
    in_msg = json.loads(inp.read())
    s3meta = None
    if 'replace' in in_msg:
        s3meta = place_remote_message(in_msg, test_folder, s3)

    cma_input = {'event': in_msg, 'context': context, 'schemas': schemas}
    current_directory = os.getcwd()

    stream_process = subprocess.Popen(['python', current_directory, 'stream'],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    write_streaming_input('loadAndUpdateRemoteEvent', cma_input, stream_process.stdin)
    load_and_update_remote_event_response = read_streaming_output(stream_process)
    cma_input = {'event': load_and_update_remote_event_response, 'context': context,
                 'schemas': schemas}
    write_streaming_input('loadNestedEvent', cma_input, stream_process.stdin)
    load_nested_event_response = read_streaming_output(stream_process)

    message_config = load_nested_event_response.get('messageConfig')
    if 'messageConfig' in load_nested_event_response:
        del load_nested_event_response['messageConfig']
    cma_input = {'handler_response': load_nested_event_response,
                 'event': load_and_update_remote_event_response,
                 'message_config': message_config, 'schemas': schemas}
    write_streaming_input('createNextEvent', cma_input, stream_process.stdin)
    create_next_event_response = read_streaming_output(stream_process)

    stream_process.stdin.write('<EXIT>\n'.encode('utf-8'))
    stream_process.stdin.flush()
    exit_code = stream_process.wait(20)
    assert exit_code == 0

    out = open(os.path.join(test_folder, f'{testcase}.output.json'), encoding='utf-8')
    out_msg = json.loads(out.read())
    assert create_next_event_response == out_msg

    if s3meta is not None:
        clean_up_remote_message(s3meta['bucket_name'], s3meta['key_name'], s3)


def transform_messages(params, test_folder, s3):  # pylint: disable=too-many-locals
    """
    transform cumulus messages, and check if the command return status and outputs are correct.
    Each test case (such as 'basic') has its corresponding example messages and schemas.
    """
    schemas = {
        'input': 'schemas/examples-messages.input.json',
        'output': 'schemas/examples-messages.output.json',
        'config': 'schemas/examples-messages.config.json'
    }
    context = params.get('context', None)
    schemas = params.get('schemas', schemas)
    testcase = params['testcase']

    inp = open(os.path.join(test_folder, f'{testcase}.input.json'), encoding='utf-8')
    in_msg = json.loads(inp.read())
    s3meta = None
    if 'replace' in in_msg:
        s3meta = place_remote_message(in_msg, test_folder, s3)

    all_input = {'event': in_msg, 'context': context, 'schemas': schemas}
    current_directory = os.getcwd()
    remote_event_command = ['python', current_directory, 'loadAndUpdateRemoteEvent']
    (exitstatus, remote_event, _) = execute_command(remote_event_command, json.dumps(all_input))
    assert exitstatus == 0
    full_event = json.loads(remote_event)

    all_input = {'event': full_event, 'context': context, 'schemas': schemas}
    load_nested_event = ['python', current_directory, 'loadNestedEvent']
    (exitstatus, nested_event, _) = execute_command(load_nested_event, json.dumps(all_input))
    assert exitstatus == 0

    msg = json.loads(nested_event)
    message_config = msg.get('messageConfig')
    if 'messageConfig' in msg:
        del msg['messageConfig']
    all_input = {'handler_response': msg, 'event': full_event,
                 'message_config': message_config, 'schemas': schemas}
    create_next_event = ['python', current_directory, 'createNextEvent']
    (exitstatus, next_event, _) = execute_command(create_next_event, json.dumps(all_input))
    assert exitstatus == 0

    out = open(os.path.join(test_folder, f'{testcase}.output.json'), encoding='utf-8')
    out_msg = json.loads(out.read())
    print('Comparing expected event to actual event:\n\n')
    print('\n-=-=-=-=-=-=-=-=-\n')
    print(out_msg)
    print('\n-=-=-=-=-=-=-=-=-\n')
    print(next_event)
    print('\n-=-=-=-=-=-=-=-=-\n')
    assert json.loads(next_event) == out_msg

    if s3meta is not None:
        clean_up_remote_message(s3meta['bucket_name'], s3meta['key_name'], s3)


def test_basic(test_folder, s3):
    """ test basic message """
    transform_messages({'testcase': 'basic'}, test_folder, s3)
    transform_messages_streaming({'testcase': 'basic'}, test_folder, s3)


def test_basic_no_config(test_folder, s3):
    """ test basic no config message """
    schemas = {
        'input': 'schemas/examples-messages.input.json',
        'output': 'schemas/examples-messages-no-config.output.json',
    }
    transform_messages({'testcase': 'basic_no_config', 'schemas': schemas}, test_folder, s3)
    transform_messages_streaming(
        {'testcase': 'basic_no_config', 'schemas': schemas}, test_folder, s3)


def test_exception(test_folder, s3):
    """ test remote message with exception """
    transform_messages({'testcase': 'exception'}, test_folder, s3)
    transform_messages_streaming({'testcase': 'exception'}, test_folder, s3)


def test_jsonpath(test_folder, s3):
    """ test jsonpath message """
    transform_messages({'testcase': 'jsonpath'}, test_folder, s3)
    transform_messages_streaming({'testcase': 'jsonpath'}, test_folder, s3)


def test_meta(test_folder, s3):
    """ test meta message """
    transform_messages({'testcase': 'meta'}, test_folder, s3)
    transform_messages_streaming({'testcase': 'meta'}, test_folder, s3)


def test_remote(test_folder, s3):
    """ test remote message """
    transform_messages({'testcase': 'remote'}, test_folder, s3)
    transform_messages_streaming({'testcase': 'remote'}, test_folder, s3)


def test_templates(test_folder, s3):
    """ test templates message """
    transform_messages({'testcase': 'templates'}, test_folder, s3)
    transform_messages_streaming({'testcase': 'templates'}, test_folder, s3)


def test_validation_failure_case(test_folder, s3):
    """ test validation failure case """
    with pytest.raises(AssertionError):
        transform_messages({'testcase': 'invalidinput'}, test_folder, s3)


def test_workflow_task_meta(test_folder, s3):
    """ test meta.workflow task """
    context = {
        'functionName': 'first_function',
        'invokedFunctionArn': 'fakearn',
        'functionVersion': '1',
    }
    transform_messages(
        {'testcase': 'workflow_tasks', 'context': context}, test_folder, s3)
    transform_messages_streaming(
        {'testcase': 'workflow_tasks', 'context': context}, test_folder, s3)


def test_multiple_workflow_tasks_meta(test_folder, s3):
    """ test multiple meta.workflow_task entries"""
    context = {
        'functionName': 'second_function',
        'invokedFunctionArn': 'fakearn2',
        'functionVersion': '2',
    }
    transform_messages(
        {'testcase': 'workflow_tasks_multiple', 'context': context}, test_folder, s3)
    transform_messages_streaming(
        {'testcase': 'workflow_tasks_multiple', 'context': context}, test_folder, s3)

