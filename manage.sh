#!/usr/bin/env bash

###
# Generalized Scripts for Python setup
# @author: Alvin Wan
# @site: alvinwan.com
###

function gs_install {

  if [[ $CONDA == "false" ]];
    then
      # install virtualenv
      check=`virtualenv --version`
      [ $? != 0 ] && sudo pip3 install virtualenv

      # create env
      virtualenv -p python3 env;

      # activate virtualenv
      source env/bin/activate
    else
      # check for env
      conda create -n piipod python=3.4

      # activate env
      source activate piipod;
  fi

  # install
  pip install --upgrade pip
  pip install -r requirements.txt

  # add configuration file if does not exist
  if [ ! -f "config.cfg" ];
    then cp default-config.cfg config.cfg
  fi

  echo "---

  [OK] Installation complete.
  Use 'make db' to create the database. Use 'make refresh' to DELETE the old
  database and recreate one using the new schema.
  "
}

function gs_check {
  echo '3 checks:'

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

  exit=`conda --version`
  if [ $? != 0 ];
    then echo '[Error] (Optional) Anaconda not found';
    else echo '[OK] Anaconda found'
  fi
}

function gs_activate {

  if [[ $CONDA == "true" ]];
    then
      # check for virtualenv
      if [ -d "env" ];
        then python3 -m venv env
      fi

      # activate virtualenv
      source env/bin/activate
    else
      # activate env
      source activate piipod;
    fi

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
