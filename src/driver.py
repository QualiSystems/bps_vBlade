from cloudshell.shell.core.driver_context import InitCommandContext, AutoLoadCommandContext, \
    AutoLoadDetails
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from ixia_breakingpoint_vchassis.src.cloudshell_scripts_helpers import get_api_session

from ixia_breakingpoint_ve_vblade.src.utils.sandbox_msg import get_sandbox_msg

WARN_MINIMUM_PORTS = 'warning: IGNORING CONFIGURED NUMBER OF PORTS={0} PORTS ON {1}\n MINIMUM NUMBER OF PORTS IS {2}'

WARN_MAXIMUM_PORTS = 'warning: IGNORING CONFIGURED NUMBER OF PORTS={0} ON {1}\n MAXIMUM NUMBER OF PORTS IS {2}'

NUMBER_OF_OVF_VNICS_BY_DEFAULT = 2

# At the moment only vCenter, if this changes, the constant will have to become a variable and use switch logic to
# choose
MAXIMUM_ALLOWED_VNICS_ON_CLOUD_PROVIDER = 8

EX_MISSING_ATTRIBUTE = 'Missing attribute on resource model {0}'

ATTR_NUMBER_OF_PORTS = 'Number Of Ports'


# noinspection PyAttributeOutsideInit
class IxiaBreakingpointVeVbladeDriver(ResourceDriverInterface):
    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        pass

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        self.name = context.resource.name
        self.model = context.resource.model
        self.api = get_api_session()
        self.user_msg = get_sandbox_msg(self.api, context)

    def pre_autoload_configuration_command(self, context):
        """
        A simple example function
        :param cloudshell.shell.core.driver_context.ResourceCommandContext context: the context the command runs on
        """
        self.user_msg('Checking port configuration on {0}'.format(self.name))

        if ATTR_NUMBER_OF_PORTS not in context.resource.attributes: raise Exception(
            EX_MISSING_ATTRIBUTE.format(self.model))

        number_of_ports = context.resource.attributes[ATTR_NUMBER_OF_PORTS]

        self.user_msg('{0} ports needed on {1} '.format(number_of_ports, self.name))

        if number_of_ports > MAXIMUM_ALLOWED_VNICS_ON_CLOUD_PROVIDER:
            self.user_msg(WARN_MAXIMUM_PORTS.format(number_of_ports, self.name, MAXIMUM_ALLOWED_VNICS_ON_CLOUD_PROVIDER))

        if number_of_ports < NUMBER_OF_OVF_VNICS_BY_DEFAULT:
            self.user_msg(WARN_MINIMUM_PORTS.format(number_of_ports, self.name, NUMBER_OF_OVF_VNICS_BY_DEFAULT))

        if number_of_ports > NUMBER_OF_OVF_VNICS_BY_DEFAULT:
            call_vCenter_method_to_add_vnics()

        pass

    def get_inventory(self, context):
        """
        Discovers the resource structure and attributes.
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        # See below some example code demonstrating how to return the resource structure
        # and attributes. In real life, of course, if the actual values are not static,
        # this code would be preceded by some SNMP/other calls to get the actual resource information
        '''
           # Add sub resources details
           sub_resources = [ AutoLoadResource(model ='Generic Chassis',name= 'Chassis 1', relative_address='1'),
           AutoLoadResource(model='Generic Module',name= 'Module 1',relative_address= '1/1'),
           AutoLoadResource(model='Generic Port',name= 'Port 1', relative_address='1/1/1'),
           AutoLoadResource(model='Generic Port', name='Port 2', relative_address='1/1/2'),
           AutoLoadResource(model='Generic Power Port', name='Power Port', relative_address='1/PP1')]


           attributes = [ AutoLoadAttribute(relative_address='', attribute_name='Location', attribute_value='Santa Clara Lab'),
                          AutoLoadAttribute('', 'Model', 'Catalyst 3850'),
                          AutoLoadAttribute('', 'Vendor', 'Cisco'),
                          AutoLoadAttribute('1', 'Serial Number', 'JAE053002JD'),
                          AutoLoadAttribute('1', 'Model', 'WS-X4232-GB-RJ'),
                          AutoLoadAttribute('1/1', 'Model', 'WS-X4233-GB-EJ'),
                          AutoLoadAttribute('1/1', 'Serial Number', 'RVE056702UD'),
                          AutoLoadAttribute('1/1/1', 'MAC Address', 'fe80::e10c:f055:f7f1:bb7t16'),
                          AutoLoadAttribute('1/1/1', 'IPv4 Address', '192.168.10.7'),
                          AutoLoadAttribute('1/1/2', 'MAC Address', 'te67::e40c:g755:f55y:gh7w36'),
                          AutoLoadAttribute('1/1/2', 'IPv4 Address', '192.168.10.9'),
                          AutoLoadAttribute('1/PP1', 'Model', 'WS-X4232-GB-RJ'),
                          AutoLoadAttribute('1/PP1', 'Port Description', 'Power'),
                          AutoLoadAttribute('1/PP1', 'Serial Number', 'RVE056702UD')]

           return AutoLoadDetails(sub_resources,attributes)
        '''
        pass

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass


