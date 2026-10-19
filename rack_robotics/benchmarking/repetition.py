"""Bookkeeping for consecutive physical cycles; contains no scene reset calls."""
import copy
import math


def validate_request(cycles, role, occupied=False):
    if type(cycles) is not int or not 1 <= cycles <= 100:
        raise ValueError('Cycle count must be an integer from1 through100')
    if cycles > 1 and (role != 'control' or occupied):
        raise ValueError('Continuous cycles are a separate nominal diagnostic, not randomized/occupied trials')


class CycleLedger:
    def __init__(self, requested):
        validate_request(requested, 'control')
        self.requested = requested
        self.records = []
        self.initial = None

    @property
    def elapsed(self):
        return sum(row['duration_s'] for row in self.records)

    def begin(self, measured_state):
        if (self.initial is not None or len(self.records) >= self.requested
                or self.records and not self.records[-1]['passed']):
            raise ValueError('Cannot begin an extra, overlapping or post-failure cycle')
        self.initial = copy.deepcopy(measured_state)
        return bool(measured_state['retained'] and measured_state['initialization_helpers_disabled'])

    def finish(self, outcome, measured_state):
        duration = outcome['duration_s']
        if self.initial is None or not math.isfinite(duration) or duration < 0:
            raise ValueError('Missing start or invalid cycle duration')
        boundary_ok = bool(self.initial['retained'] and measured_state['retained']
                           and self.initial['initialization_helpers_disabled']
                           and measured_state['initialization_helpers_disabled'])
        task_ok = bool(outcome['done'] and not outcome['error']
                       and outcome['unplug_success'] and outcome['replug_success'])
        record = {'cycle': len(self.records)+1, 'start_time_s': self.elapsed,
                  'end_time_s': self.elapsed+duration, **copy.deepcopy(outcome),
                  'initial_state': self.initial, 'final_state': copy.deepcopy(measured_state),
                  'boundary_checks_passed': boundary_ok,
                  'passed': task_ok and (self.requested == 1 or boundary_ok)}
        self.records.append(record)
        self.initial = None
        return record

    @property
    def passed(self):
        return len(self.records) == self.requested and all(row['passed'] for row in self.records)
