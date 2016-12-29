## Setter

### setter.py

Script to create SiLK IP address set and prefix map (pmap) files.

For command line usage info, see setter-help-output.txt. For an example of a
cli call to setter.py see setter-wrapper.sh.

setter.py consumes a specially-comment-decorated rwsetbuild text file and crafts 
a full compliment of hierarchical set and pmap files based on the user's 
configuration of the comments.

Expectation is, for example, to build out a tree of customer-coi-org-location
files, including customer.set, customer-coi.set, customer-coi-org.set,
customer-coi-org-location.set, and so on. The idea is that you can build
out any type of hierarchy that you need for your use case just by adding
comments associated with the hierarchy you want using hierarchy level 
indicators (L0, L1, L2, L3, etc).

The hierarchy levels are provided by you in a custom comment above the address
blocks associated with that level. The format for this comment is:

    #setter:Ln=short_name|Long Name - Amplifying Information

Examples:

    # ROOT - L0 not required

    #setter:L0=mycompanyname # leave off the long name to keep it out of the long pmap label

    # CUSTOMERS

    #setter:L1=customers # no long name here either

    #setter:L2=customer1name|Customer One Name
    #setter:L3=HQ|Headquarters - Washington DC
    10.10.10.0/24

    #setter:L2=customer2name|Customer Two Name
    #setter:L3=us_ops|US Operations Center
    10.20.20.0/24

    # SENSORS

    #setter:L1=sensors

    #setter:L2=sourcefire|SourceFire
    #setter:L3=us|US
    #setter:L4=west|West
    10.30.30.0/24
    #setter:L4=east|East
    10.30.40.0/24

    #setter:L2=niksun|Niksun
    #setter:L3=us|US
    #setter:L4=west|West
    10.40.30.0/24
    #setter:L4=east|East
    10.40.40.0/24


Setter.py also creates a tree of pmap files, although for most purposes,
a single inclusive pmap file is enough. Pmap files are built in long and 
short formats, with the long format containing a report/evidence-centric
proper name, and the short format containing an all lower case short name
to reserve netops/analyst working screen space.

    Example Long: Apple - Data Center East - Falls Church VA - Building 129
    Example Short: apple-dc_east-b129

There are some other utility scripts included.

### setter-wrapper.sh

setter-wrapper.sh is a simple bash wrapper to setter.py so that users
can establish their normally-desired setter.py options within the wrapper
and not have to type those in each time.

### is-this-my-ip.sh

is-this-my-ip.sh is a script that accepts various formats of IP address
info (text, comma separated text, text file, or set) as the input parameter
and runs the address(s) against your top-level/all-inclusive pmap file
created by setter.py to see if any of those addresses are in the pmap. If
so, it prints out the address and the customer (associated label in the pmap)
information.

### SiLK Installation required

setter.py depends upon SiLK executables being installed.

SiLK: https://tools.netsa.cert.org/silk/index.html 