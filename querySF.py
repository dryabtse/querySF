from simple_salesforce import Salesforce
import collections
import argparse
import keyring
import sys
import os

PROCESS_KV = True

# Credentials
URL='https://mongodb.my.salesforce.com'
TOKEN_SECRET_NAME = 'SF_TOKEN'
TOKEN = keyring.get_password("system", TOKEN_SECRET_NAME)
USERNAME = 'user.name@mongodb.com'
PASSWORD = keyring.get_password("system", USERNAME)

# SOQL query parts
QUERY_FIELDS = "CaseNumber, Status, Priority, Owner__c, Subject"
QUERY_PREFIX = "SELECT " + QUERY_FIELDS + " FROM Case WHERE CaseNumber IN ("
QUERY_STATUS_FILTER = "AND Status IN ("
QUERY_SUFFIX = "ORDER BY CaseNumber"

class Status():
    OPN = "'Open'"
    CSD = "'Closed'"
    WFC = "'Waiting for Customer'"
    WFD = "'Waiting for Development'"
    INP = "'In Progress'"
    RES = "'Resolved'"
    HLD = "'On Hold'"
    ALL = OPN + ", " + CSD + ", " + WFC + ", " + WFD + ", " + INP + ", " + RES + ", " + HLD

# Recursively print the resultset ObjectDict
def recPrintOdict(odict, indent=0):
    prefix = ''
    if indent > 0:
        prefix = '└'
    for i in range(0,indent):
        prefix = prefix + '-'

    for k,v in odict.items():
        k,v = keyValueProcessor(k,v)
        if(isinstance(v, collections.OrderedDict)):
            print(prefix + '+', k, ': ')
            recPrintOdict(v, indent+2)
        else:
            print(prefix + '-', k, ': ', v)

def printQueryResults(res):
    if 'records' in res:
        records = res['records']
        if len(records) > 0:
            for r in records:
                recPrintOdict(r)
                print("\n=============================================================================\n")

# Some of the object keys retrieved from SF have ugly names, this function can be used to replace them with 
# something more sensible
def keyValueProcessor(k, v):
    if PROCESS_KV == False:
        return k,v

    vNew = ""
    kNew = ""
    if k == "Owner__c":
        kNew = "Owner"
        # Construct the owner's first name + last name and truncate the rest
        for word in v.split(" "):
            if word == "[<a":
                break
            if(len(vNew) > 0):
                vNew = vNew + " " + word
            else:
                vNew = vNew + word
    else:
        vNew = v
        kNew = k
    
    return kNew,vNew

# Check if the ticket number is matching the expected pattern
def sanitizeTicketArgument(tkArg):
    good = True
    if (len(tkArg) != 8):
        good = False
    for c in tkArg:
        if (c.isalpha()):
            good = False

    return good
        
# To process the command line arguments
def processArguments():
    parser = argparse.ArgumentParser(description='Query tickets information from SalesForce')
    parser.add_argument('tickets', metavar='T', type=str, nargs='+', help='8-digit ticket number')
    parser.add_argument('--status', metavar='S', type=str, nargs=1, help='status filter; accepted values: OPN, CSD, WFC, WFD, INP, RES, ALL', default=argparse.SUPPRESS)
    args = parser.parse_args()

    inClause = ""
    statusFilter = ""

    for t in args.tickets:
        if sanitizeTicketArgument(t) == False:
            print("ERROR: The specified argument does not appear to be a ticket number: %s \n" % t)
            parser.print_help()
            sys.exit()

        if (len(inClause) == 0):
            inClause = "'" + t + "'"
        else:
            inClause = inClause + ", '" + t + "'"

    if "status" in args:
        if len(args.status) != 1:
            print("ERROR: A single status argument is expected, found %s" % len(args.status)) 
            parser.print_help()
            sys.exit()

        statusFilter = statusFilter + statusSelector(args.status[0])

        if statusFilter == "Invalid":
            print("ERROR: An incorrect status value has been specified: %s" % args.status[0])
            parser.print_help()
            sys.exit()

    return inClause, statusFilter

# Status selector for --status option
def OPN():
    return Status.OPN
def CSD():
    return Status.CSD
def INP():
    return Status.INP
def WFC():
    return Status.WFC
def WFD():
    return Status.WFD
def RES():
    return Status.RES
def HLD():
    return Status.HLD
def ALL():
    return Status.ALL

def statusSelector(input):
    switcher = {
        "OPN": OPN,
        "CSD": CSD,
        "INP": INP,
        "WFC": WFC,
        "WFD": WFD,
        "RES": RES,
        "HLD": HLD,
        "ALL": ALL
    }
    func = switcher.get(input, lambda: "Invalid")
    return func()

def main():
    
    tickets,statuses = processArguments()

    # SOQL query assembly
    query = QUERY_PREFIX + tickets + ") "
    if len(statuses) > 0:
        query = query + QUERY_STATUS_FILTER + statuses + ") " + QUERY_SUFFIX

    try:
        sf = Salesforce(instance_url=URL, username=USERNAME, password=PASSWORD, security_token=TOKEN)
        result = sf.query(query)
    except:
        print("FATAL ERROR: SalesForce could not be run: ", sys.exc_info()[0])
        raise

    if result['done'] == True:
        printQueryResults(result)
    else:
        print("The SalesForce query failed to fetch any results.")

if __name__ == '__main__':
    main()
