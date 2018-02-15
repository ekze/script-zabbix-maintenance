#!/usr/bin/python
import json, sys, requests, time

# Fix for proxy env var
proxies = {'http': None,'https': None}
# Global variables for requests
headers = {'Content-Type': 'application/json-rpc'}
zabbix_host = 'zbx.spb.play.dc'
base_url = 'http://' + zabbix_host + '/api_jsonrpc.php'

# Get user
user = str(sys.argv[1])
# Password
password = str(sys.argv[2])
# Action
action = str(sys.argv[3])
# Hostname
hostname = str(sys.argv[4])


# Base function for request to Zabbix
# login - login to Zabbix
# logout - logout from Zabbix
# maintenance_list - list of all maintenances
# host_list - list of all hosts
# create - create maintenance period
# remove - remove maintenance period
def request(type, auth, name = None, uid = None, user = user, password = password):
    global proxies, headers, base_url
    # Set base JSON for request
    if type == 'login':
        data = json.loads('{"jsonrpc": "2.0", "method": "user.login", "params": { "user": "NULL", "password": "NULL" }, "id": 1, "auth": null }')
        data['params']['user'] = user
        data['params']['password'] = password
    if type == 'logout':
        data = json.loads('{"jsonrpc": "2.0", "method": "user.logout", "params": [], "id": 1, "auth": "NULL"}')
    if type == 'maintenance_list':
        data = json.loads('{"jsonrpc": "2.0", "method": "maintenance.get", "params": { "output": "extend", "selectGroups": "extend", "selectHosts": "extend", "selectTimeperiods": "extend"}, "auth": "NULL", "id": 1}')
    if type == 'host_list':
        data = json.loads('{ "jsonrpc": "2.0", "method": "host.get", "params": { }, "auth": "NULL", "id": 1 }')
    if type == 'create':
        data = json.loads('{"jsonrpc":"2.0","method":"maintenance.create","params":{"name":"NULL","active_since":0,"active_till":0,"hostids":[],"timeperiods":[{"timeperiod_type":0,"start_time":0,"period":5184000}]},"auth":"NULL","id":1}')
        data['params']['active_since'] = str(int(time.time()))
        data['params']['active_till'] = str(int(time.time()) + 31536000)
        data['params']['hostids'].append(uid)
        data['params']['name'] = 'automatic_' + name
    if type == 'remove':
        data = json.loads('{"jsonrpc":"2.0","method":"maintenance.delete","params":[],"auth":"NULL","id":1}')
        data['params'].append(uid)
    # Set auth token for non-login request
    if type != 'login':
        data['auth'] = auth
    # Dumps JSON to text
    data = json.dumps(data)
    try:
        data = requests.post(base_url, data = data, proxies=proxies, headers = headers).text
        data = json.loads(data)
        return data
    except:
        print 'Error to get response from Zabbix for ' + type


# Login to Zabbix
def login(user, password):
    data = request('login', None, None, None, user, password)
    try:
        auth = data['result']
        print 'Login to ' + zabbix_host + ': ok'
        return auth
    except:
        print "Problem with login"
        sys.exit(1)

# Logout from Zabbix
def logout(auth):
    data = request('logout', auth)
    try:
        if data['result'] == True:
            print 'Logout from ' + zabbix_host + ': ok'
        else:
            print 'Problem with logout'
    except:
        print 'Problem with logout'
        sys.exit(1)

# Get list of all maintenance
def maintenance_list(auth):
    data = request('maintenance_list', auth)
    try:
        print data
    except:
        print 'Problem with get list of maintenances'
        sys.exit(1)

# Get maintenance ID for Zabbix host
def maintenance_getid(auth, host):
    data = request('maintenance_list', auth)
    for maintenance in data['result']:
        if 'automatic' in maintenance['name']:
            for each in maintenance['hosts']:
                if host == each['host']:
                    return str(maintenance['maintenanceid'])
    return None

# Get host IDs for host with hostname like string
def host_get_ids(auth, host):
    data = request('host_list', auth)
    hosts = []
    names = set()
    for each in data['result']:
        if host in each['host']:
            info = { 'name': each['host'], 'hostid': each['hostid'] }
            hosts.append(info)
    print 'Get host IDs for ' + host + ':'
    for each in hosts: print str(each['name']) + ' - ' + str(each['hostid'])
    return hosts

# Create maintenance period for host with Zabbix hostname like string
def maintenance_create(auth, host):
    hosts = host_get_ids(auth, host)
    print '-----'
    if len(hosts) > 0:
        for each in hosts:
            x = request('create', auth, each['name'], each['hostid'])
            try:
                print 'Maintenance for ' + str(each['name']) + ' created: ' + str(x['result']['maintenanceids'][0])
                continue
            except:
                print 'Maintenance for ' + str(each['name']) + ' NOT created!!!'
                continue
    else:
        print 'No host found'

# Delete maintenance period for host with Zabbix hostname like string
def maintenance_remove(auth, host):
    hosts = host_get_ids(auth, host)
    print '-----'
    if len(hosts) > 0:
        for each in hosts:
            maintenanceid = maintenance_getid(auth, each['name'])
            if maintenanceid != None:
                x = request('remove', auth, each['name'], maintenanceid)
                try:
                    if x['result']['maintenanceids'][0] == maintenanceid:
                        print 'Maintenance for ' + each['name'] + ' removed'
                    else:
                        print 'Maintenance for ' + each['name'] + ' NOT removed!!!'
                except:
                    print 'Maintenance for ' + each['name'] + ' NOT removed!!!'
            else:
                print each['name'] + ' not in maintenance'
    else:
        print 'No host found'

# Work
auth = login(user,password)
print '-----'
if action == 'create':
    maintenance_create(auth, hostname)
if action == 'remove':
    maintenance_remove(auth, hostname)
print '-----'
logout(auth)