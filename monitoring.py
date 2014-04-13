#!/usr/bin/env python
__author__ = 'Peter Cerno'

import argparse
import datetime
import re
import sys
import pandas as pd
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from pandas import DataFrame


class Monitoring(object):
    """
    Time monitoring class.
    """
    def __init__(self, date_from, date_toex):
        """
        Constructor of the time monitoring class.
        @param date_from: Date from (including).
        @param date_toex: Date to (excluding).
        """
        self.date_from = date_from
        self.date_toex = date_toex
        self._line = 0
        self._date = None
        self._time = None
        self._date_line = None
        self._time_line = None
        self._data = []
        self._proj = []
        self._comm = []
        self._warn = []

    # Match a date yyyy-mm-dd
    _match_date = re.compile(
        r"""^\s*
        (?P<year>[0-9]{4})-
        (?P<month>1[0-2]|0[1-9])-
        (?P<day>3[01]|0[1-9]|[12][0-9])
        (?P<remainder>.*)$""",
        re.IGNORECASE | re.UNICODE | re.VERBOSE)
    # Match a time interval hh:mm - hh:mm
    _match_time_interval = re.compile(
        r"""^\s*
        (?P<hour_from>2[0-3]|[01][0-9]):
        (?P<minute_from>[0-5][0-9])\s*-\s*
        (?P<hour_to>2[0-3]|[01][0-9]):
        (?P<minute_to>[0-5][0-9])
        (?P<remainder>.*)$""",
        re.IGNORECASE | re.UNICODE | re.VERBOSE)
    # Match a time hh:mm
    _match_time = re.compile(
        r"""^\s*
        (?P<hour>2[0-3]|[01][0-9]):
        (?P<minute>[0-5][0-9])
        (?P<remainder>.*)$""",
        re.IGNORECASE | re.UNICODE | re.VERBOSE)
    # Match a task
    _match_task = re.compile(
        r"""^\s*
        (?P<task>[^#]+)
        (?P<remainder>.*)$""",
        re.IGNORECASE | re.UNICODE | re.VERBOSE)
    # Match an assignment of a task to a project
    _match_assignment = re.compile(
        r"""^\s*%\s*
        (?P<task>[^#]+)->
        (?P<project>[^#]+)
        (?P<remainder>.*)$""",
        re.IGNORECASE | re.UNICODE | re.VERBOSE)
    # Match a comment starting with #
    _match_comment = re.compile(
        r"^\s*#\s*(.*)$",
        re.IGNORECASE | re.UNICODE)
    
    def process(self, lines):
        """
        Process all lines of the work log.
        @param lines: All lines of the work log.
        """
        for line in lines:
            self._process_line(line)
    
    def print_result(self):
        """
        Print the result after processing the work log.
        """
        task_table, proj_table, task_projs = self.get_result()
        if (task_table is None) or\
           (proj_table is None) or\
           (task_projs is None):
            return
        print 'Task Table'
        print task_table
        print
        print 'Project Table'
        print proj_table
        task_projs_count = task_projs.count()
        task_zero = task_projs_count[task_projs_count == 0].index.values
        task_many = task_projs_count[task_projs_count >= 2].index.values
        if len(task_zero) > 0:
            print
            print 'Tasks assigned to no projects:', ', '.join(task_zero)
        if len(task_many) > 0:
            print
            print 'Tasks assigned to multiple projects:', ', '.join(task_many)
            for group in task_projs:
                if group[1].count() > 1:
                    print str(group[0]) + ':', ', '.join(group[1].values)
        if len(self._comm) > 0:
            print
            print 'Comments:'
            for comm in self._comm:
                print '%08d: %s' % (comm[0], comm[2])
        if len(self._warn) > 0:
            print
            print 'Warnings:'
            for warn in self._warn:
                print '%08d: %s' % (warn[0], warn[1])

    def get_result(self):
        """
        Get the result after processing the work log.
        """
        if (self._data is None) or (len(self._data) == 0) or\
           (self._proj is None) or (len(self._proj) == 0):
            return (None, None, None)
        task_frame = DataFrame(self._data, 
            columns = ['line', 'date', 'hours', 'task'])
        proj_frame = DataFrame(self._proj, 
            columns = ['line', 'date', 'task', 'project'])
        # Group projects assigned to tasks
        task_projs = (task_frame[['task']])\
            .merge(proj_frame[['task', 'project']], how='outer', on='task')\
            .drop_duplicates(['task', 'project'])\
            .groupby('task').project
        # Filter tasks without projects
        task_frame = task_frame.merge(proj_frame[['task']]\
            .drop_duplicates('task'))
        # Construct task table
        task_table = (task_frame[['task', 'date', 'hours']])\
            .groupby(['task', 'date']).sum()\
            .unstack()['hours'].fillna(0.0)
        # Assign tasks to projects
        join_frame = task_frame.merge(proj_frame, 
            how='inner', on='task', suffixes=['_task', '_proj'])
        join_frame = \
            (join_frame[join_frame.line_task <= join_frame.line_proj])\
            .sort(columns=['line_task', 'line_proj'])\
            .drop_duplicates('line_task')
        # Construct project table
        proj_table = (join_frame[['date_task', 'project', 'hours']])\
            .groupby(['project', 'date_task']).sum()\
            .unstack()['hours'].fillna(0.0)
        proj_table.columns.name = 'date'
        # Set totals
        task_table['TOTAL'] = task_table.sum(axis=1)
        proj_table['TOTAL'] = proj_table.sum(axis=1)
        task_table.ix['TOTAL'] = task_table.sum()
        proj_table.ix['TOTAL'] = proj_table.sum()
        return (task_table, proj_table, task_projs)
    
    def _process_line(self, line):
        """
        Process one line of the work log.
        @param line: Line of the work log.
        """
        date, time, elap, task, proj, comm, rest = self._analyze_line(line)
        date_not_changed = True
        self._line += 1
        if date:
            date_not_changed = False
            if self._date:
                if date < self._date:
                    self._warn.append([
                        self._line,
                        'The date %s on the line %d is smaller '
                        'than the previous date %s on the line %d' % (
                            date.strftime('%Y-%m-%d'), 
                            self._line, 
                            self._date.strftime('%Y-%m-%d'),
                            self._date_line)])
                elif date == self._date:
                    date_not_changed = True
            self._date = date
            self._date_line = self._line
        if time and (time[0], time[1]) >= (time[2], time[3]):
            self._warn.append([
                self._line, 'The time %s on the line %d is illegal' % (
                    '%02d:%02d - %02d:%02d' % time, self._line)])
        if date_not_changed:
            if time:
                if self._time:
                    curr_time = (time[0], time[1])
                    prev_time = (self._time[2], self._time[3])
                    if curr_time < prev_time:
                        self._warn.append([
                            self._line,
                            'The time %s on the line %d overlaps '
                            'the previous time %s on the line %d' % (
                                '%02d:%02d - %02d:%02d' % time, 
                                self._line, 
                                '%02d:%02d - %02d:%02d' % self._time,
                                self._time_line)])
                self._time = time
                self._time_line = self._line
        else:
            self._time = time
            self._time_line = self._line
        if len(rest) > 0:
            self._warn.append([
                self._line,
                'Unrecognized line %d: %s' % (self._line, rest)])
        if self._date and\
           (self._date >= self.date_from) and (self._date < self.date_toex):
            if elap and task:
                self._data.append([self._line, self._date, elap, task])
            if task and proj:
                self._proj.append([self._line, self._date, task, proj])
            if comm:
                self._comm.append([self._line, self._date, comm])
    
    def _analyze_line(self, line):
        """
        Analyze one line of the work log.
        @param line: Line of the work log.
        """
        date = None
        time = None
        elap = None
        task = None
        proj = None
        comm = None
        rest = None
        match = self._match_date.search(line)
        if match:
            year = int(match.group('year'))
            month = int(match.group('month'))
            day = int(match.group('day'))
            line = match.group('remainder').strip()
            date = datetime.date(year, month, day)
        match = self._match_time_interval.search(line)
        if match:
            hour_from = int(match.group('hour_from'))
            minute_from = int(match.group('minute_from'))
            hour_to = int(match.group('hour_to'))
            minute_to = int(match.group('minute_to'))
            time = (hour_from, minute_from, hour_to, minute_to)
            line = match.group('remainder').strip()
            elap = max(0.0, hour_to - hour_from +\
                   round((minute_to - minute_from)/60.0, 2))
        else:
            match = self._match_time.search(line)
            if match:
                hour = int(match.group('hour'))
                minute = int(match.group('minute'))
                line = match.group('remainder').strip()
                elap = hour + round(minute/60.0, 2)
        if not elap is None:
            match = self._match_task.search(line)
            if match:
                task = match.group('task').strip()
                line = match.group('remainder').strip()
        else:
            match = self._match_assignment.search(line)
            if match:
                task = match.group('task').strip()
                proj = match.group('project').strip()
                line = match.group('remainder').strip()
        match = self._match_comment.search(line)
        if match:
            comm = match.group(1).strip()
            line = ''
        rest = line.strip()
        return (date, time, elap, task, proj, comm, rest)

