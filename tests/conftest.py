"""
Shared pytest fixtures for cumulus-message-adapter tests.
"""
import os
import pytest
from message_adapter import aws, message_adapter


@pytest.fixture(autouse=True, scope='session')
def lambda_task_root():
    """Set the LAMBDA_TASK_ROOT environment variable once for the entire test session."""
    os.environ["LAMBDA_TASK_ROOT"] = os.path.join(os.getcwd(), 'examples')


@pytest.fixture(scope='session')
def test_folder():
    """Path to the examples/messages directory."""
    return os.path.join(os.getcwd(), 'examples/messages')


@pytest.fixture(scope='session')
def context_folder():
    """Path to the examples/contexts directory."""
    return os.path.join(os.getcwd(), 'examples/contexts')


@pytest.fixture(scope='session')
def schemas_folder():
    """Path to the examples/schemas directory."""
    return os.path.join(os.getcwd(), 'examples/schemas')


@pytest.fixture(scope='session')
def s3():
    """AWS S3 resource."""
    return aws.s3()


@pytest.fixture(scope='session')
def cumulus_message_adapter():
    """MessageAdapter instance."""
    return message_adapter.MessageAdapter()


@pytest.fixture(scope='session')
def bucket_name():
    """Name of the S3 test bucket."""
    return 'testing-internal'


@pytest.fixture(scope='session')
def key_name():
    """S3 key name for the test event object."""
    return 'blue_whale-event.json'


@pytest.fixture(scope='session')
def config_key_name():
    """S3 key name for the config test object."""
    return 'cma_config_blue_whale-event.json'


@pytest.fixture(scope='session')
def test_uuid():
    """UUID used for remote event object keys in tests."""
    return 'aad93279-95d4-4ada-8c43-aa5823f8bbbc'


@pytest.fixture(scope='session')
def next_event_object_key_name(test_uuid):
    """S3 key name for the next event object."""
    return f'events/{test_uuid}'


@pytest.fixture
def s3_object():
    """S3 test event object payload."""
    return {'input': ':blue_whale:'}


@pytest.fixture
def config_s3_object():
    """S3 config test object payload."""
    return {'task_config': 'bad value', 'input': ':blue_whale:'}


@pytest.fixture
def nested_response():
    """Handler response used as input to create_next_event."""
    return {'input': {'dataLocation': 's3://source.jpg'}}


@pytest.fixture
def event_with_cma():
    """Event containing a 'cma' key."""
    return {'cma': {'foo': 'bar', 'event': {'some': 'object'}}}


@pytest.fixture
def event_with_replace(bucket_name, key_name):
    """Event containing a 'replace' key pointing to S3."""
    return {'replace': {'Bucket': bucket_name, 'Key': key_name, 'TargetPath': '$'}}


@pytest.fixture
def config_event_with_replace(bucket_name, config_key_name):
    """Event with a 'cma' wrapper and a 'replace' key targeting the config S3 object."""
    return {
        'cma': {
            'task_config': 'foo_bar',
            'event': {
                'replace': {'Bucket': bucket_name, 'Key': config_key_name, 'TargetPath': '$'}
            }
        }
    }


@pytest.fixture
def event_without_replace():
    """Simple event without a 'replace' key."""
    return {'input': ':baby_whale:'}
