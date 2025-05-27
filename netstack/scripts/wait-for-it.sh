#!/bin/bash
# wait-for-it.sh - 等待服務就緒的腳本

set -e

host="$1"
port="$2"
shift 2
cmd="$@"

until nc -z "$host" "$port"; do
  >&2 echo "等待 $host:$port 可用..."
  sleep 1
done

>&2 echo "$host:$port 已就緒"
exec $cmd 