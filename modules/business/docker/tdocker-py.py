#!/usr/bin/env python
# -*- coding:utf-8 -*-

from docker import Client

cli = Client(base_url='127.0.0.1:5555', version='1.22', timeout=15)

cli.create_host_config()
cli.create_container()





