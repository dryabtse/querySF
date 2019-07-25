# querySF
A short POC on how to query support tickets in SalesForce from CLI

### Requirements
- You will need to generate an API token for your account in SalesForce
- The script expects the token and the user password to be stored and retrieved using [keyring](https://pypi.org/project/keyring/) (supports Keychain as a backend on OSX)

```
$ python3 querySF.py  -h
usage: querySF.py [-h] [--status S] T [T ...]

Query tickets information from SalesForce

positional arguments:
  T           8-digit ticket number

optional arguments:
  -h, --help  show this help message and exit
  --status S  status filter; accepted values: OPN, CSD, WFC, WFD, INP, RES, ALL
```
