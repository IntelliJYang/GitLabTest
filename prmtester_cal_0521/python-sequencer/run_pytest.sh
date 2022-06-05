#!/bin/bash
# precondition:
# for coverage:
# pip install pytest --user
# pip install pytest-cov --user

# pip install pytest-pep8 --user
# pip install mock --user

basepath=$(cd `dirname $0`; pwd)
export PYTHONPATH=$basepath
if [[ -d virtualenv ]]; then
	rm -rf virtualenv
fi
virtualenv virtualenv --no-site-packages
source virtualenv/bin/activate
pip install -r requirements.txt
pytest -vv --cov-config .coveragerc --cov=x527 --cov-report=term --cov-report=html:htmlcov
deactivate
rm -rf virtualenv
