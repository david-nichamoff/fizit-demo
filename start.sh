#!/bin/bash

# Start npm development server
npm run dev &
npm_pid=$!

# Start Django development server
python manage.py runserver &
django_pid=$!

# Start Django event listener
python manage.py listen_events &
events_pid=$!

# Save process IDs to a file
echo $npm_pid > pids.txt
echo $django_pid >> pids.txt
echo $events_pid >> pids.txt

echo "All processes started."