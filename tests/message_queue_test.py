from unittest.mock import patch

from aerith_cbot.services.abstractions.models.chat import ChatType
from aerith_cbot.services.implementations.chat_dispatcher import MessageQueue


@patch("time.time")
def test_fetch_ready_entries_by_time(mock_time):
    start_time = 1000.0
    mock_time.return_value = start_time

    queue = MessageQueue()
    queue.add(123, ChatType.private, [{"role": "user", "content": "Hello"}])

    assert len(queue.fetch_ready_entries()) == 0

    mock_time.return_value = start_time + MessageQueue.TIME_LIMIT_UPPER_BOUND + 0.1

    ready_entries = queue.fetch_ready_entries()

    assert len(ready_entries) == 1
    assert ready_entries[0].chat_id == 123


@patch("time.time")
def test_fetch_ready_entries_by_count(mock_time):
    mock_time.return_value = 1000.0

    queue = MessageQueue()
    queue.add(123, ChatType.private, [{"role": "user", "content": "Message 1"}])

    assert len(queue.fetch_ready_entries()) == 0

    messages = [
        {"role": "user", "content": f"Message {i}"} for i in range(2, MessageQueue.COUNT_LIMIT + 2)
    ]
    queue.add(123, ChatType.private, messages)

    ready_entries = queue.fetch_ready_entries()

    assert len(ready_entries) == 1
    assert len(ready_entries[0].messages) == MessageQueue.COUNT_LIMIT + 1


@patch("time.time")
def test_clear(mock_time):
    mock_time.return_value = 1000.0

    queue = MessageQueue()
    queue.add(123, ChatType.private, [{"role": "user", "content": "Test"}])
    queue.add(456, ChatType.group, [{"role": "user", "content": "Other chat"}])

    queue.clear(123)

    mock_time.return_value = 1000.0 + MessageQueue.TIME_LIMIT_UPPER_BOUND + 0.1

    ready_entries = queue.fetch_ready_entries()

    assert len(ready_entries) == 1
    assert ready_entries[0].chat_id == 456


@patch("time.time")
def test_latest_update_not_ready(mock_time):
    current_time = 1000.0
    mock_time.return_value = current_time

    queue = MessageQueue()
    queue.add(123, ChatType.private, [{"role": "user", "content": "Initial message"}])

    with patch("random.randint", return_value=MessageQueue.TIME_LIMIT_UPPER_BOUND):
        # still not ready cause 0 seconds passed since last adding
        assert len(queue.fetch_ready_entries()) == 0

        current_time += MessageQueue.TIME_LIMIT_UPPER_BOUND - 0.5
        mock_time.return_value = current_time

        queue.add(123, ChatType.private, [{"role": "user", "content": "New message"}])

        # same: still not ready cause 0 seconds passed since last adding
        assert len(queue.fetch_ready_entries()) == 0

        current_time += MessageQueue.TIME_LIMIT_UPPER_BOUND - 0.5
        mock_time.return_value = current_time

        # not ready cause only MessageQueue.TIME_LIMIT - 0.5 seconds passed, so 0.5 seconds left
        assert len(queue.fetch_ready_entries()) == 0

        current_time += 1
        mock_time.return_value = current_time

        # wait fot another second and now entries are available
        assert len(queue.fetch_ready_entries()) == 1
