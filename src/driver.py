import copy

from cloudshell.api.cloudshell_api import CloudShellAPISession, InputNameValue, SetConnectorRequest
from cloudshell.shell.core.driver_context import InitCommandContext, AutoLoadCommandContext, \
    AutoLoadDetails, AutoLoadResource, AutoLoadAttribute
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

from constants import WARN_MINIMUM_PORTS, WARN_MAXIMUM_PORTS, WARN_MAXIMUM_CPUS, \
    WARN_MINIMUM_CPUS, WARN_MAXIMUM_MEMORY, WARN_MINIMUM_MEMORY, NUMBER_OF_VCPUS_BY_DEFAULT, \
    NUMBER_OF_OVF_VNICS_BY_DEFAULT, MEMORY_BY_DEFAULT, MAXIMUM_ALLOWED_VNICS_ON_CLOUD_PROVIDER, \
    MAXIMUM_ALLOWED_CPUS_ON_CLOUD_PROVIDER, MAXIMUM_ALLOWED_MEMORY_ON_CLOUD_PROVIDER, EX_MISSING_ATTRIBUTE, \
    ATTR_NUMBER_OF_PORTS, ATTR_NUMBER_OF_CPUS, ATTR_MEMORY_IN_GBS, REQUIRED_ATTRIBUTES
from utils.sandbox_msg import get_sandbox_msg
import json

# At the moment only vCenter, if this changes, the constant will have to become a variable and use switch logic to
# choose


