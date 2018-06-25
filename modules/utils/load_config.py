#!/usr/bin/env python
# -*- coding:utf-8 -*-

import configparser


class Config_file:
    def __init__(self, config_path):
        # 初始化实例
        self.config_parser = configparser.ConfigParser()
        self.config_path = config_path
        self.load_config_file()

    def load_config_file(self):
        # 读取配置文件
        self.config_parser.read(self.config_path, encoding='utf-8')

    def get_config_section(self, section_name):
        # 获取配置指定section信息
        config_msg = self.config_parser.items(section_name)
        return dict(config_msg)


class Config_data:
    """公共对象"""
    config_obj = None

    @staticmethod
    def set_config_data(obj):
        # 定义公共对象
        Config_data.config_obj = obj

    @staticmethod
    def get_config_data(name):
        # 调用公共对象执行对应method
        return Config_data.config_obj.get_config_section(name)


