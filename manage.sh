#!/usr/bin/env bash

###
# Generalized Scripts for Python setup
# @author: Alvin Wan
# @site: alvinwan.com
###

function gs_install {

  # install virtualenv
  check=`virtualenv --version`
  [ $? != 0 ] && sudo pip3 install virtualenv

  # check for virtualenv
  python3 -m venv env

  # activate virtualenv
  source env/bin/activate

  # install
  pip3 install --upgrade pip
  pip3 install -r requirements.txt

  # add configuration file if does not exist
  [ ! -f "queue.cfg" ] && cp default-config.cfg config.cfg

  echo "---

  [OK] Installation complete.
  Use 'make db' to create the database. Use 'make refresh' to DELETE the old
  database and recreate one using the new schema.
  "
}

function gs_check {
  echo '2 checks:'

  exit=`python3 --version`
  [ $? != 0 ] && echo '[Error] Python3 not found' || echo '[OK] Python3 found'

  exit=`mysql --version`
  [ $? != 0 ] && echo '[Error] MySQL not found' || echo '[OK] MySQL found'
}

function gs_activate {
  #!/usr/bin/env bash

  # check for virtualenv
  [ -d "env" ] && python3 -m venv env

  # activate virtualenv
  source env/bin/activate

  echo "---

  [OK] Virtualenv activated.
  "
}

###
# Commands
# source manage.sh [command]
###

[ $1 = "activate" ] && gs_activate
[ $1 = "check" ] && gs_check
[ $1 = "install" ] && gs_install
