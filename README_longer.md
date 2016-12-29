setter.README

Author: Chuck King

This file explains the configuration formats used by setter.py to build a hierarchy of set and pmap files that can be used by analysts and other scripts/tools.

It is very important to pay close attention to the setter levels, since each level will be used to create/load a tree node within setter.  If you incorrectly identify the appropriate node level, you can assign the level to the wrong place in the tree and end up with your information getting generated incorrectly. For example, if your intention is to create my_mssp > customers > apple > hq, but unintentionally place the apple level under my_mssp > sensors, you'd get my_mssp > sensors > apple > hq. For this reason, please use the -f and -t options during content file development/testing. These options will show you what files will get created and will print out the setter tree that gets loaded, so you can see where you are assigning nodes/netblocks. 
When either of these options are used, no files will be generated. Use these options, have a good look around, and then when satisfied your config file is correct, generate the output files.

To prevent having to add lots of 'end' tags, setter is designed to keep using all previously identified ancestor nodes/levels for all subordinate nodes/levels, unless the current ancestor node/levels have been explicitly modified. It is YOUR RESPONSIBILITY to make sure that when your addresses change to a new org, type, location, etc, (depending upon the hierarchy you design), that you add all appropriate setter labels to ensure the net blocks will get assigned to the correct location in the tree, which of course determines where that information will be deployed within the set and pmap file hierarchy. If you DO NOT do this, your sets/pmaps will be all sorts of incorrect.

In order for setter to parse the tags correctly, they must be included in the content configuration file in a specific format, as shown below.

Note: Because of a pmap dependency, no commas are allowed within the tag values.

### Root Node

- all trees will have a single root node at level 0
- if you want to name it, you may include a level 0 header as below
- if provided, the name will be included as part of your output file structure and short pmap names
- if not provided, a default root will be used internally and the level 0 node will not be part of your output file structure or short pmap names
- assuming you provide a level 0 as below, you would get files like my_mssp.set, my_mssp.short-pmap, my_mssp.long-pmap, my_mssp-customers.set, etc.
- assuming you did not provide a level 0 node, you would get files like customers.set, customers.short-pmap, customers.long-pmap, sensors.set, etc.
- notice that if you do not provide a root, you do not get a files aggregated at the root (e.g., no set file that includes all customer and sensor addresses) 
- #setter:L0=my_mssp

### Setter Comment Format

- #setter:Ln=name|Long Name
- #setter: is the Unix commented header / marker that setter.py looks for to process a level label
- Ln= determines the level number
- name determines the name used in the file names and short pmaps
- | is the delineator between name and long name, if long name is going to be provided
- Long Name is the proper name information that will become part of the long pmap description information
- Long Name is optional and when not provided, will not add to the composite long name derived from all the non-empty long names from the associated node to the root node. Normally it makes sense to leave the long name off of the root and simple/high-level grouping nodes (e.g., customers, sensors)

### Design The Hierarchy You Want

- include levels to create the tree hierarchy any way you want
- all levels/nodes may have net blocks or no net blocks, which means you can include levels/nodes simply to create the hierarchy you want reflected in the file names, short pmap names, and long pmap names
- when setter processes the content file, after it processes a level/node, if it finds net blocks, it will process them and add them to the most recent level processed.
- if no net blocks are encountered, it will simply continue processing levels and adding them to the tree
- below, the level 1 customer node will be added as a child to the L0 my_mssp node
- no long name is given because we don't want to add any maintenance/layout node info to the long pmap description
- #setter:L1=customers
- #setter:L2=apple

### Script Does Some Cleanup

- below, "HQ" will be checked for appropriate characters and lower cased by setter to produce "hq" since the name will be used as part of the file names and the short pmap names.
- below, we've included some location information within the long name description fragment
- #setter:L3=HQ|Headquarters - Cupertino CA

### Add Your Network Address Blocks

