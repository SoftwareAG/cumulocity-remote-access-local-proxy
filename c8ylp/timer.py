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
"""Timer"""

import logging
import time
from datetime import timedelta
from typing import Callable


class CommandTimer:
    """Command Timer which shows how long a command takes to run
    and prints out a message to the user

    Example

    >>>
    with CommandTimer():
        print("Doing someting")
        time.sleep(100)
    >>>

    """

    def __init__(self, message: str, on_exit: Callable[[], None] = None) -> None:
        self.message = message
        self.start_time = 0
        self.last_duration = 0
        self._on_exit = on_exit

    def start(self):
        """Start the timer"""
        self.start_time = time.monotonic()
        return self

    def stop(self) -> float:
        """Stop the timer and return the duration in seconds

        Returns:
            float: Duration in seconds
        """
        if not self.start_time:
            return 0
        self.last_duration = time.monotonic() - self.start_time
        return self.last_duration

    def stop_with_message(self):
        """Stop timer and print out a message about the duration"""
        duration = timedelta(seconds=(round(self.stop(), 0)))
        msg = f"{self.message}: {duration}"
        logging.info(msg)
        if callable(self._on_exit):
            self._on_exit(msg)

    def __enter__(self) -> None:
        self.start()

    def __exit__(self, _type, _value, _traceback) -> None:
        self.stop_with_message()
