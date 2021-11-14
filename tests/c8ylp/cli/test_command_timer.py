"""Test command timer"""
import time
import pytest
from c8ylp.main import CommandTimer


def test_timer_calling_stop_before_start():
    """Test calling stop before timer has started"""
    timer = CommandTimer("My task")
    assert timer.stop() == 0


def test_timer_context(capfd: pytest.CaptureFixture):
    """Test timing using context"""
    timer = CommandTimer("My task")

    with timer:
        time.sleep(1)
    assert timer.last_duration > 1.0
    out, err = capfd.readouterr()
    assert out == "My task: 0:00:01\n"
    assert not err
