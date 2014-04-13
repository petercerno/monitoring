
Monitoring
==========

A simple python application for monitoring your time.

Bitcoin Address: `14prQgT7Ur6zsEfCKYyvfQHkFVNWkfumHz`

Motivation
----------

Inspired by Chapter "Know Thy Time" of Peter F. Drucker's book: "The Effective Executive."

As Peter F. Drucker states in this chapter: 

> "Effective executives, in my observation, do not start with their tasks. They start with their time. And they do not start out with planning. They start by  finding out where their time actually goes."

The aim of the time monitoring application is to provide developers / executives with a simple tool for monitoring their time. The input for the application is a simple text file containing the so-called "work log." The work log can contain an arbitrary text. However, only specific entries will be recognized and processed by the time monitoring application. These entries usually contain some information about the date and / or time-span of a specific task. For instance:

    2013-10-07 22:00 - 22:30 Working on the time monitoring app

The time monitoring application recognizes the following statements in the work log:

    yyyy-MM-dd         ... date
    hh:mm task         ... task and its time duration
    hh:mm - hh:mm task ... task and its time interval
    % task -> project  ... task assigned to a project
    # comment          ... comment

We provide a sample work log (`work.txt`) that illustrates all important concepts.

The time monitoring application recognizes the following command line options:

    positional arguments:
      work                     work file

    optional arguments:
      -h, --help               show this help message and exit
      -f FROM, --from FROM     date from (including)
      -t TOEX, --toex TOEX     date to (excluding)
      -w WIDTH, --width WIDTH  display width (columns)

Sample use:

    python monitoring.py work.txt -f 2013-09-01 -t 2013-10-01

The time monitoring application outputs the work log statistics (inside the specified date interval). Additionally, it detects and informs you of all potential typos and errors in the work log.

LICENSE
=======

The time monitoring application is licensed to you under MIT.X11:

Copyright (c) 2014 Peter Cerno.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.