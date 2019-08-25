#!/bin/sh

HOST=$1
PORT=$2
shift 2

echo "Waiting for" "$HOST" "$PORT"

for i in `seq 60` ; do
    nc -vzw 1 "$HOST" "$PORT" > /dev/null 2>&1

    if [ $? -eq 0 ] ; then
        echo "Waiting's over"
        exec "$@"
        exit 0
    fi
    sleep 1
done
echo "Operation timed out" >&2
exit 1
