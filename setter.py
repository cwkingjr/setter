#!/usr/bin/env python

# author = Chuck King

"""
This software reads specially commented set text files and generates
both set and pmap files.
"""

# Using old style exception declarations because it works with python 2.4.3
# Instead of "except IOError as e", using "except IOError, e"

import datetime
import errno
import logging, logging.handlers
import sys
import optparse
import os
from os.path import expanduser
import subprocess

class Netblock(object):
    """Holds network address block, cidr mask, and pmap name/description info"""
    def __init__(self, startAddress, cidr, pmapName=None, pmapShortName=None):
        self.startAddress = startAddress
        self.cidr = cidr
        self.pmapName = pmapName
        self.pmapShortName = pmapShortName
        
    def getStartAddress(self):
        return self.startAddress

    def getCidr(self):
        return self.cidr

    def getPmapName(self):
        return self.pmapName

    def getPmapShortName(self):
        return self.pmapShortName

class Node(object):
    """Tree node that holds level info, name, long name, local netblocks, and parent/children refs"""
    def __init__(self, name, longName, parent=None):
        self.name = name
        self.longName = longName
        self.parent = parent
        self.children = []
        self.netblocks = []
        self.filename = ""
        self.pmapname = ""

        if parent is None:
            self.level = 0 # root
        else:
            self.parent.children.append(self)
            self.level = self.parent.level + 1

    def addChild(self, child):
        self.children.append(child)
        child.parent = self
        child.level = self.level + 1

    def addNetblock(self, netblock):
        netblock.pmapName = self.getPmapName() 
        netblock.pmapShortName = self.getFileName() 
        self.netblocks.append(netblock)

    def getName(self):
        return self.name

    def setName(self, mystr):
        self.name = mystr

    def setLongName(self, mystr):
        self.longName = mystr

    def getFileName(self, joinstr='-'):
        if self.filename == "":
            filenamelist = [] 
            self.fillFileNameList(filenamelist)
            if len(filenamelist):
                filenamelist.reverse()
            self.filename = joinstr.join(filenamelist)
        return self.filename 

    def fillFileNameList(self, filenamelist):
        # file name will consist of a concatenation of short names
        # between this node and all parent nodes with short names

        # if not unlabelled root
        if self.name != 'root':
            # if not empty
            if self.name != "":
                filenamelist.append(self.name)
            # walk toward root
            if self.level:
                self.parent.fillFileNameList(filenamelist)

    def getPmapName(self, joinstr=' - '):
        if self.pmapname == "":
            pmapnamelist = [] 
            self.fillPmapNameList(pmapnamelist)
            if len(pmapnamelist):
                pmapnamelist.reverse()
            self.pmapname = joinstr.join(pmapnamelist)
        return self.pmapname 

    def fillPmapNameList(self, pmapnamelist):
        # pmap name will consist of a concatenation of pmap names
        # between this node and all ancestor nodes with long names

        # if not unlabelled root
        if self.name != 'root':
            # if not empty
            if self.longName != "":
                pmapnamelist.append(self.longName)
            # walk toward root
            if self.level:
                self.parent.fillPmapNameList(pmapnamelist)

    def getNetblocks(self, netblocklist, localOnly=False):
        # get our netblocks
        if len(self.netblocks):
            netblocklist.extend(self.netblocks) 
        # get our children's netblocks
        if not localOnly: 
            for child in self.children:
                child.getNetblocks(netblocklist, localOnly)
        #logger.debug("At end of getnetblocks call for node %s, netblocklist has %d length" % (self.getName(),len(netblocklist)))


