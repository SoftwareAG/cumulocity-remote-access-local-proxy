import json
import logging
import os
import time
import requests
from c8ylp.rest_client.c8y_enterprise import Cube, CubeImage, SoftwareImage, CubeOperation
from c8ylp.rest_client.c8y_exception import C8yException
from c8ylp.rest_client.rest_constants import UPDATE_FIRMWARE_OPERATION_HEADER, C8YQueries, C8YOperationStatus


class C8yRestClient:

    def __init__(self, serial_number, user, password, tenant, tfacode=None):
        self.host = 'https://main.dm-zz-q.ioee10-cloud.com/'
        self.session = requests.Session()
        self.session.verify = False
        self.device_id = None
        self.token = None
        self.tenant = None
        self.headers = None
        self.cy8_device = None
        self.ext_type = 'c8y_Serial'
        self.serial_number = serial_number
        self.start(user, password, tenant, tfacode)

    def start(self, user, password, tenant, tfacode):
        self.tenant = tenant
        self.validate_tenant_id()
        self.retrieve_token(user, password, tfacode, tenant)
        os.environ['C8Y_TOKEN'] = self.session.cookies.get_dict()['authorization']
        # self.headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token}
        self.headers = {'Content-Type': 'application/json',
                                  'X-XSRF-TOKEN': self.session.cookies.get_dict()['XSRF-TOKEN']
                                   #'Authorization': 'Basic ' + encoded_auth_string
                      }
        self.get_device_info()

    def validate_tenant_id(self):
        # 'https://main.dm-zz-q.ioee10-cloud.com/tenant/loginOptions'
        tenant_id = None
        current_user_url = self.host + f'tenant/loginOptions'
        headers = {}
        response = self.session.get(current_user_url, headers=headers)
        logging.debug(f'Response received: {response}')
        if response.status_code == 200:
            login_options_body = json.loads(response.content.decode('utf-8'))
            login_options = login_options_body['loginOptions']
            for option in login_options:
                if 'initRequest' in option:
                    tenant_id = option['initRequest'].split('=')[1]
                    if self.tenant != tenant_id:
                        logging.debug(f'Wrong Tenant ID {self.tenant}, Correct Tenant ID: {tenant_id}')
                        self.tenant = tenant_id
                    break

        else:
            logging.error(f'Error validating Tenant ID!')
        return tenant_id

    def retrieve_token(self, user, password, tfacode, tenant):
        oauth_url = self.host + f'tenant/oauth?tenant_id={tenant}'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        body = {
            'grant_type': 'PASSWORD',
            'username': user,
            'password': password,
            'tfa_code': tfacode
        }
        logging.debug(f'Sending requests to {oauth_url}')
        response = self.session.post(oauth_url, headers=headers, data=body)
        if response.status_code == 200:
            logging.debug(f'Authentication successful. Tokens have been updated {self.session.cookies.get_dict()}!')
            self.token = self.session.cookies.get_dict()['authorization']
            os.environ['C8Y_TOKEN'] = self.token
            return

        msg = f'Server Error received for User {user} and Tenant {tenant}. Status Code: {response.status_code}'
        logging.error(msg)
        raise C8yException(msg, None)

    def get_data(self, query: str) -> dict:
        """
        Method to get data by specified query

        :param query:   Query
        :return:        Response data in dict representation
        """
        response = self.session.get(url=f'{self.host}{query}', headers=self.headers)
        return json.loads(response.text)

    def send_data(self, query: str, data):
        """
        Method to send data to the Cumulocity host URL

        :param query:   Query
        :param data:    Data to send
        :return:        Response data
        """
        response = self.session.post(url=f'{self.host}{query}', data=json.dumps(data), headers=self.headers)
        return response.request

    def get_device_id_by_serial_number(self, serial_number: str, ext_type: str) -> int:
        """
        Method to get Cumulocity device ID by device serial number

        :param serial_number:   Cumulocity device ESN
        :return:                Cumulocity device ID
        """
        # c8y devices list --query "c8y_Hardware.serialNumber eq '{serial_number}'"
        # response = self.get_data(query=C8YQueries.GET_DEVICE_ID_BY_SN.format(serial_number))
        response = self.get_data(query=C8YQueries.GET_DEVICE_ID_BY_ESN.format(ext_type, serial_number))
        return int(response['managedObject']['id'])

    def get_cube_availability_status(self) -> str:
        """
        Method to get Cumulocity device availability status

        :param device_id:   Cumulocity device ID
        :return:            Cumulocity device availability status
        """
        # c8y devices get --id {device_id} --select "id,c8y_Availability.status"
        response = self.get_data(query=C8YQueries.SELECT_DEVICE_BY_ID.format(self.device_id))

        return response['c8y_Availability']['status']

    def get_cube_connection_status(self) -> str:
        """
        Method to get Cumulocity device connection status

        :param device_id:   Cumulocity device ID
        :return:            Cumulocity device connection status
        """
        # c8y devices get --id {device_id} --select "id,c8y_Connection.status"
        response = self.get_data(query=C8YQueries.SELECT_DEVICE_BY_ID.format(self.device_id))

        return response['c8y_Connection']['status']

    def get_current_firmware(self, device_type: str) -> tuple:
        """
        Method to get firmware currently installed on the Cube

        :param device_type:     Cumulocity device type
        :return:                Currently installed firmware
        """
        # c8y devices get --id 20228252 --select "c8y_Firmware.name,c8y_Firmware.version"
        response = self.get_data(query=C8YQueries.SELECT_DEVICE_BY_ID.format(self.device_id))
        firmware_name = response['c8y_Firmware']['name']
        firmware_version = response['c8y_Firmware']['version']

        available_firmwares = self.get_available_firmwares(device_type)

        return tuple(firmware for firmware in available_firmwares[firmware_name] if firmware_version in firmware)

    def get_available_firmwares(self, device_type: str):
        """
        Method to get a list of available firmwares for selected device type

        :param device_type: Cumulocity device ID
        :return:
        """
        all_firmwares = {}
        # c8y inventory find --query "c8y_Filter.type eq '{device_type}'" --filter "type eq 'c8y_Firmware'" --select "id,name"
        firmwares = self.get_data(C8YQueries.GET_FIRMWARE_BY_DEVICE_TYPE.format(device_type))

        supported_firmwares = tuple((firmware['name'], firmware['id']) for firmware in firmwares['managedObjects'])

        for firmware in supported_firmwares:
            firmware_images = self.get_data(C8YQueries.GET_FIRMWARE_BINARY.format(firmware[1]))

            firmware_version_url = [
                (firmware[0], image['c8y_Firmware']['version'], image['c8y_Firmware']['url']) for image in firmware_images['managedObjects']
            ]

            all_firmwares.update({firmware[0]: sorted(firmware_version_url)})

        return all_firmwares

    def wait_for_operation_state(self, operation_id: int, expected_state: str, time_to_wait: int = 10 * 60, period: int = 60):
        """
        Function to wait until operation state will be equal to expected state.

        :param operation_id:    Cumulocity operation ID.
        :param expected_state:  Expected state.
        :param time_to_wait:    Time to wait.
        :param period:          Time between state verification

        :return: Whether state is expected (bool).
        """
        time_start = time.time()
        while time.time() < time_start + time_to_wait:
            if expected_state == self.get_operation_state(operation_id):
                return True
            time.sleep(period)
        else:
            logging.warning(f"Operation ('{operation_id}') is not changed to '{expected_state}' in '{time_to_wait}' seconds")
            return False

    def get_operation_state(self, operation_id: int) -> str:
        """
        Method to get Cumulocity operation status by operation ID

        :param operation_id:    Cumulocity operation ID
        :return:                Cumulocity operation status
        """
        response = self.get_data(query=C8YQueries.GET_OPERATION.format(operation_id))
        return response['status']

    def get_remote_configuration_from_cumulocity(self) -> dict:
        """
        Method to get a remote configuration

        :return: Cube remote configuration from Cumulocity
        """
        # c8y devices get --id 20228252 --select "schindler_RemoteConfiguration"
        response = self.get_data(query=C8YQueries.SELECT_DEVICE_BY_ID.format(self.device_id))
        return response['schindler_RemoteConfiguration']

    def get_lxc_container(self) -> str:
        """
        Method to get a currently installed LXC container

        :return: LXC container version
        """
        response = self.get_data(query=C8YQueries.SELECT_DEVICE_BY_ID.format(self.device_id))

        return response['ac_lxcContainer']['contVersion']

    def update_cube_firmware(self, firmware: SoftwareImage) -> int:
        """
        Method to start update operation for cube under test

        :param firmware:
        :type firmware:
        :return:                    Cumulocity operation ID
        """

        operation_description = f"{UPDATE_FIRMWARE_OPERATION_HEADER} to: {firmware.name} ({firmware.version})"
        firmware_info = {
            "c8y_Firmware": {
                "name": firmware.name,
                "url": firmware.url,
                "version": firmware.version
            },
            "deviceId": str(self.device_id),
            "description": operation_description,
        }

        response = self.send_data(C8YQueries.POST_OPERATION, data=firmware_info)
        #if response.status_code != 201:
        #    raise C8yException(f'Error on send operation '
        #                       f'Status Code {response.status_code}', None)

    def get_device_info(self):
        # 1st query the device id
        identity_url = self.host + C8YQueries.GET_DEVICE_ID_BY_ESN.format(self.ext_type, self.serial_number)
        response = self.session.get(identity_url, headers=self.headers)
        if response.status_code != 200:
            raise C8yException(f'Error on  {identity_url}. '
                               f'Status Code {response.status_code}', None)
        ext_id = json.loads(response.text)
        self.device_id = ext_id['managedObject']['id']

        # 2nd query the device info
        identity_url = self.host + C8YQueries.GET_DEVICE_INFO_BY_DEV_ID.format(self.device_id)
        response = self.session.get(identity_url, headers=self.headers)
        if response.status_code != 200:
            raise C8yException(f'Error on {identity_url}. Status Code {response.status_code}', None)
        self.cy8_device = Cube(response.text)

    def get_device_operation(self):
        identity_url = self.host + C8YQueries.GET_UPDATE_OPERATION_BY_DEVICE_ID.format(self.device_id)

        response = self.session.get(identity_url, headers=self.headers)
        if response.status_code != 200:
            raise C8yException(f'Error on  {identity_url}. '
                               f'Status Code {response.status_code}', None)
        operations = json.loads(response.text)
        update_operations = [
            operation for operation in operations['operations'] if f'{UPDATE_FIRMWARE_OPERATION_HEADER}'
                                                     in operation.get('description', '')
        ]

        my_operation = CubeOperation(update_operations)
        return my_operation


if __name__ == '__main__':
    # my_device_address = 'cb1-2102351HNDDMK2000759'.lower()
    my_device_address = 'cb4-a1eucpg1qa2121000025'.lower()
    _tenant = 't2700'
    rest_user_name = 'service_schindler-jenkins',
    rest_user_password = '2txFLPmgE5xwWRovG7nW7e4Y94XhwOB3'
    client = C8yRestClient(my_device_address, rest_user_name, rest_user_password, _tenant)
    fw = client.get_available_firmwares(client.cy8_device.type)
    # print(fw)
    my_firmware_list = CubeImage(fw)
    my_firmware = my_firmware_list.get_middle()
    # client.update_cube_firmware(my_firmware)
    operation = client.get_device_operation()
    print(f'operation status {operation.status}')
    # client.wait_for_operation_state(operation_id, C8YOperationStatus.EXECUTING)
    client.wait_for_operation_state(operation.id, C8YOperationStatus.SUCCESSFUL)


