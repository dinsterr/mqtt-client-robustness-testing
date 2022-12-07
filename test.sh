#!/usr/bin/env bash

exec 3<>/dev/tcp/localhost/8088
echo -e "TEST" >&3
cat <&3
