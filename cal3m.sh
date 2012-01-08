#!/usr/bin/env bash

export PATH=/opt/local/libexec/gnubin:$PATH

echo
cal | sed "s/^/ /;s/$/ /;s/ $(date +%e) / $(date +%e | sed 's/./#/g') /" 
cal $(date -d "next month" +"%m %Y") | sed "s/^/ /"
cal $(date -d "+2 month" +"%m %Y") | sed "s/^/ /"
