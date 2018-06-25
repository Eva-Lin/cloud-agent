#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
import traceback

import libvirt

# from docker import DockerClient as Client
# from agent.utils.load_config import get_config_data
# from agent.business.command.exec_cmd import (Command, ExecShellException)

generic_log = logging.getLogger("business.kvm.domain")

class DomainException(Exception):
    pass

class GetConfigInfoException(Exception):
    pass


class DomainMethod(object):
    def __init__(self, docker, docker_version, docker_time_out=15):
        # 创建连接
        try:
            self.cli = libvirt.open()
        except Exception as e:
            generic_log.error("connect libvirt error".format(
                docker=docker, version=docker_version, error=traceback.format_exc()
            ))
            raise DomainException("connect libvirt client error".format(e))

    def __del__(self):
        try:
            self.cli.close()
        except:
            generic_log.error("container conn close error: error={error}".format(
                traceback.format_exc()
            ))

    def create_domain(
            self, image, cpu_period, cpu_quota, memory_used, hostname, tty, network_disabled,
            network_mode, devices, environment, dns, volumes=None, binds=None, cap_add=None,
            device_read_bps=None, device_write_bps=None, device_read_iops=None, device_write_iops=None):
        """
        创建容器
        :param image: 镜像名称
        :param cpu_period:
        :param cpu_quota:
        :param memory_used: 内存限制
        :param hostname: 主机名
        :param tty:
        :param network_disabled: 网络设置
        :param network_mode: 网络模式 (默认none)
        :param devices: 挂在
        :param environment: 环境变量
        :param dns: 域名解析
        :param cap_add: 部分权限
        :param volumes: 共享存储
        :param binds:挂在点 {'/home/user1/': {
                                                'bind': '/mnt/vol2',
                                                'mode': 'rw',
                                            }，}
        :param device_read_bps: IO限速
        :param device_write_bps: IO限速
        :param device_read_iops: IO限速
        :param device_write_iops: IO限速
        :return:
        """

        try:
            # 查看镜像是否存在
            harbor_user, harbor_pwd, harbor_host = _get_admin_config()
            generic_log.info("harbor_user:{}, harbor_pwd:{}, harbor_host:{}".format(
                harbor_user, harbor_pwd, harbor_host
            ))
            login_info = self.cli.login(harbor_user, harbor_pwd, registry=harbor_host)
            generic_log.info("logging harbor info:{}".format(login_info))
            self.get_image_status(image)
        except Exception:
            generic_log.error("create_host_config->get_img_status error: error={error}".format(
                error=traceback.format_exc()
            ))
            raise

        try:
            # 创建容器
            if not hostname:
                hostname = None     # 不给hostname 就是默认的
            container_obj = self.cli.containers.create(
                image=image,
                network_disabled=network_disabled,
                name=hostname,
                tty=tty,
                environment=environment,
                volumes=volumes,
                cap_add=cap_add,
                devices=devices,
                network_mode=network_mode,
                dns=dns,
                cpu_period=cpu_period,
                mem_limit=memory_used,
                memswap_limit=-1,
                mem_swappiness=0,
            )
        except Exception as e:
            generic_log.error("create_container error: err={error}".format(
                error=traceback.format_exc()
            ))
            raise ContainerException(
                "create_container error,info: %s" % str(e))

        try:
            # 更新容器cpu限制
            container_obj.update(
                cpu_quota=cpu_quota,
                cpu_period=cpu_period,
            )
        except Exception as e:
            generic_log.error("update_container error: err={error}".format(
                error=traceback.format_exc()
            ))
            raise ContainerException(
                "update_container error,info: %s" % str(e))

        return container_obj

    def update_container_config(
            self, container_id, cpu_quota=None, memory=None, memswap=None, cpu_period=None):
        """
        更新容器配置
        :param container_id: 容器的id
        :param cpu_quota: 修改后的cpu限制
        :param memory: 修改后的内存限制
        :param memswap:
        :param cpu_period :
        :return:
        """
        try:
            if memswap is None:
                memswap = -1

            container_obj = self.cli.containers.get(container_id)
            container_obj.update(
                mem_limit=memory,
                memswap_limit=memswap,
                cpu_period=cpu_period,
                cpu_quota=cpu_quota
            )
        except Exception as e:
            generic_log.error("update_container_config error: err={error}".format(
                error=traceback.format_exc()
            ))
            raise ContainerException(str(e))
        return True

    def delete_container(self, container_id=None, force=False):
        """
        关闭指定容器
        :param container_id:
        :param force:
        :return:
        """
        try:
            container_obj = self.cli.containers.get(container_id)
            container_obj.remove(force=force)
        except Exception as e:
            generic_log.error("delete_container err: container_id={container_id}, err={error}".format(
                container_id=container_id, error=traceback.format_exc()
            ))
            raise ContainerException(str(e))
        return True

    def get_container_status(self, container_id):
        """
        得到容器状态
        :return:
        """
        try:
            container_obj = self.cli.containers.get(container_id)
            status = container_obj.attrs["State"]["Running"]
            return status
        except Exception as e:
            generic_log.error("get_container_status err: container_id={container_id}, err={error}".format(
                container_id=container_id, error=traceback.format_exc()
            ))
            raise ContainerException(str(e))

    def get_hostname(self, container_id):
        """
        获得hostname信息
        :param container_id:
        :return:
        """
        try:
            container_obj = self.cli.containers.get(container_id)
            hostname = container_obj.name
            return hostname.strip('/')
        except Exception as e:
            generic_log.error("get_hostname error: container_id={container_id}, err={error}".format(
                error=traceback.format_exc(), container_id=container_id
            ))
            raise ContainerException(str(e))

    def is_use_swap(self, container_id):
        """
        获取容器是否使用了交换分区
        :param container_id:
        :return: True:使用， False：未使用
        """
        try:
            container_obj = self.cli.containers.get(container_id)
            memswap_info = container_obj.attrs.get("HostConfig", {}).get("MemorySwap")
            mem_swap = int(memswap_info)
            if mem_swap == -1:  # 未使用交换分区
                return False
            else:
                return True
        except Exception:
            generic_log.error("is_use_swap error: container_id={container_id}, err={error}".format(
                error=traceback.format_exc(), container_id=container_id
            ))
            return None

    def get_image_status(self, image):
        """
        查看现在处理的这个镜像是否已经被pull到环境中
        没有就pull一下
        :param image:
        :return:
        """
        try:
            image_dt = self.cli.images.list()
            if image_dt:
                for _dt in image_dt:
                    if image in _dt.tags:
                        return True
        except Exception:
            generic_log.error("get_image_status error: err={error}".format(error=traceback.format_exc()))
            cmd = "echo 'y' | sudo dmsetup udevcomplete_all"
            generic_log.info("start_exec_dmsetup")
            try:
                exectuor = Command()
                exectuor.execute_cmd(cmd)
                self.cli.images.pull(image)
            except Exception as ee:
                generic_log.error("dmsetup exec: err={error}".format(error=traceback.format_exc()))
                raise ContainerException(str(ee))
        try:
            self.cli.images.pull(image)
        except Exception as e:
            generic_log.error("get_image_status error: err={error}".format(error=traceback.format_exc()))
            raise ContainerException(str(e))

    def start_container(self, container_id=None):
        """
        启动指定容器
        :param container_id:
        :return:
        """
        try:
            container_obj = self.cli.containers.get(container_id)
            container_obj.start()
            container_obj.reload()
            c_status = container_obj.status
            if c_status != 'running':
                generic_log.error("start_container error: container_id={container_id}, status={status}, err={error}".format(
                    container_id=container_id, status=c_status, error=traceback.format_exc()
                ))
                raise ContainerException('error : %s' % c_status)
            return c_status
        except Exception as e:
            generic_log.error("start_container error: container_id={container_id}, err={error}".format(
                container_id=container_id, error=traceback.format_exc()
            ))
            err_str = str(traceback.format_exc())
            if err_str.find("devicemapper: Can't set cookie dm_task_set_cookie failed") != -1:
                cmd = "echo 'y' | sudo dmsetup udevcomplete_all"
                generic_log.info("start_container_exec_dmsetup")
                try:
                    container_obj = self.cli.containers.get(container_id)
                    container_obj.start()
                    container_obj.reload()
                    c_status = container_obj.status
                    if c_status != 'running':
                        generic_log.error("start_container error: container_id={container_id}, err={error}".format(
                            container_id=container_id, error=traceback.format_exc()
                        ))
                        raise ContainerException('error : %s' % c_status)
                    return c_status
                except Exception as ee:
                    generic_log.error("start_container_exec_err:{}".format(
                        traceback.format_exc()
                    ))
                    raise ContainerException(str(ee))
            raise ContainerException(str(e))

    def stop_container(self, container_id=None):
        """
        关闭指定容器
        :param container_id:
        :return:
        """
        try:
            container_obj = self.cli.containers.get(container_id)
            container_obj.stop()
        except Exception as e:
            generic_log.error("stop_container error: container_id={container_id}, err={error}".format(
                container_id=container_id, error=traceback.format_exc()
            ))
            raise ContainerException(str(e))
        return True

    def pause_container(self, container_id=None):
        """
        暂停指定容器
        :param container_id:
        :return:
        """
        try:
            container_obj = self.cli.containers.get(container_id)
            container_obj.pause()
        except Exception as e:
            generic_log.error("pause_container error: container_id={container_id}, err={error}".format(
                container_id=container_id, error=traceback.format_exc()
            ))
            raise ContainerException(str(e))
        return True

    def unpause_container(self, container_id=None):
        """
        取消暂停指定容器
        :param container_id:
        :return:
        """
        try:
            container_obj = self.cli.containers.get(container_id)
            container_obj.unpause()
        except Exception as e:
            generic_log.error("unpause_container error: container_id={container_id}, err={error}".format(
                container_id=container_id, error=traceback.format_exc()
            ))
            raise ContainerException(str(e))
        return True

    def execute_command_on_container(self, container_id, cmd):
        """
        在指定容器上执行指定命令
        :return:
        """
        try:
            container_obj = self.cli.containers.get(container_id)
            exit_code, output = container_obj.exec_run(cmd)
            return output
        except Exception as e:
            generic_log.error("exec_cmd_container error: cmd={cmd}, container_id={container_id}, err={error}".format(
                container_id=container_id, error=traceback.format_exc(), cmd=cmd
            ))
            raise ContainerException(str(e))

    def get_container_info(self):
        """
        得到所有running容器的对象列表tmp_xulin
        :return:
        """
        try:
            info_lt = self.cli.containers.list()
            return info_lt
        except Exception as e:
            generic_log.error("get_container_info error: err={error}".format(
                error=traceback.format_exc()
            ))
            raise ContainerException(str(e))

    def commit_image(self, container_id, repository, tag="latest", message=None):
        """
        克隆容器 - 将给定的容器提交为镜像,并上传到harbor
        :param container_id:
        :param repository:
        :param tag:
        :param message
        :return: 提交的镜像id
        """
        try:
            # 提交镜像, 如果重复提交会将同名的repository和tag设置为none
            container_obj = self.cli.containers.get(container_id)
            image_obj = container_obj.commit(repository=repository, tag=tag, message=message)
            image_id = image_obj.id.split(":")[1]
            generic_log.info("commit info: image_tags={}, image_id={}".format(ret.tags[0], image_id))

            # 登录harbor
            harbor_user, harbor_pwd, harbor_host = _get_admin_config()
            login_info = self.cli.login(username=harbor_user, password=harbor_pwd, registry=harbor_host)
            generic_log.info("registry_login_info:{}".format(login_info))

            # 推送到私有镜像仓库
            push_info = self.cli.images.push(repository, tag)
            if push_info.find("errorDetail") != -1:  # 上传镜像失败
                return None
            generic_log.info("Push_info:{}".format(push_info))
            ret_info = {
                "image_id": image_id,
                "repository": repository,
                "tag": tag
            }
            return ret_info
        except Exception as e:
            generic_log.error("commit image error: err={error}".format(
                error=traceback.format_exc()
            ))
            raise ContainerException("commit image error: {}".format(e))

    def exec_startscript(self, container_id):
        """
        执行启动脚本
        :param container_id:
        :return:
        """
        # 启动脚本存放的位置(固定好的路径)
        # cmd = ["bash", "-c", "if [ -e /usr/sbin/start ]; then sh /usr/sbin/start fi"]
        # cmd = ["bash", "-c", "nohup /bin/bash /usr/sbin/start"]

        # try:
        #     info = self.cli.exec_create(container_id, cmd)
        #     exec_id = info["Id"]
        #     result = self.cli.exec_start(exec_id=exec_id)
        #     return result
        # except Exception as e:
        #     generic_log.error("exec_start_script err: cmd={cmd}, error={error}".format(
        #         cmd=cmd, error=traceback.format_exc()
        #     ))
        #     raise ContainerException(str(e))

        cmd = 'docker exec {container_id} bash -c "nohup /bin/bash /usr/sbin/start > /dev/null 2>&1 &" '.format(
            container_id=container_id
        )
        try:
            Command().execute_cmd(cmd)
        except Exception as e:
            generic_log.info("exec scirpt: {}".format(e))

    def build_image(self, image_id, repository, tag):
        """
        :param image_id:
        :param tag:
        :param repository:
        :return:
        """
        try:
            # 登录harbor
            harbor_user, harbor_pwd, harbor_host = _get_admin_config()
            login_info = self.cli.login(harbor_user, harbor_pwd, registry=harbor_host)
            generic_log.info("registry_login_info:{}".format(login_info))

            # 推送到私有镜像仓库
            push_info = self.cli.images.push(repository, tag)
            generic_log.info("Push_info:{}".format(push_info))
            if push_info.find("errorDetail") != -1:  # 上传镜像失败
                return None
            ret_info = {
                "image_id": image_id,
                "repository": repository,
                "tag": tag
            }
            return ret_info
        except Exception as e:
            generic_log.error("build_image err: error={}".format(
                traceback.format_exc()
            ))
            raise ContainerException(str(e))


