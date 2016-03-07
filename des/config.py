#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, os.path

CONFIG_FILENAME = "config.txt"


class Config(object):

    _config_filename = CONFIG_FILENAME

    key_logging_configuration_file = "logging_configuration_file"
    key_location_mapper_destination_file = "location_mapper_destination_file"
    key_use_netloc = "use_netloc"
    key_use_checksum = "use_checksum"
    key_audit_only = "audit_only"

    @staticmethod
    def __get__logger():
        logger = logging.getLogger(__name__)
        return logger

    @staticmethod
    def _set_config_filename(config_filename):
        if Config._instance is None:
            Config.__get__logger().info("Setting config_filename to '%s'", config_filename)
            Config._config_filename = config_filename
        else:
            Config.__get__logger().warn("Setting config_filename on already initialized class. Using '%s'"
                                        % Config._get_config_filename())

    @staticmethod
    def _get_config_filename():
        if not Config._config_filename:
            Config._set_config_filename(CONFIG_FILENAME)

        return Config._config_filename

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            filename = Config._get_config_filename()
            Config.__get__logger().info("Creating Config._instance from '%s'" % filename)
            with open(filename) as file:
                lines = file.read().splitlines()

            Config.props = dict()
            for line in lines:
                if line.strip() == "" or line.startswith("#"):
                    pass
                else:
                    k, v = line.split("=")
                    Config.props[k.strip()] = v.strip()

            Config.__get__logger().info("Found %d entries in '%s'" % (len(Config.props), filename))
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def __drop__(self):
        Config._instance = None

    def prop(self, key, default_value=None):
        value = default_value
        try:
            value = self.props[key]
        except KeyError:
            pass

        return value

    def boolean_prop(self, key, default_value=False):
        value = self.prop(key, str(default_value))
        return "True" == value

    def __set_prop__(self, key, value):
        self.props[key] = value

