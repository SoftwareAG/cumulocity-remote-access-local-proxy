# cumulocity agent service
C8YDA_SERVICE = 'c8yda'

UPDATE_FIRMWARE_OPERATION_HEADER = "Firmware update by Jenkins :p"

# availability status
C8Y_DEVICE_UNAVAILABLE = 'UNAVAILABLE'
C8Y_DEVICE_AVAILABLE = 'AVAILABLE'

# connection status
C8Y_DEVICE_DISCONNECTED = 'DISCONNECTED'
C8Y_DEVICE_CONNECTED = 'CONNECTED'

# firmware info indexes
FIRMWARE_NAME_INDEX = 0
FIRMWARE_VERSION_INDEX = 1
FIRMWARE_URL_INDEX = 2


class C8YOperationStatus:
    """
    Class to determine all Cumulocity operation's status
    """
    SUCCESSFUL = 'SUCCESSFUL'
    FAILED = 'FAILED'
    EXECUTING = 'EXECUTING'
    PENDING = 'PENDING'


class C8YQueries:
    """
    Class to determine all necessary queries to Cumulocity
    """
    GET_TENANT_OPTIONS = 'tenant/loginOptions'
    POST_OAUTH = 'tenant/oauth?tenant_id={}'
    SELECT_DEVICE_BY_ID = 'inventory/managedObjects/{}'
    GET_DEVICE_ID_BY_SN = 'inventory/managedObjects?q=$filter=(c8y_Hardware.serialNumber+eq+{})'
    GET_FIRMWARE_BY_DEVICE_TYPE = 'inventory/managedObjects?query=$filter=(c8y_Filter.type+eq+{})+and+(type+eq+c8y_Firmware)&pageSize=100&withTotalPages=true'
    GET_FIRMWARE_BINARY = "inventory/managedObjects?query=$filter=bygroupid({})&withTotalPages=true&pageSize=2000"
    GET_OPERATION = 'devicecontrol/operations/{}'
    GET_UPDATE_OPERATION_BY_DEVICE_ID = 'devicecontrol/operations?pageSize=2000&deviceId={}'
    POST_OPERATION = 'devicecontrol/operations'
    GET_DEVICE_ID_BY_ESN = 'identity/externalIds/{}/{}'
    GET_DEVICE_INFO_BY_DEV_ID = 'inventory/managedObjects/{}'
