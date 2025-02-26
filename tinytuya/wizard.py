# TinyTuya Setup Wizard
# -*- coding: utf-8 -*-
"""
TinyTuya Setup Wizard Tuya based WiFi smart devices

Author: Jason A. Cox
For more information see https://github.com/jasonacox/tinytuya

Description
    Setup Wizard will prompt the user for Tuya IoT Developer credentials and will gather all
    registered Device IDs and their Local KEYs.  It will save the credentials and the device
    data in the tinytuya.json and devices.json configuration files respectively. The Wizard
    will then optionally scan the local devices for status.

    HOW to set up your Tuya IoT Developer account: iot.tuya.com:
    https://github.com/jasonacox/tinytuya#get-the-tuya-device-local-key

Credits
* Tuya API Documentation
    https://developer.tuya.com/en/docs/iot/open-api/api-list/api?id=K989ru6gtvspg
* TuyaAPI https://github.com/codetheweb/tuyapi by codetheweb and blackrozes
    The TuyAPI/CLI wizard inspired and informed this python version.
"""
# Modules
from __future__ import print_function
import json
from colorama import init
from datetime import datetime
import tinytuya

# Backward compatibility for python2
try:
    input = raw_input
except NameError:
    pass

# Colorama terminal color capability for all platforms
init()

# Configuration Files
DEVICEFILE = tinytuya.DEVICEFILE
SNAPSHOTFILE = tinytuya.SNAPSHOTFILE
CONFIGFILE = tinytuya.CONFIGFILE
RAWFILE = tinytuya.RAWFILE

# Global Network Configs
DEFAULT_NETWORK = tinytuya.DEFAULT_NETWORK
TCPTIMEOUT = tinytuya.TCPTIMEOUT    # Seconds to wait for socket open for scanning
TCPPORT = tinytuya.TCPPORT          # Tuya TCP Local Port

