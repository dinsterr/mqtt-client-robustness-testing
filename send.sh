#!/usr/bin/env bash



exec 3<>/dev/tcp/$1/$2
for i in {1..9}
do
  echo -e "$i" >&3

  echo "$i"
  echo "$i" >&2
done
# cat <&3
echo "Finished sending TEST"
exit 1