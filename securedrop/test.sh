#!/bin/bash

set -e

if [ $(which vagrant) ] ; then
    echo ""
    echo "*** You probably want to run tests from vagrant. Run 'vagrant ssh', then 'cd /vagrant/securedrop' and re-run this script***"
    echo ""
fi

python tests/unit_tests.py
python tests/functional/submit_and_retrieve_message.py
python tests/functional/submit_and_retrieve_file.py

