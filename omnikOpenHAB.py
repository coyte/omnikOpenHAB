#!/usr/local/bin/jython
"""OmnikOpenhab program.

Get data from an omniksol inverter with 602xxxxx - 606xxxx ans save the data in
a database or push to pvoutput.org.
"""
import socket  # Needed for talking to inverter
import sys
import logging
import logging.config
import ConfigParser
import os
import InverterMsg  # Import the Msg handler



class OmnikOpenhab(object):
    """
    Get data from Omniksol inverter and store the data in a configured output
    format/location.
    """

    config = None
    logger = None
    total_e_today = 0
    total_e_total = 0
    total_p_ac = 0
    total_i_ac = 0
    

    def __init__(self, config_file):
        # Load the setting
        config_files = [self.__expand_path('config-default.cfg'),
                        self.__expand_path(config_file)]

        self.config = ConfigParser.RawConfigParser()
        self.config.read(config_files)

    def getInverters(self):
        self.build_logger(self.config)
        #Get number of inverters
        inverterCount = len(self.config.sections())
        #For each inverter, get data and add to total
        for i in range(1,inverterCount):
            msg = self.run(i)
            self.add(msg)

        self.logger.debug("Total_e_today: {0}".format(OmnikOpenhab.total_e_today))
        self.logger.debug("Total_e_total: {0}".format(OmnikOpenhab.total_e_total))
        self.logger.debug("Total_p_ac: {0}".format(OmnikOpenhab.total_p_ac)) 
        self.logger.debug("Total_i_ac: {0}".format(OmnikOpenhab.total_i_ac)) 
         
    
    def add(self,msg):
        OmnikOpenhab.total_e_today += msg.e_today
        OmnikOpenhab.total_e_total += msg.e_total
        OmnikOpenhab.total_p_ac += msg.p_ac(1) + msg.p_ac(2) + msg.p_ac(3)
        OmnikOpenhab.total_i_ac += msg.i_ac(1) + msg.i_ac(2) + msg.i_ac(3)
        

    def run(self,inverternr):
        """Get information from inverter and store is configured outputs."""

        
        
        

        # Connect to inverter
        ip = self.config.get('inverter' + str(inverternr), 'ip')
        port = self.config.get('inverter' + str(inverternr), 'port')
        

        for res in socket.getaddrinfo(ip, port, socket.AF_INET,
                                      socket.SOCK_STREAM):
            family, socktype, proto, canonname, sockadress = res
            try:
                self.logger.debug('connecting to {0} port {1}'.format(ip, port))
                inverter_socket = socket.socket(family, socktype, proto)
                inverter_socket.settimeout(10)
                inverter_socket.connect(sockadress)
            except socket.error as msg:
                self.logger.error('Could not open socket')
                self.logger.error(msg)
                sys.exit(1)

        wifi_serial = self.config.getint('inverter' + str(inverternr), 'wifi_sn')
        inverter_socket.sendall(OmnikOpenhab.generate_string(wifi_serial))
        data = inverter_socket.recv(1024)
        inverter_socket.close()

        msg = InverterMsg.InverterMsg(data)

        self.logger.debug("ID: {0}".format(msg.id))
  
        return(msg)

    def build_logger(self, config):
        # Build logger
        """
        Build logger for this program


        Args:
            config: ConfigParser with settings from file
        """
        log_levels = dict(debug=10, info=20, warning=30, error=40, critical=50)
        log_dict = {
            'version': 1,
            'formatters': {
                'f': {'format': '%(asctime)s %(levelname)s %(message)s'}
            },
            'handlers': {
                'none': {'class': 'logging.NullHandler'},
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'f'
                },
            },
            'loggers': {
                'OmnikLogger': {
                    'handlers': config.get('log', 'type').split(','),
                    'level': log_levels[config.get('log', 'level')]
                }
            }
        }
        logging.config.dictConfig(log_dict)
        self.logger = logging.getLogger('OmnikLogger')

    def override_config(self, section, option, value):
        """Override config settings"""
        self.config.set(section, option, value)

    @staticmethod
    def __expand_path(path):
        """
        Expand relative path to absolute path.

        Args:
            path: file path

        Returns: absolute path to file

        """
        if os.path.isabs(path):
            return path
        else:
            return os.path.dirname(os.path.abspath(__file__)) + "/" + path

    @staticmethod
    def generate_string(serial_no):
        """Create request string for inverter.

        The request string is build from several parts. The first part is a
        fixed 4 char string; the second part is the reversed hex notation of
        the s/n twice; then again a fixed string of two chars; a checksum of
        the double s/n with an offset; and finally a fixed ending char.

        Args:
            serial_no (int): Serial number of the inverter

        Returns:
            str: Information request string for inverter
        """
        response = '\x68\x02\x40\x30'

        double_hex = hex(serial_no)[2:] * 2
        hex_list = [double_hex[i:i + 2].decode('hex') for i in
                    reversed(range(0, len(double_hex), 2))]

        cs_count = 115 + sum([ord(c) for c in hex_list])
        checksum = hex(cs_count)[-2:].decode('hex')
        response += ''.join(hex_list) + '\x01\x00' + checksum + '\x16'
        return response



if __name__ == "__main__":
    omnik_openhab = OmnikOpenhab('config.cfg')
    omnik_openhab.getInverters()