def wizard(color=True, retries=None, forcescan=False, nocloud=False):
    """
    TinyTuya Setup Wizard Tuya based WiFi smart devices

    Parameter:
        color = True or False, print output in color [Default: True]
        retries = Number of retries to find IP address of Tuya Devices
        forcescan = True or False, force network scan for device IP addresses

    Description
        Setup Wizard will prompt user for Tuya IoT Developer credentials and will gather all of
        the Device IDs and their Local KEYs.  It will save the credentials and the device
        data in the tinytuya.json and devices.json configuration files respectively.

        HOW to set up your Tuya IoT Developer account: iot.tuya.com:
        https://github.com/jasonacox/tinytuya#get-the-tuya-device-local-key

    Credits
    * Tuya API Documentation
        https://developer.tuya.com/en/docs/iot/open-api/api-list/api?id=K989ru6gtvspg
    * TuyaAPI https://github.com/codetheweb/tuyapi by codetheweb and blackrozes
        The TuyAPI/CLI wizard inspired and informed this python version.
    """

    config = {}
    config['apiKey'] = ''
    config['apiSecret'] = ''
    config['apiRegion'] = ''
    config['apiDeviceID'] = ''
    needconfigs = True
    try:
        # Load defaults
        with open(CONFIGFILE) as f:
            config = json.load(f)
    except:
        # First Time Setup
        pass

    (bold, subbold, normal, dim, alert, alertdim, cyan, red, yellow) = tinytuya.termcolor(color)

    print(bold + 'TinyTuya Setup Wizard' + dim + ' [%s]' % (tinytuya.version) + normal)
    print('')

    if (config['apiKey'] != '' and config['apiSecret'] != '' and
            config['apiRegion'] != ''):
        needconfigs = False
        apiDeviceID = '<None>' if not config['apiDeviceID'] else config['apiDeviceID']
        print("    " + subbold + "Existing settings:" + dim +
              "\n        API Key=%s \n        Secret=%s\n        DeviceID=%s\n        Region=%s" %
              (config['apiKey'], config['apiSecret'], apiDeviceID,
               config['apiRegion']))
        print('')
        answer = input(subbold + '    Use existing credentials ' +
                       normal + '(Y/n): ')
        if answer[0:1].lower() == 'n':
            needconfigs = True

    if needconfigs:
        # Ask user for config settings
        print('')
        config['apiKey'] = input(subbold + "    Enter " + bold + "API Key" + subbold +
                                 " from tuya.com: " + normal)
        config['apiSecret'] = input(subbold + "    Enter " + bold + "API Secret" + subbold +
                                    " from tuya.com: " + normal)
        config['apiDeviceID'] = input(subbold +
                                      "    (Optional) Enter " + bold + "any Device ID" + subbold +
                                      " currently registered in Tuya App (used to pull full list): " + normal)
        # TO DO - Determine apiRegion based on Device - for now, ask
        print("\n      " + subbold + "Region List" + dim +
              "\n        cn\tChina Data Center" +
              "\n        us\tUS - Western America Data Center" +
              "\n        us-e\tUS - Eastern America Data Center" +
              "\n        eu\tCentral Europe Data Center" +
              "\n        eu-w\tWestern Europe Data Center" +
              "\n        in\tIndia Data Center\n")
        config['apiRegion'] = input(subbold + "    Enter " + bold + "Your Region" + subbold +
                                    " (Options: cn, us, us-e, eu, eu-w, or in): " + normal)
        # Write Config
        json_object = json.dumps(config, indent=4)
        with open(CONFIGFILE, "w") as outfile:
            outfile.write(json_object)
        print(bold + "\n>> Configuration Data Saved to " + CONFIGFILE)
        print(dim + json_object)

    if nocloud:
        with open(DEVICEFILE, "r") as infile:
            tuyadevices = json.load( infile )
    else:
        cloud = tinytuya.Cloud( **config )

        # on auth error getdevices() will implode
        if cloud.error:
            err = cloud.error['Payload'] if 'Payload' in cloud.error else 'Unknown Error'
            print('\n\n' + bold + 'Error from Tuya server: ' + dim + err)
            print('Check API Key and Secret')
            return

        # Get UID from sample Device ID
        json_data = cloud.getdevices( True )

        if 'result' not in json_data:
            err = json_data['Payload'] if 'Payload' in json_data else 'Unknown Error'
            print('\n\n' + bold + 'Error from Tuya server: ' + dim + err)
            print('Check DeviceID and Region')
            return

        # Filter to only Name, ID and Key, IP and mac-address
        tuyadevices = cloud.filter_devices( json_data['result'] )

    for dev in tuyadevices:
        if 'sub' in dev and dev['sub'] and 'key' in dev:
            found = False
            for parent in tuyadevices:
                # the local key seems to be the only way of identifying the parent device
                if 'key' in parent and 'id' in parent and dev['key'] == parent['key']:
                    found = parent
                    break
            if found:
                dev['parent'] = found['id']

    # Display device list
    print("\n\n" + bold + "Device Listing\n" + dim)
    output = json.dumps(tuyadevices, indent=4)  # sort_keys=True)
    print(output)

    # Save list to devices.json
    print(bold + "\n>> " + normal + "Saving list to " + DEVICEFILE)
    with open(DEVICEFILE, "w") as outfile:
        outfile.write(output)
    print(dim + "    %d registered devices saved" % len(tuyadevices))

    if not nocloud:
        # Save raw TuyaPlatform data to tuya-raw.json
        print(bold + "\n>> " + normal + "Saving raw TuyaPlatform response to " + RAWFILE)
        json_data['file'] = {
            'name': RAWFILE,
            'description': 'Full raw list of Tuya devices.',
            'account': cloud.apiKey,
            'date': datetime.now().isoformat(),
            'tinytuya': tinytuya.version
        }
        try:
            with open(RAWFILE, "w") as outfile:
                outfile.write(json.dumps(json_data, indent=4))
        except:
            print('\n\n' + bold + 'Unable to save raw file' + dim )

    # Find out if we should poll all devices
    answer = input(subbold + '\nPoll local devices? ' + normal + '(Y/n): ')
    if answer.lower().find('n') < 0:
        result = tinytuya.scanner.poll_and_display( tuyadevices, color=color, scantime=retries, snapshot=True, forcescan=forcescan )
        iplist = {}
        found = 0
        for itm in result:
            if 'gwId' in itm and itm['gwId']:
                gwid = itm['gwId']
                ip = itm['ip'] if 'ip' in itm and itm['ip'] else ''
                ver = itm['version'] if 'version' in itm and itm['version'] else ''
                iplist[gwid] = (ip, ver)
        for k in range( len(tuyadevices) ):
            gwid = tuyadevices[k]['id']
            if gwid in iplist:
                tuyadevices[k]['ip'] = iplist[gwid][0]
                tuyadevices[k]['version'] = iplist[gwid][1]
                if iplist[gwid][0]: found += 1
        if found:
            # re-write devices.json now that we have IP addresses
            output = json.dumps(tuyadevices, indent=4)
            print(bold + "\n>> " + normal + "Saving IP addresses to " + DEVICEFILE)
            with open(DEVICEFILE, "w") as outfile:
                outfile.write(output)
            print(dim + "    %d device IP addresses found" % found)

    print("\nDone.\n")
    return


if __name__ == '__main__':

    try:
        wizard()
    except KeyboardInterrupt:
        pass
