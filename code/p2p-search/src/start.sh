#!/bin/bash

if [ $# -lt 1 ]
then
  echo ""
  echo "[WARNING] no superpeer connection. Please check README.txt"
  echo ""
  echo "Example of usage:  ./start.sh -alias leo -ip 130.161.158.167 -sp 130.161.158.167 -djp 9000"
  exit 0
fi

while [ $# -gt 0 ]
do
  case $1
  in
    -alias)
      alias=$2
      shift 2
    ;;
    
    -ip)
      hostaddress=$2
      shift 2
    ;;

    -sp)
      superpeeraddress=$2
      shift 2
    ;;


    -djp)
      djangoport=$2
      shift 2
    ;;

    *)
      echo ""
      echo "Usage: $0 -alias NICKNAME -ip IPADDRESS -sp SPIPADDRESS -djp PORT"
      echo "  e.g. $0 -alias leo -ip 130.161.158.167 -sp 130.161.158.167 -djp 9000"
      echo ""
      echo "-alias NICKNAME"
      echo "     put here your nickname"
      echo "-ip IPADDRESS"
      echo "     your host IP address"
      echo "-sp: SIPADDRESS"
      echo "     superPeer IP address"
      echo "-djp: PORT"
      echo "     the port on localhost in which django run"
      echo ""
      shift 1
    ;;
  esac
done

PYTHONPATH=$PYTHONPATH:`pwd`
export PYTHONPATH

python mysite/manage.py runserver $djangoport&
djangoPID=$!

python main/main.py alias=$alias ip=$hostaddress sip=$superpeeraddress

kill -TERM $djangoPID
