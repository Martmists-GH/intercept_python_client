#!/usr/bin/env bash

if [[ "$(id -u)" != "0" ]]; then
   echo "Make sure to run this with sudo or as root, or it won't work!"
   exit 1
fi

hash foo 2>/dev/null

if [[ $? -ne 0 ]]; then
    echo "Make sure python 3.6 or 3.7 is installed and set to python3!"
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

python3 -m pip install -r ${DIR}/requirements.txt
echo "python3 $DIR" > /usr/bin/intercept
chmod +x /usr/bin/intercept

echo "----------------------"
echo
echo "Intercept Python Client installed, use 'intercept' or '/usr/bin/intercept' to run the client."