def main():
    """
    Time monitoring application.
    """
    # global monitoring
    parser = argparse.ArgumentParser(description='Time monitoring application')
    parser.add_argument('work', help='work file')
    parser.add_argument('-f', '--from', help='date from (including)')
    parser.add_argument('-t', '--toex', help='date to (excluding)')
    parser.add_argument('-w', '--width', help='display width (columns)')
    args = parser.parse_args()
    args.f = args.__dict__['from']
    args.t = args.__dict__['toex']
    args.w = args.__dict__['width']
    today = datetime.date.today()
    if args.f and args.t:
        date_from = parse(args.f).date()
        date_toex = parse(args.t).date()
        if date_toex <= date_from:
            print "Warning: to-date must be strictly greater than from-date"
            return
    elif args.f and not args.t:
        date_from = parse(args.f).date()
        date_toex = date_from + relativedelta(months=1)
    elif not args.f and args.t:
        date_toex = parse(args.t).date()
        date_from = date_toex - relativedelta(months=1)
    else:
        date_toex = datetime.date(today.year, today.month, 1)
        date_from = date_toex - relativedelta(months=1)
    try:
        display_max_rows = pd.get_option('display.max_rows')
        display_max_columns = pd.get_option('display.max_columns')
        display_height = pd.get_option('display.height')
        display_width = pd.get_option('display.width')
        pd.set_option('display.max_rows',    1000)
        pd.set_option('display.max_columns', 1000)
        pd.set_option('display.height',      1000)
        if args.w:
            pd.set_option('display.width', int(args.w))
        f = open(args.work, 'rU')
        monitoring = Monitoring(date_from, date_toex)
        monitoring.process(f)
        monitoring.print_result()
    except IOError:
        sys.stderr.write('Problem reading: ' + args.work)
    finally:
        pd.set_option('display.max_rows', display_max_rows)
        pd.set_option('display.max_columns', display_max_columns)
        pd.set_option('display.height', display_height)
        pd.set_option('display.width', display_width)
        f.close()

if __name__ == "__main__":
    main()
