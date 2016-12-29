#!/bin/bash

#set to location of your comprehensive pmap file created via setter.py
PMAP_FILE=/home/silkuser/setter/setter-out/myL0name.long-pmap

if [ "$#" -lt "1" ]; then
    echo "Please provide IP address parameter; this can be a single address, comma "
    echo "separated address list, file with a list of addresses, or a set file."
    echo "Example: $0 2.2.2.2"
    echo "Example: $0 2.2.2.2,3.3.3.3,4.4.4.4"
    echo "Example: $0 /path/to/my/addresses.txt"
    echo "Example: $0 /path/to/file.set"
    exit 1
fi

ADDRESS=$1

# check to see if this is a file name
if [ -f $ADDRESS ]; then

    # if file, see if it's a set file
    FILE_TYPE=`rwfileinfo --fields=1 --no-titles $ADDRESS` 
    #set file type is FT_IPSET(0x1d)
    if [ $FILE_TYPE == "FT_IPSET(0x1d)" ]; then
        # read the addresses from the set file
        # this will be pretty chatty
        rwsetcat $ADDRESS | rwtuc --fields=sip | rwcut --no-columns --pmap-file=setter:$PMAP_FILE --fields=sip,src-setter
    else
        # read the text file of addresses
        cat $ADDRESS | rwtuc --fields=sip | rwcut --no-columns --pmap-file=setter:$PMAP_FILE --fields=sip,src-setter
    fi
else
    # convert any commas to newlines to get a unix list/array
    IP_LIST=$(echo "$ADDRESS" | tr "," "\n")
    for IP in $IP_LIST; do
        echo $IP | rwtuc --fields=sip | rwcut --no-columns --pmap-file=setter:$PMAP_FILE --fields=sip,src-setter
    done
fi
