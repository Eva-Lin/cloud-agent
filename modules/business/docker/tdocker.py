#!/usr/bin/env python
# -*- coding:utf-8 -*-

import docker

client = docker.from_env()

# new_container = client.containers.run("registry.cloud.jyall.com/build_gw:1.0", detach=True)
#
# new_container.logs()

container = client.containers.get('8a07e1a8a6')

container.remove()





