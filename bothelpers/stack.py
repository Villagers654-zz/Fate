"""
Module for building up a counter over time for unique IDs

Classes:
    Stack

Misc variables:
    __title__
    __author__
    __license__
    __copyright__
    __version__

Copyright (C) 2018-present Michael Stollings
Unauthorized copying, or reuse of anything in this repository written by the owner, via any medium is strictly prohibited.
This copyright notice, and this permission notice must be included in all copies, or substantial portions of the Software
Proprietary and confidential
Written by Michael Stollings <mrmichaelstollings@gmail.com>
"""

__title__ = "StackCounter"
__author__ = "Michael Stollings"
__licence__ = "Proprietary and confidential"
__copyright__ = "Copyright (C) 2018-present Michael Stollings"
__version__ = "1.0.0"


from time import time, sleep


class Stack:
    """
    An object to stack up counters at an interval

    Parameters
    ----------
    interval : int
        the interval at which to add +1 to a IDs counter
    timeout : int, optional
        the seconds at which to reset on use if inactive for this period of time
    max_stack : int
        the counter limit
    """
    def __init__(self, interval, timeout, max_stack):
        self.interval = interval
        self.timeout = timeout
        self.max_stack = max_stack
        self.index = {}

    def get_stack(self, unique_id):
        """Gets the IDs number of stacked intervals"""
        if unique_id in self.index:
            time_since = time() - self.index[unique_id]
            self.index[unique_id] = time()

            # Stacks expired due to not being used within the timeout
            if self.timeout and time_since > self.timeout:
                return 0

            # Limit the stack to `max_stack`
            stack = int(time_since / self.interval)
            if stack > self.max_stack:
                stack = self.max_stack

            return stack

        # For first use with a ID, set the last_used_time and return 0
        self.index[unique_id] = time()
        return 0

