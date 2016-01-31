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
  virtualenv -p python3 env

  # activate virtualenv
  source env/bin/activate

  # install
  pip3 install --upgrade pip
  pip3 install -r requirements.txt

  # add configuration file if does not exist
  if [ ! -f "queue.cfg" ];
    then cp default-config.cfg config.cfg
  fi

  echo "---

  [OK] Installation complete.
  Use 'make db' to create the database. Use 'make refresh' to DELETE the old
  database and recreate one using the new schema.
  "
}

function gs_check {
  echo '2 checks:'

  exit=`python3 --version`
  if [ $? != 0 ];
    then echo '[Error] Python3 not found';
    else echo '[OK] Python3 found'
  fi

  exit=`mysql --version`
  if [ $? != 0 ];
    then echo '[Error] MySQL not found';
    else echo '[OK] MySQL found'
  fi
}

function gs_activate {

  # check for virtualenv
  if [ -d "env" ];
    then python3 -m venv env
  fi

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

if [[ $1 == "activate" ]];
  then gs_activate
fi

if [[ $1 == "check" ]];
  then gs_check
fi

if [[ $1 == "install" ]];
  then gs_install
fi
