#!/bin/bash

IFS=$'\n'
directories=$(cat directories.txt)

pass=0
fail=0

function prepare_venv() {
    VIRTUALENV="$(which virtualenv)"
    if [ $? -eq 1 ]; then
        # python36 which is in CentOS does not have virtualenv binary
        VIRTUALENV="$(which virtualenv-3)"
    fi
    if [ $? -eq 1 ]; then
        # still don't have virtual environment -> use python3.6 directly
        python3.6 -m venv venv && source venv/bin/activate && python3 "$(which pip3)" install pyflakes
    else
        ${VIRTUALENV} -p python3 venv && source venv/bin/activate && python3 "$(which pip3)" install pyflakes
    fi
}

# run the pyflakes for all files that are provided in $1
function check_files() {
    for source in $1
    do
        echo "$source"
        pyflakes "$source"
        if [ $? -eq 0 ]
        then
            echo "    Pass"
            let "pass++"
        elif [ $? -eq 2 ]
        then
            echo "    Illegal usage (should not happen)"
            exit 2
        else
            echo "    Fail"
            let "fail++"
        fi
    done
}

[ "$NOVENV" == "1" ] || prepare_venv || exit 1

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
pushd "${SCRIPT_DIR}/.."


echo "----------------------------------------------------"
echo "Checking source files for common errors in following"
echo "directories:"
echo "$directories"
echo "----------------------------------------------------"
echo

# checks for the whole directories
for directory in $directories
do
    files=$(find "$directory" -path "$directory/venv" -prune -o -name '*.py' -print)

    check_files "$files"
done


if [ $fail -eq 0 ]
then
    echo "All checks passed for $pass source files"
else
    let total=$pass+$fail
    echo "$fail source files out of $total files needs to be checked and fixed"
    exit 1
fi

popd