# noinspection PyAttributeOutsideInit
IXIA_MANAGEMENT_PORT = 'Ixia Management Port'
ATTR_REQUESTED_TARGET_VNIC = 'Requested Target vNIC Name'
ATTR_REQUESTED_SOURCE_VNIC = 'Requested Source vNIC Name'
ATTR_LOGICAL_NAME = 'Logical Name'
MODEL_PORT = 'Virtual Port'


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

    def pre_autoload_configuration_command(self, context):
        """
        A simple example function
        :param cloudshell.shell.core.driver_context.ResourceCommandContext context: the context the command runs on
        """
        self.api = CloudShellAPISession(host=context.connectivity.server_address,
                                        token_id=context.connectivity.admin_auth_token,
                                        domain='Global')
        self.user_msg = get_sandbox_msg(self.api, context)
        self.user_msg('Checking port configuration on {0}'.format(self.name))

        for attribute_name in REQUIRED_ATTRIBUTES:
            if attribute_name not in context.resource.attributes: raise Exception(
                EX_MISSING_ATTRIBUTE.format(self.model, attribute_name))

        number_of_ports = int(context.resource.attributes[ATTR_NUMBER_OF_PORTS])
        number_of_cpus = int(context.resource.attributes[ATTR_NUMBER_OF_CPUS])
        memory_in_gbs = int(context.resource.attributes[ATTR_MEMORY_IN_GBS])

        vm_changes = dict()
        vm_changes = self._get_nic_changes(number_of_ports, vm_changes)
        vm_changes = self._get_CPU_changes(number_of_cpus, vm_changes)
        vm_changes = self._get_memory_changes(memory_in_gbs, vm_changes)
        vm_changes_params = json.dumps(vm_changes)
        if vm_changes:
            self.api.ExecuteResourceConnectedCommand(context.reservation.reservation_id, context.resource.name,
                                                     'modify_vm_hardware', 'remote_app_management', [vm_changes_params])

        pass

    def _get_nic_changes(self, number_of_ports, vm_changes):
        if number_of_ports + 1 > MAXIMUM_ALLOWED_VNICS_ON_CLOUD_PROVIDER:
            self.user_msg(
                WARN_MAXIMUM_PORTS.format(number_of_ports, self.name, MAXIMUM_ALLOWED_VNICS_ON_CLOUD_PROVIDER))
        if number_of_ports < NUMBER_OF_OVF_VNICS_BY_DEFAULT:
            self.user_msg(WARN_MINIMUM_PORTS.format(number_of_ports, self.name, NUMBER_OF_OVF_VNICS_BY_DEFAULT))
        if number_of_ports > NUMBER_OF_OVF_VNICS_BY_DEFAULT:
            number_of_ports_to_add = number_of_ports - NUMBER_OF_OVF_VNICS_BY_DEFAULT
            self.user_msg(
                '{0} ports needed on {1}\nadding {2} ports '.format(number_of_ports, self.name, number_of_ports_to_add))
            vm_changes['nics'] = number_of_ports_to_add
        return vm_changes

    def _get_CPU_changes(self, number_of_cpus, vm_changes):
        if number_of_cpus > MAXIMUM_ALLOWED_CPUS_ON_CLOUD_PROVIDER:
            self.user_msg(
                WARN_MAXIMUM_CPUS.format(number_of_cpus, self.name, MAXIMUM_ALLOWED_CPUS_ON_CLOUD_PROVIDER))
        if number_of_cpus < NUMBER_OF_VCPUS_BY_DEFAULT:
            self.user_msg(WARN_MINIMUM_CPUS.format(number_of_cpus, self.name, NUMBER_OF_VCPUS_BY_DEFAULT))
        if number_of_cpus > NUMBER_OF_VCPUS_BY_DEFAULT:
            self.user_msg('{0} cpus needed on {1} '.format(number_of_cpus, self.name))
            vm_changes['cpu'] = int(number_of_cpus)
        return vm_changes

    def _get_memory_changes(self, memory_in_GBs, vm_changes):
        if memory_in_GBs > MAXIMUM_ALLOWED_CPUS_ON_CLOUD_PROVIDER:
            self.user_msg(
                WARN_MAXIMUM_MEMORY.format(memory_in_GBs, self.name, MAXIMUM_ALLOWED_MEMORY_ON_CLOUD_PROVIDER))
        if memory_in_GBs < MEMORY_BY_DEFAULT:
            self.user_msg(WARN_MINIMUM_MEMORY.format(memory_in_GBs, self.name, MEMORY_BY_DEFAULT))
        if memory_in_GBs > MEMORY_BY_DEFAULT:
            self.user_msg('{0} GBs of memory needed on {1} '.format(memory_in_GBs, self.name))
            vm_changes['memory'] = int(memory_in_GBs)
        return vm_changes

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

        number_of_ports = int(context.resource.attributes[ATTR_NUMBER_OF_PORTS]) + 1
        resources = []
        attributes = []
        for i in range(number_of_ports):
            address = str(i)
            attributes.append(AutoLoadAttribute(address, 'Requested vNIC Name', 'Network adapter ' + str(i + 1)))
            if i == 0:
                port_name = IXIA_MANAGEMENT_PORT
            else:
                port_name = 'Port ' + address
                attributes.append(AutoLoadAttribute(address, ATTR_LOGICAL_NAME, address))

            resources.append(AutoLoadResource(model=MODEL_PORT, name=port_name, relative_address=address))
        return AutoLoadDetails(resources, attributes)

        # '''
        #    # Add sub resources details
        #    sub_resources = [ AutoLoadResource(model ='Generic Chassis',name= 'Chassis 1', relative_address='1'),
        #    AutoLoadResource(model='Generic Module',name= 'Module 1',relative_address= '1/1'),
        #    AutoLoadResource(model='Generic Port',name= 'Port 1', relative_address='1/1/1'),
        #    AutoLoadResource(model='Generic Port', name='Port 2', relative_address='1/1/2'),
        #    AutoLoadResource(model='Generic Power Port', name='Power Port', relative_address='1/PP1')]
        #
        #
        #    attributes = [ AutoLoadAttribute(relative_address='', attribute_name='Location', attribute_value='Santa Clara Lab'),
        #                   AutoLoadAttribute('', 'Model', 'Catalyst 3850'),
        #                   AutoLoadAttribute('', 'Vendor', 'Cisco'),
        #                   AutoLoadAttribute('1', 'Serial Number', 'JAE053002JD'),
        #                   AutoLoadAttribute('1', 'Model', 'WS-X4232-GB-RJ'),
        #                   AutoLoadAttribute('1/1', 'Model', 'WS-X4233-GB-EJ'),
        #                   AutoLoadAttribute('1/1', 'Serial Number', 'RVE056702UD'),
        #                   AutoLoadAttribute('1/1/1', 'MAC Address', 'fe80::e10c:f055:f7f1:bb7t16'),
        #                   AutoLoadAttribute('1/1/1', 'IPv4 Address', '192.168.10.7'),
        #                   AutoLoadAttribute('1/1/2', 'MAC Address', 'te67::e40c:g755:f55y:gh7w36'),
        #                   AutoLoadAttribute('1/1/2', 'IPv4 Address', '192.168.10.9'),
        #                   AutoLoadAttribute('1/PP1', 'Model', 'WS-X4232-GB-RJ'),
        #                   AutoLoadAttribute('1/PP1', 'Port Description', 'Power'),
        #                   AutoLoadAttribute('1/PP1', 'Serial Number', 'RVE056702UD')]
        #
        #    return AutoLoadDetails(sub_resources,attributes)
        # '''

    def connect_child_resources(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :rtype: str
        """
        api = CloudShellAPISession(host=context.connectivity.server_address,
                                   token_id=context.connectivity.admin_auth_token,
                                   domain='Global')
        resource_name = context.resource.fullname
        reservation_id = context.reservation.reservation_id
        connectors = context.connectors

        if not context.connectors:
            return 'Success'

        resource = api.GetResourceDetails(resource_name)

        to_disconnect = []
        to_connect = []
        temp_connectors = []
        ports = self._get_ports(resource)

        for connector in connectors:
            me, other = self._set_remap_connector_details(connector, resource_name, temp_connectors)
            to_disconnect.extend([me, other])

        connectors = temp_connectors

        # these are connectors from app to vlan where user marked to which interface the connector should be connected
        connectors_with_predefined_target = [connector for connector in connectors if connector.vnic_id != '']

        # these are connectors from app to vlan where user left the target interface unspecified
        connectors_without_target = [connector for connector in connectors if connector.vnic_id == '']

        for connector in connectors_with_predefined_target:
            if connector.vnic_id not in ports.keys():
                raise Exception('Tried to connect an interface that is not on reservation - ' + connector.vnic_id)

            else:
                if hasattr(ports[connector.vnic_id], 'allocated'):
                    raise Exception('Tried to connect several connections to same interface: ' + ports[connector.vnic_id])

                else:
                    to_connect.append(SetConnectorRequest(SourceResourceFullName=ports[connector.vnic_id].Name,
                                                          TargetResourceFullName=connector.other,
                                                          Direction=connector.direction,
                                                          Alias=connector.alias))
                    ports[connector.vnic_id].allocated = True

        unallocated_ports = [port for key, port in ports.items() if not hasattr(port, 'allocated')]

        if len(unallocated_ports) < len(connectors_without_target):
            raise Exception('There were more connections to TeraVM than available interfaces after deployment.')
        else:
            for port in unallocated_ports:
                if connectors_without_target:
                    connector = connectors_without_target.pop()
                    to_connect.append(SetConnectorRequest(SourceResourceFullName=port.Name,
                                                          TargetResourceFullName=connector.other,
                                                          Direction=connector.direction,
                                                          Alias=connector.alias))

        if connectors_without_target:
            raise Exception('There were more connections to TeraVM than available interfaces after deployment.')

        api.RemoveConnectorsFromReservation(reservation_id, to_disconnect)
        api.SetConnectorsInReservation(reservation_id, to_connect)

        return 'Success'

    @staticmethod
    def _set_remap_connector_details(connector, resource_name, connectors):
        attribs = connector.attributes
        if resource_name in connector.source.split('/'):
            remap_requests = attribs.get(ATTR_REQUESTED_SOURCE_VNIC, '').split(',')

            me = connector.source
            other = connector.target

            for vnic_id in remap_requests:
                new_con = copy.deepcopy(connector)
                IxiaBreakingpointVeVbladeDriver._update_connector(new_con, me, other, vnic_id)
                connectors.append(new_con)

        elif resource_name in connector.target.split('/'):
            remap_requests = attribs.get(ATTR_REQUESTED_TARGET_VNIC, '').split(',')

            me = connector.target
            other = connector.source

            for vnic_id in remap_requests:
                new_con = copy.deepcopy(connector)
                IxiaBreakingpointVeVbladeDriver._update_connector(new_con, me, other, vnic_id)
                connectors.append(new_con)



        else:
            raise Exception("Oops, a connector doesn't have required details:\n Connector source: {0}\n"
                            "Connector target: {1}\nPlease contact your admin".format(connector.source,
                                                                                      connector.target))

        return me, other

    @staticmethod
    def _update_connector(connector, me, other, vnic_id):
        connector.vnic_id = vnic_id
        connector.me = me
        connector.other = other

    @staticmethod
    def _get_ports(resource):
        ports = {str(idx): port for idx, port in enumerate(resource.ChildResources)
                 if port.ResourceModelName == MODEL_PORT}
        return ports

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass
