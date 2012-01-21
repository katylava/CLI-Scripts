#!/usr/bin/env python

import datetime
import re
from textwrap import TextWrapper

filepath = 'times.txt'
date_format = '%a %b %d %Y'

f = file(filepath, 'r')
current_date = []

times = {}
# times[date][projects][project][tasks][task] = interval
# times[date][projects][project][total] = interval
# times[date][total] = interval

def parse_line_as_date(line):
    line = '%s %s' % (line, datetime.datetime.today().year)
    try:
        current_date.append(datetime.datetime.strptime(line, date_format))
    except ValueError:
        return False
    else:
        return True

def matches_proj_time_fmt(line):
    pattern = r'^(\d{1,2}:\d{2}\s?-\s?\d{1,2}:\d{2}\s?&?\s?)+(@[a-zA-Z0-9\-_]+)$'
    if re.match(pattern, line):
        return True
    else:
        return False

def parse_line_as_project_time(line):
    times, project = line.split('@')
    interval = get_interval(times)
    return (project, interval)

def get_interval(timestr):
    timestr = timestr.replace(' ','').strip()
    parts = timestr.split('&')
    total = datetime.timedelta()
    dt = current_date[-1]
    for intvlstr in parts:
        fr, to = intvlstr.split('-')
        fr_hour, fr_min = fr.split(':')
        to_hour, to_min = to.split(':')
        fr_date = dt.replace(hour=int(fr_hour), minute=int(fr_min))
        to_date = dt.replace(hour=int(to_hour), minute=int(to_min))
        if int(fr_hour) > int(to_hour):
            to_date = to_date + datetime.timedelta(days=1)
        intvl = to_date - fr_date
        total += intvl
    return total

def fmtdur(dur, fmt='{:02d}:{:02d}'):
    h = dur.total_seconds() // 3600
    m = dur.total_seconds() // 60 % 60
    s = dur.total_seconds() % 60
    return fmt.format(int(h), int(m), int(s))


l = f.next()
while 1:
    l = l.rstrip()
    if l.startswith('-'):
        try:
            l = f.next()
        except StopIteration:
            break
    elif parse_line_as_date(l):
        times[current_date[-1]] = {'projects': {}, 'total': datetime.timedelta()}
        l = f.next()
    elif matches_proj_time_fmt(l):
        proj_intvl = parse_line_as_project_time(l)
        if proj_intvl:
            dt = current_date[-1]
            project, intvl = proj_intvl
            times[dt]['projects'].setdefault(project, {'total': datetime.timedelta(), 'tasks': {}})
            times[dt]['total'] += intvl
            times[dt]['projects'][project]['total'] += intvl
            task = ''
            l = f.next()
            while l and l.startswith(' '):
                task = '%s %s' % (task, l.strip())
                try:
                    l = f.next()
                except StopIteration:
                    l = False
            times[dt]['projects'][project]['tasks'].setdefault(task, datetime.timedelta())
            times[dt]['projects'][project]['tasks'][task] += intvl
            if not l:
                break
    else:
        try:
            l = f.next()
        except StopIteration:
            break

dates = times.keys()
dates.sort()
grand_total = datetime.timedelta()

for dt in dates:
    wrapper = TextWrapper(width=65, subsequent_indent=" "*13)
    dtd = times[dt]
    grand_total += dtd['total']
    print '-'*18
    print '%s on %s' % (fmtdur(dtd['total']), dt.strftime("%a %b %d"))
    for p, pd in dtd['projects'].items():
        print '  %s @%s' % (fmtdur(pd['total']), p)
        for task, intvl in pd['tasks'].items():
            print '    [%s] %s' % (fmtdur(intvl), wrapper.fill(task))

print '-'*18
print 'Total {}'.format(fmtdur(grand_total))

