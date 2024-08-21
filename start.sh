#!/bin/bash

# Define log files
npm_log="log/npm.log"
django_log="log/django.log"
events_log="log/events.log"

# Start npm development server and redirect output to log file
npm run dev > $npm_log 2>&1 &
npm_pid=$!

# Start Django development server and redirect output to log file
python manage.py runserver > $django_log 2>&1 &
django_pid=$!

# Start Django event listener and redirect output to log file
python manage.py listen_events > $events_log 2>&1 &
events_pid=$!

# Save process IDs to a file
echo $npm_pid > pids.txt
echo $django_pid >> pids.txt
echo $events_pid >> pids.txt

echo "All processes started. Logs are being written to $npm_log, $django_log, and $events_log"