def main():

    # Since these are declared in main, have to explicitly add them to the global symbol table
    # so they can be found by the other methods

    # script version = major.minor.date-in-YYYYMMDD
    global version
    version = '0.6.20130529'

    # error logging object
    global logger

    # max node depth we'll allow the tree to grow
    global MAX_DEPTH
    MAX_DEPTH = 10

    global options, args
    (options, args) = processOptions()

    global LOG_FILENAME
    if options.logpath:
        mypath = options.logpath
    else:
        # home folder
        mypath = expanduser("~")
    LOG_FILENAME = "%s/%s" % (mypath, 'setter.log') 

    # we'll be reading in one set.txt file
    global SET_TXT_FILE
    if options.settxtfile:
        # expecting full path including file name
        SET_TXT_FILE = options.settxtfile
    else:
        # home folder
        mypath = expanduser("~")
        SET_TXT_FILE = "%s/%s" % (mypath, 'setter-content.txt') 
    checkFile(SET_TXT_FILE)

    # where are we in the tree
    global currentnode
    global root
    root = Node("root","")
    currentnode = root

    # make sure there's only one level 0 in configs if provided and it comes first
    global levelzeroingested
    levelzeroingested = False
    global levelentryingested
    levelentryingested = False
    
    # track lines in set.txt file for error reporting
    global linecounter
    linecounter = 0

    ########### 
    ##  Logger set up

    # Set up local stdin and file log destinations
    logger = logging.getLogger(LOG_FILENAME)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=10)
    # We'll leave the info logged to file at debug and alter the command line based upon cli options
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    if options.debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    # create formatters and add them to the handlers
    # you can use the same one but I didn't want the datetime on the console
    chformatter = logging.Formatter('%(levelname)-8s %(message)s')
    fhformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(chformatter)
    fh.setFormatter(fhformatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    ##
    ##########

    logger.debug("=================================================================================")
    logger.debug("========================== STARTING NEW SCRIPT RUN ==============================")
    logger.debug("=================================================================================")

    logger.info("Check the log file at %s for debug-level logging info" % LOG_FILENAME)

    readSetTextFile()

    # prints out the tree that gets loaded as a quick check
    if options.printtree:
        printTree(root, options.setlevel)

    # print out the file names that will be created as quick check
    if options.printfilenames:
        printFileNames(root, options.setlevel)

    if options.printtree or options.printfilenames:
        # these are for testing the context file so don't go any further
        sys.exit(1)

    # where we will store the output files
    if options.outpath:
        outpath = options.outpath
    else:
        # home folder
        outpath = expanduser("~")

    if options.nooutdate:
        outpath = "%s/%s" % (outpath, 'setter-out') 
    else:
        # append a date-centric folder to the path
        mydate = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        outpath = "%s/%s-%s" % (outpath, mydate, 'setter-out') 

    mkdir_p(outpath)

    if not options.noset:
        createSetFiles(root, outpath, options.setlevel)

    if not options.nolongpmap:
        createPmapFiles(root, outpath, options.pmaplonglevel)

    if not options.noshortpmap:
        # create with short names
        createPmapFiles(root, outpath, options.pmapshortlevel, True)

def createSetFiles(node, filepath, gotolevel):
    if node.level <= gotolevel: 
        setinfo = "#\n"
        filename = "%s/%s.set" % (filepath, node.getFileName())
        netblocklist = []
        node.getNetblocks(netblocklist)
        for item in netblocklist:
            setinfo = setinfo + "%s/%d\n" % (item.startAddress, item.cidr)
        args = ["rwsetbuild", "stdin", filename]
        proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        proc.communicate(setinfo)
        proc.wait()
        if proc.returncode:
            raise RuntimeError("Could not build IP set %s" % filename)
        for child in node.children:
            createSetFiles(child, filepath, gotolevel)

def createPmapFiles(node, filepath, gotolevel, shortname=False):
    if node.level <= gotolevel: 
        pmapinfo = "map-name setter\nmode ip\n"
        nodefilename = node.getFileName()
        if shortname:
            filename = "%s/%s.short-pmap" % (filepath, nodefilename)
        else:
            filename = "%s/%s.long-pmap" % (filepath, nodefilename)
        netblocklist = []
        node.getNetblocks(netblocklist)
        # sort this by cidr with most granular on bottom
        for item in sorted(netblocklist, key=lambda block: block.cidr):
            if shortname:
                pmapinfo = pmapinfo + "%s/%d %s\n" % (item.startAddress, item.cidr, item.pmapShortName)
            else:
                pmapinfo = pmapinfo + "%s/%d %s\n" % (item.startAddress, item.cidr, item.pmapName)
        args = ["rwpmapbuild", "--input-file", "stdin", "--output-file", filename]
        proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        proc.communicate(pmapinfo)
        proc.wait()
        if proc.returncode:
            raise RuntimeError("Could not build pmap %s" % filename)
        for child in node.children:
            createPmapFiles(child, filepath, gotolevel, shortname)

def printTree(node, gotolevel):
    if node.level <= gotolevel: 
        mylevel = " "*2*node.level
        print "%sL%d %s : %s" % (mylevel, node.level, node.name, node.longName)
        netblocklist = []
        node.getNetblocks(netblocklist, True)
        for item in netblocklist:
            print "%s%s/%d %s" % (mylevel + "   ", item.startAddress, item.cidr, item.pmapName)
        for child in node.children:
            printTree(child, gotolevel)

def printFileNames(node, gotolevel):
    if node.level <= gotolevel: 
        print "%s" % (node.getFileName())
        for child in node.children:
            printFileNames(child, gotolevel)

def checkPathExists(path):
    if not os.path.exists(path):
        logger.error("Path provided does not exist: %s" % (path))
        sys.exit(1)

def checkDirectory(path):
    checkPathExists(path)
    if not os.path.isdir(path): 
        logger.error("Path provided is not a directory: %s" % (path))
        sys.exit(1)

def checkFile(path):
    checkPathExists(path)
    if not os.path.isfile(path): 
        logger.error("File path provided is not a file: %s" % (path))
        sys.exit(1)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError, exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def isIPv4Address(txt):
    if not '.' in txt:
        return False 
    quads = txt.split('.')
    if len(quads) != 4:
        return False
    for quad in quads:
        if not 0 <= int(quad) <= 255:
            return False
    return True

def tryOpen(path,mode):
    # refactoring out a lot of repeated I/O exception wrapping
    # returns reference to file object if all goes well
    if mode == 'r':
        modetext = 'read'
    elif mode == 'w':
        modetext = 'write'
    else:
        logger.error("TryOpen requires a mode of r (read) or w (write) for file %s" % (path))
        sys.exit(1)
    try:
        return open(path,mode)
    except IOError, e:
        logger.error("Exception opening file for %s: %s" % (modetext,str(e)))
        sys.exit(1)

def tryClose(fileref):
    # refactoring out a lot of repeated I/O exception wrapping
    try:
        file.close(fileref)
    except IOError, e:
        logger.error("Exception closing file: %s" % (str(e)))
        sys.exit(1)

def getCleanName(mystr):
    # name needs to be cleaned up as needed to ensure it'll work as part of a file name
    name = mystr.strip().lower()
    newname = ""
    goodchars = "abcdefghijklmnopqrstuvwxyz0123456789-_."
    # remove non-desired chars
    for char in name:
        if char in goodchars:
            newname = newname + char
        else:
            newname = newname + '_'
            logger.debug("Line %d: Replacing bad file name character '%s' with '_': %s" % (linecounter,char,name))

    newname = newname.strip()

    if mystr != newname:
        logger.info("Line %d: Replaced level name '%s' with '%s' for use as part of file name" % (linecounter,mystr,newname))

    return newname

def checkForInvalidPmapChars(mystr):
    mystr = mystr.strip()
    # pmap's won't allow certain chars so we have to check for those
    # according to rwpmapbuild man a comma is actually allowed but will break some usage
    badchars = ","
    for char in mystr:
        if char in badchars:
            # try/except needed here because this method can be called from options area before logger is set up
            try:
                logger.error("Line %d: Found '%s' character which is not allowed as part of pmap description/text" % (linecounter,char))
            except NameError:
                msg = "Sorry, '%s' character is not allowed as part of -j/--pmap-joiner string" % (char)
                print "ERROR: %s" % msg 
            sys.exit(1)
    return mystr

def getCleanLevel(mystr):
    # this will be the node level
    mystr = mystr.strip()
    if mystr.startswith('L'):
        # grab everything after the L
        mystr = mystr[1:]
    else:
        logger.error("Line %d: The setter level config does not start with L; e.g., Ln=shortname: %s" % (linecounter,mystr))
        sys.exit(1)
    mynum = int(mystr)
    # check to see that it's a positive integer in a reasonable range
    if not 0 <= mynum <= 100:
        logger.error("Line %d: The setter level doesn't appear to be an integer (0-100): %s" % (linecounter,mystr))
        sys.exit(1)
    return mynum

def getConfigLineTokens(setterline):
    #setter:L1=someshortname|Some Long Name
    # idea is that short name will be lower cased, and short, and used in set/pmap file names,
    # where long name will be proper cased, can be longer, and will become part of 
    # the PMAP text/description when concatenated with the long name from other tree nodes above it.

    # split at the setter header colon
    tokens = setterline.split(':')
    if len(tokens) != 2:
        logger.error("Line %d: Problem parsing setter configuration; should be one and only one colon: %s" % (linecounter,setterline))
        sys.exit(1)

    # process the line part after #setter:
    sections = tokens[1].split('|')
    if len(sections) != 2:
        logger.info("Line %d: Processed config entry with no long name: %s" % (linecounter,setterline))

    # do level and name (both required)
    parts = sections[0].split('=')
    if len(parts) != 2:
        logger.error("Line %d: Problem parsing first section of setter config entry; requires Ln=shortname: %s" % (linecounter,setterline))
        sys.exit(1)

    level = getCleanLevel(parts[0]) 
    name = getCleanName(parts[1])

    # do the long name if there is one
    # it's not required and would be empty if they don't want the long name
    # for this node to show up in the concatenated pmap name
    if len(sections) > 1:
        longname = checkForInvalidPmapChars(sections[1])
    else:
        longname = ""

    return (level,name,longname)

def loadNumSet(addressElement,myset):
    # silk allows addresses to include commas and ranges
    # so we have to break those out into quad sets to iterate later
    if ',' in addressElement or '-' in addressElement:
        # 2.3.4.5,7,9-21
        # if there aren't any commas, this will still return a list of one element
        parts = addressElement.split(',')
        for part in parts:
            if '-' in part:
                # add numbers for range
                myrange = part.split('-')
                mystart = int(myrange[0])
                myend = int(myrange[1])
                i = mystart
                while i <= myend:
                    myset.add(i)
                    i = i + 1
            else:
                # add comma'd number
                myset.add(part)
    else:
        # just a single number
        myset.add(addressElement)

def getConfigLineNetblocks(line):
    # check the config line for netblock info, tweak as needed, and
    # return list of netblock objects
    # if the line includes commas or ranges then we have to build
    # a netblock for each different IP address, so we return a list
    # of netblocks to meet all contingencies
    netblocklist = []
    cidr = ""

    # temp containers
    # storing in sets so we can capture all the variants presented as
    # single numbers, comma-delimited sets, and range-delimited sets
    anums = set()
    bnums = set()
    cnums = set()
    dnums = set()

    myline = line.strip()
    if '#' in myline:
        # some address block entries may contain comments within the line
        # and may contain whitespace between the address and the # symbol
        # e.g., 2.2.2.0/24      # some random comment
        myline = myline.split('#')[0].strip()

    # if has cidr provided, grab that
    if '/' in myline:
        tokens = myline.split('/')
        address = tokens[0]
        cidr = int(tokens[1])
    else:
        address = myline

    quads = address.split('.')
    a = quads[0]
    b = quads[1]
    c = quads[2]
    d = quads[3]

    # assigning character list to variable simply to save typing in checks below
    # zero
    z = ['0']
    # lower or upper x
    x = ['x','X']
    # either
    xz = ['x','X','0']

    # try to determine cidr when not given
    if '0' in quads:
        if a in z:
            logger.error("Line %d: 0 is not allowed in IPv4 address first quad; %s" % (linecounter,line))
            sys.exit(1)
        # don't change the cidr if it was assigned within the file
        if cidr == "": 
            if b in z and c in xz and d in xz:
                cidr = 8 
                c = '0'
                d = '0'
            elif c in z and d in xz:
                cidr = 16
                d = '0'
            elif d in z:
                cidr = 24

    # change x's to 0's for pmap
    if 'x' in quads or 'X' in quads:
        if a in x:
            # note that rwsetbuild allows x.x.x.255 with no cidr listed, which will produce
            # a set of all addresses ending in 255.  To convert to pmaps, we need a cidr,
            # so I am treating 0's like x's when it comes to guessing cidr maps.  For this 
            # reason, I'm also not allowing a quad x's.
            logger.error("Line %d: x is not allowed in IPv4 address first quad; %s" % (linecounter,line))
            sys.exit(1)

        """
        if there's also an x all the way down the quads then just convert them to 0's and don't
        worry about translating them to ranges but if there's an x somewhere up the quads without
        x's all the way down the quads, we'll have to translate them to 0-255 ranges,
        e.g., 2.x.3.4 would need to be 2.0-255.3.4
        """

        if b in x:
            if c in xz and d in xz:
                if cidr == "":
                    cidr = 8 
                b = '0'
                c = '0'
                d = '0'
            else:
                b = "0-255"

        if c in x:
            if d in xz:
                if cidr == "":
                    cidr = 16
                c = '0'
                d = '0'
            else:
                c = '0-255'

        if d in x:
            if cidr == "":
                cidr = 24
            d = '0'

    if cidr == "":
        cidr = 32

    if not 7 < cidr <= 32:
        logger.error("Line %d: Address block with slash has inappropriate CIDR notation, expecting 8-32; %s" % (linecounter,line))
        sys.exit(1)

    loadNumSet(a,anums)
    loadNumSet(b,bnums)
    loadNumSet(c,cnums)
    loadNumSet(d,dnums)

    for a in anums:
        for b in bnums:
            for c in cnums:
                for d in dnums:
                    # create a netblock and load it up
                    address2 = "%d.%d.%d.%d" % (int(a),int(b),int(c),int(d)) 
                    #print "a.b.c.d/cidr is: %s/%d" % (address2,cidr)
                    if not isIPv4Address(address2):
                        logger.error("Line %d: Derived address block is not a dotted-quad IPv4 address; %s" % (linecounter,line))
                        sys.exit(1)
                    netblock = Netblock(address2, cidr)
                    netblocklist.append(netblock)

    return netblocklist

def readSetTextFile():
    setFile  = tryOpen(SET_TXT_FILE, 'r')

    global currentnode
    global linecounter
    global levelentryingested
    global levelzeroingested
    global root

    for line in setFile:
        linecounter += 1
        
        # ignore blank lines
        if len(line.strip()) == 0:
            continue

        # chop off any newlines and beginning/ending white space
        line = line.strip()

        if line.startswith('#') and not line.startswith('#setter:'):
            logger.debug("Line %d: Skipping comment: %s" % (linecounter,line))
            continue

        if line.startswith('#setter:'):
            # load the config info

            logger.debug("Line %d: Found setter config line: %s" % (linecounter,line))

            level,name,longname = getConfigLineTokens(line)

            # change the info on the root node
            # make sure we only have one level zero entry and it is the first entry
            # so we can rename root before populating other nodes
            if level == 0:
                if levelzeroingested:
                    logger.error("Line %d: You may only include one level 0 entry and it must be the first setter config entry: %s" % (linecounter,line))
                    sys.exit(1)
                else:
                    levelzeroingested = True

                if levelentryingested:
                    logger.error("Line %d: If you include a level 0 entry it must be the first setter config entry: %s" % (linecounter,line))
                    sys.exit(1)
                else:
                    levelentryingested = True
        
                root.setName(name)
                root.setLongName(longname)
                continue

            # cover non-zero ingests and the case where no level zero included in configs
            if levelentryingested == False:
                levelentryingested = True

            # asking to go down more than one node
            if (level - currentnode.level) > 1:
                logger.error("Line %d: Inconsistent level assignment; e.g., L3 being assigned before L2: %s" % (linecounter,line))
                sys.exit(1)
                 
            # asking to add child
            if level == currentnode.level + 1: 
                # create a node and add it as child
                child = Node(name,longname,currentnode)
                currentnode = child

            # asking to add sibling
            elif level == currentnode.level: 
                currentnode = currentnode.parent
                # create a node and add it as child
                child = Node(name,longname,currentnode)
                currentnode = child

            # asking to add node higher in the tree 
            elif level < currentnode.level:
                while (level - 1) < currentnode.level:
                    currentnode = currentnode.parent
                # create a node and add it as child
                child = Node(name,longname,currentnode)
                currentnode = child

        else:
            # build netblock instance from address info
            # some lines will need to be converted into multiple netblocks
            # e.g., 2.3-4.2.2 would produce 2 netblocks

            logger.debug("Line %d: Found address line of %s" % (linecounter, line))

            blocks = getConfigLineNetblocks(line)
            for block in blocks:
                logger.debug("Line %d: Adding netblock %s/%d to node %s" % (linecounter,
                    block.getStartAddress(), block.getCidr(), currentnode.getPmapName(options.pmapconcat)))
                currentnode.addNetblock(block)

    tryClose(setFile)

def processOptions():
    """ process commandline options """
    usage = """usage: ./%prog [options]
    use -h for help / option descriptions 
    """

    parser = optparse.OptionParser(usage)
    parser.add_option("-c", "--pmap-concat", dest="pmapconcat", help="""Allows default pmap name concatenation string of ' - ' to be overridden.  A node's pmap name is derived from a reversed concatenation of the node's non-empty long name and each ancestor node's non-empty long name, separated by this concatenation string.  E.g., Grandparent - Parent - Child""")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="""Optional.  Dump debug (vice info) output to the command line interface.  Debug-level output is automatically logged to rotating log files and is far easier to review there.""")
    parser.add_option("-f", "--print-file-names", action="store_true", dest="printfilenames", help="""Optional.  Print the names of files that would be created (truncates if set-level option provided).  This is meant for use to check your setter-context file configuration.  When used, setter will terminate before creating the real files.""")
    parser.add_option("-i", "--in-file", dest="settxtfile", help="""Setter text file to process. Default is ~/setter-content.txt.""")
    parser.add_option("-l", "--log-path", dest="logpath", help="""Path where you want setter.log file written. Default is your home dir.""")
    parser.add_option("-o", "--out-path", dest="outpath", help="""Path where you want files written. Default is your home dir inside a date-setter folder.""")
    parser.add_option("-O", "--no-out-date", action="store_true", dest="nooutdate", help="""Do not include the processed date in the folder name where output files are written.""")
    parser.add_option("-p", "--pmap-long-level", dest="pmaplonglevel", help="""Level restriction used when creating long-description pmap files.  Default is all levels.  E.g., -p 1 would create a long pmap file for level 0 and each level 1 entry.  Every level file includes records for itself and all descendant levels.""")
    parser.add_option("-P", "--no-long-pmap", action="store_true", dest="nolongpmap", help="""Do not create long (proper name) pmap files.""")
    parser.add_option("-r", "--pmap-short-level", dest="pmapshortlevel", help="""Level restriction used when creating short-description pmap files.  Default is all levels.  E.g., -r 1 would create a short pmap file for level 0 and each level 1 entry.  Every level file includes records for itself and all descendant levels.""")
    parser.add_option("-R", "--no-short-pmap", action="store_true", dest="noshortpmap", help="""Do not create short (file-name-based) pmap files.""")
    parser.add_option("-s", "--set-level", dest="setlevel", help="""Level restriction used when creating set files.  Default is all levels.  E.g., -s 3 would create a set file for level 0 and each level 1, 2, and 3 entry.  Every level file includes records for itself and all descendant levels.""")
    parser.add_option("-S", "--no-set", action="store_true", dest="noset", help="""Do not create set files.""")
    parser.add_option("-t", "--print-tree", action="store_true", dest="printtree", help="""Optional.  Print a text representation of the tree of nodes that will be loaded from setter-context.txt (truncates if set-level option provided).  This is meant for use to check your setter-context file configuration.  When used, setter will terminate before creating the real files.""")
    parser.add_option("-v", "--version", action="store_true", dest="version", help="""Indicates script version""")
    
    (options, args) = parser.parse_args()

    if options.version:
        sys.stdout.write("Script version: %s\n" % (version))
        sys.exit(1)

    if options.setlevel:
        # make sure this is within some reasonable integer level
        try:
            options.setlevel = int(options.setlevel)
        except ValueError, e:
            print("Exception: set-level option requires an integer value: you provided '%s'" % (options.setlevel))
            sys.exit(1)
        if not 0 <= options.setlevel <= MAX_DEPTH:
            print("The set-level option value, when used, must be between 0-%d: you provided '%s'" % (options.setlevel, MAX_DEPTH))
            sys.exit(1)
    else:
        options.setlevel = MAX_DEPTH 

    if options.pmaplonglevel:
        # make sure this is within some reasonable integer level
        try:
            options.pmaplonglevel = int(options.pmaplonglevel)
        except ValueError, e:
            print("Exception: pmap-long-level option requires an integer value: you provided '%s'" % (options.pmaplonglevel))
            sys.exit(1)
        if not 0 <= options.pmaplonglevel <= MAX_DEPTH:
            print("The pmap-long-level option value, when used, must be between 0-%d: you provided '%s'" % (options.pmaplonglevel, MAX_DEPTH))
            sys.exit(1)
    else:
        options.pmaplonglevel = MAX_DEPTH 

    if options.pmapshortlevel:
        # make sure this is within some reasonable integer level
        try:
            options.pmapshortlevel = int(options.pmapshortlevel)
        except ValueError, e:
            print("Exception: pmap-short-level option requires an integer value: you provided '%s'" % (options.pmapshortlevel))
            sys.exit(1)
        if not 0 <= options.pmapshortlevel <= MAX_DEPTH:
            print("The pmap-short-level option value, when used, must be between 0-%d: you provided '%s'" % (options.pmapshortlevel, MAX_DEPTH))
            sys.exit(1)
    else:
        options.pmapshortlevel = MAX_DEPTH 

    if not options.pmapconcat:
        options.pmapconcat = ' - '
    else:
        options.pmapconcat = checkForInvalidPmapChars(options.pmapconcat)

    return (options, args)

if __name__ == "__main__":
    main()