if __name__ == '__main__':
    image = "registry.cloud.jyall.com/build_dockerfile_java:3.2"
    cpu_period = 1000
    cpu_quota = 1000
    memory_used = "1024m"
    hostname = None
    tty = True
    network_disabled = False
    network_mode = "none"
    dev_name = "/dev/tapdisk-252-01d4b484-bbf7-11e6-8a53-000c290201d4be98-bbf7-11e6-8a53-000c2902"
    devices = ["%s:%s:rwm" % (dev_name, dev_name)]
    # 环境变量
    environment = {
        "DEV": dev_name,
        "LOCATION": "/data"
    }
    dns = ["10.10.10.10"]
    cap_add = ['SYS_ADMIN']
    obj = ContainerMethod(docker="10.10.20.219:5555", docker_version="1.22")
    volumes = ["/data2"]
    binds = {'/docker-data/works/user/test22': {
        'bind': '/data2',
    }}
    container_id = obj.create_container(
        image=image,
        cpu_period=cpu_period,
        cpu_quota=cpu_quota,
        memory_used=memory_used,
        hostname=hostname,
        tty=tty,
        network_disabled=network_disabled,
        network_mode=network_mode,
        devices=devices,
        environment=environment,
        dns=dns,
        cap_add=cap_add,
        binds=binds,
        volumes=volumes
    )[0]

    obj.start_container(container_id)
    print(container_id)










