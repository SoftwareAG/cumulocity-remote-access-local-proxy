#  Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
#  SPDX-License-Identifier: Apache-2.0
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from setuptools import setup

setup(name='c8ylp',
      version='1.3.5',
      description='Cumulocity Local Client Proxy',
      author='Stefan Witschel',
      license='Apache v2',
      packages=['c8ylp',
                'c8ylp.tcp_socket',
                'c8ylp.websocket_client',
                'c8ylp.rest_client'],
      entry_points={
        'console_scripts': [
              'c8ylp=c8ylp.main:start'
            ],
      },
      install_requires = [
        'requests>=2.25.1',
        'websocket_client>=1.1.0'
      ],
      zip_safe=False)
