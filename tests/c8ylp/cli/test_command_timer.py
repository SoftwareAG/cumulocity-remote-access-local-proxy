#
# Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
