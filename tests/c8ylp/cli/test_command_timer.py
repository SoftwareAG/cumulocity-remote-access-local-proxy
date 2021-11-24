"""Test command timer"""
import time
import pytest
from c8ylp.timer import CommandTimer


def test_timer_calling_stop_before_start():
    """Test calling stop before timer has started"""
    timer = CommandTimer("My task")
    assert timer.stop() == 0


def test_timer_context(capfd: pytest.CaptureFixture):
    """Test timing using context"""
    timer = CommandTimer("My task", on_exit=print)

    with timer:
        time.sleep(1)

    # Use approx due to differences in precision of timers on different OS's
    assert pytest.approx(timer.last_duration, abs=0.5) == 1.0
    out, err = capfd.readouterr()
    assert out == "My task: 0:00:01\n"
    assert not err
