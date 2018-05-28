# OmnikOpenHAB

Script to update Openhab items with the a subset of values from one or more Omnik PV (iGEN) inverters
The script reads the data of the inverters and adds it to a total.
The script is based on Woutrrr's Omnik-Data-Logger.

## Configuration
The cfg file will need the ip address, port and wifi serial number for each inverter. You can add inverters using same format.

The script return three values to be stored in existing OpenHAB items:  
etotal: Total energy production  
etoday: Today's energy production  
epower: Actual AC power  
Assign existing OpenHAB items to populate with values.


## OpenHAB
This script has only be tested with v2 of OpenHAB.
The script is a python script and needs the jsr223 installed and configured, no other dependecies exist.
Place the files in the jsr223 directory (/etc/openhab2/automation/jsr223 on a yum-installed openhab).
The script will write to the rules.log (/var/log/openhab2/) if it doesn't already exist you may to create it.
