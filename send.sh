#!/usr/bin/env bash

exec 3<>/dev/tcp/$1/$2
echo -e "TEST" >&3
#cat <&3
echo "Finished sending TEST"
