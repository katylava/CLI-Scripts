#!/usr/bin/env python

import re, os
from subprocess import call

def load_csv_psql(db, infile, table, tmpdir='/tmp', delim=','):
    tmpfile = '%s/%s' % (tmpdir, os.path.basename(infile))
    call(['cp', infile, tmpdir])

    columns = map(variablize, file(tmpfile).readline().split(','))
    columns = map(lambda v: '%s varchar(1000)' % v, columns)
    queries = [
        'drop table %s;' % table,
        'create table %s (%s);' % (table, ','.join(columns)),
        "copy %s from '%s' with csv header delimiter '%s';" % (table, tmpfile, delim),
        'alter table %s add column id serial;' % table,
        'alter table %s add primary key (id);' % table,
    ]
    for q in queries:
        call(['psql','-a','-d',db,'-c',q])

    call(['rm', tmpfile])


def variablize(text, prefix=''):
    if not prefix:
        # if no prefix, move any digits or non-word chars to the end
        parts = re.match('(^[\W\d]*)(.*$)', text).groups()
        text = "%s %s" % (parts[1], parts[0])
    text = ("%s %s" % (prefix, text)).strip().lower()
    text =  re.sub('[\W]', '_', text)
    return re.sub('_*$', '', text)


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [-t|--table=newtable] [-d|--tmpdir=/tmp] database_name  somefile.csv")
    parser.add_option('-t', '--table', help='name of new table to create', default='newtable')
    parser.add_option('-d', '--tmpdir', help='path to temporary directory which psql has permission to access', default='/tmp')
    parser.add_option('-s', '--separator', help='field delimiter character', default=',')
    (options, args) = parser.parse_args()

    if not len(args) == 2:
        parser.error('requires a database name and path to csv file')

    db, infile = args

    if options.table == 'newtable':
        table = variablize(infile)
    else:
        table = options.table

    load_csv_psql(db, infile, table, options.tmpdir, option.separator)

