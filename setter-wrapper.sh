#!/bin/bash

SETTER_PY=/home/silkuser/setter/setter.py
WORKING_DIR=/home/silkuser/setter

IN_FILE=$WORKING_DIR/setter-content.txt
OUT_PATH=$WORKING_DIR
LOG_PATH=$WORKING_DIR

SET_LEVEL=10
PMAP_SHORT_LEVEL=0
PMAP_LONG_LEVEL=0

/usr/bin/env python $SETTER_PY \
     -i $IN_FILE \
     -o $OUT_PATH \
     -O \
     -l $LOG_PATH \
     -s $SET_LEVEL \
     -r $PMAP_SHORT_LEVEL \
     -p $PMAP_LONG_LEVEL
