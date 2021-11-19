import json
from json import JSONDecodeError
from c8yrc.rest_client.c8y_exception import C8yException


class Cube(object):

    def __init__(self, j=None):
        self.type = None
        self.c8y_Firmware = None
        if j:
            try:
                self.__dict__ = json.loads(j)

            except JSONDecodeError as e:
                raise C8yException('fail parsing json, no valid response for the api', None)


class SoftwareImage(object):
    def __init__(self, j):
        if isinstance(j, tuple):
            self.name = j[0]
            self.version = j[1]
            self.url = j[2]
        if isinstance(j, dict):
            self.__dict__ = j

    @staticmethod
    def my_sort(elem):
        return elem.version


class CubeImage(object):

    def __init__(self, j=None):
        self.software_list = list()
        if j:
            if isinstance(j, dict):
                my_dict = j
                for k, v in my_dict.items():
                    if isinstance(v, list):
                        for my_list_item in v:
                            i = SoftwareImage(my_list_item)
                            self.software_list.append(i)
        self.sort_list()

    def sort_list(self):
        self.software_list.sort(key=SoftwareImage.my_sort)

    def get_last(self):
        return self.software_list[-1]

    def get_first(self):
        return self.software_list[0]

    def get_middle(self):
        index = len(self.software_list) // 2
        return self.software_list[index]

    def get_by_date(self, date):
        sw = [
            sw for sw in self.software_list if date in sw.version
        ]
        return sw[0]


class CubeOperation(object):

    def __init__(self, j):
        self.status = None
        self.c8y_Firmware = None
        self.id = None
        if isinstance(j, list):
            for k in j:
                if isinstance(k, dict):
                    self.__dict__ = k
                    self.c8y_Firmware = SoftwareImage(k['c8y_Firmware'])