- below, we've finally added some net block information. This must be a dotted-quad IPv4 address and may contain a CIDR slash to represent the bitmap/network prefix.
- Setter will process x's, commas, and slashes included within the address. 
- Integer addresses and address ranges (e.g., 2.2.2.0-2.2.3.255) are not supported.  Neither are IPv6 addresses.
- Unlike SiLK sets, for both X's and O's, setter WILL attempt to determine the CIDR number for each net block when one is NOT provided.
- For example,
- 2.2.2.0 will be interpreted as 2.2.2.0/24
- 2.x.x.x will be interpreted as 2.0.0.0/8
- 2.x.3.4 will be interpreted as 2.0-255.3.4 (and will create 256 /32 net blocks)
- 2.2.2.3 will be interpreted as 2.2.2.3/32
- 2.x.0.0 will be interpreted as 2.0.0.0/8
- 2.2-3,5.3.3 will be interpreted as 2.2.3.3/32, 2.3.3.3/32, and 2.5.3.3/32

    2.2.2.0

    2.2.3-4,9.x
    
    2.3.6.21
    
    2.3.7.0/24

### Adding Additional Peer Levels

- when we want to add additional peer levels, we have to backtrack up the tree to provide levels/nodes as needed to ensure we attach the new levels/nodes to the correct hierarchical location.
- we want my_mssp > sensors, so we need to add a level 1 sensors node to make sure we don't add the below info to the customers area.
- #setter:L1=sensors
- oh, and we want to group sensors by type, so we'll add a level 2 node under sensors to reflect that these are SourceFire sensors.
- #setter:L2=sourcefire|SourceFire
- then we'll add a location and netblock
- #setter:L3=omaha|Omaha - Building 500 Room 312
- 10.40.50.0/24

### Files That Get Created

Example showing how a hierarchy of set/pmap files can be created:

With L0 provided:

    my_mssp.set
    my_mssp-customers.set
    my_mssp-customers-apple.set
    my_mssp-customers-apple-dc_west.set
    my_mssp-customers-apple-dc_east.set
    my_mssp-customers-walmart.set
    my_mssp-customers-walmart-hq.set
    my_mssp-sensors-sourcefire.set
    my_mssp-sensors-sourcefire-omaha.set
    my_mssp-sensors-niksun.set

Or, with no L0 provided:

    customers.set
    customers-apple.set
    customers-apple-dc_west.set
    ustomers-apple-dc_east.set
    customers-walmart.set
    customers-walmart-hq.set
    sensors.set
    sensors-sourcefire.set
    sensors-sourcefire-omaha.set
    sensors-niksun.set

And these pmap files could be created:

    my_mssp.short-pmap
    my_mssp-customers.short-pmap
    my_mssp-customers-apple.short-pmap
    my_mssp-customers-apple-dc_west.short-pmap
    my_mssp-customers-apple-dc_east.short-pmap
    my_mssp-customers-walmart.short-pmap
    my_mssp-customers-walmart-hq.short-pmap
    my_mssp-sensors-sourcefire.short-pmap
    my_mssp-sensors-sourcefire-omaha.short-pmap
    my_mssp-sensors-niksun.short-pmap

    my_mssp.long-pmap
    my_mssp-customers.long-pmap
    my_mssp-customers-apple.long-pmap
    my_mssp-customers-apple-dc_west.long-pmap
    my_mssp-customers-apple-dc_east.long-pmap
    my_mssp-customers-walmart.long-pmap
    my_mssp-customers-walmart-hq.long-pmap
    my_mssp-sensors-sourcefire.long-pmap
    my_mssp-sensors-sourcefire-omaha.long-pmap
    my_mssp-sensors-niksun.long-pmap

The short pmap files would produce the short tag names when used with pmap-capable tools (e.g., rwcut) and the long pmap files would produce the long names when used with pmap-capable tools. Short names are much easier to use during analysis since they take up less screen space, but long names may be more appropriate/useful for formal incident reporting and/or handing investigation evidence over to customers and/or law enforcement.

