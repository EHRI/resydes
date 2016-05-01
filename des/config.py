#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, os.path

# The default configuration file.
CONFIG_FILENAME = "config.txt"


class Config(object):
    """
    Facility class for configuration. Config is a singleton object that can be obtained by calling the public
    constructor Config(). Config expects a configuration file that can be set with the static method
    __set_config_filename__(config_filename) before calling the constructor. After a singleton has been created,
    Config can be forced to read the configuration file again by calling __drop__() on the singleton instance
    and calling the constructor again.
    """

    _config_filename = CONFIG_FILENAME

    key_logging_configuration_file = "logging_configuration_file"
    key_location_mapper_destination_file = "location_mapper_destination_file"
    key_destination_root = "destination_root"
    key_use_netloc = "use_netloc"
    key_use_checksum = "use_checksum"
    key_audit_only = "audit_only"
    key_sync_status_report_file = "sync_status_report_file"
    key_sync_pause = "sync_pause"
    key_des_processor_listeners = "des_processor_listeners"
    key_des_dump_listeners = "des_dump_listeners"

    @staticmethod
    def __get_logger__():
        logger = logging.getLogger(__name__)
        return logger

    @staticmethod
    def __set_config_filename__(config_filename):
        if Config.__instance__ is None:
            Config.__get_logger__().info("Setting config_filename to '%s'", config_filename)
            Config._config_filename = config_filename
        else:
            Config.__get_logger__().warn("Setting config_filename on already initialized class. Using '%s'"
                                         % Config.__get_config_filename__())

    @staticmethod
    def __get_config_filename__():
        if not Config._config_filename:
            Config.__set_config_filename__(CONFIG_FILENAME)

        return Config._config_filename

    __instance__ = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance__:
            filename = Config.__get_config_filename__()
            Config.__get_logger__().info("Creating Config._instance from '%s'" % filename)
            with open(filename) as file:
                lines = file.read().splitlines()

            Config.props = dict()
            for line in lines:
                if line.strip() == "" or line.startswith("#"):
                    pass
                else:
                    k, v = line.split("=")
                    Config.props[k.strip()] = v.strip()

            Config.__get_logger__().info("Found %d entries in '%s'" % (len(Config.props), filename))
            cls.__instance__ = super(Config, cls).__new__(cls, *args, **kwargs)

        return cls.__instance__

    def __drop__(self):
        Config.__instance__ = None

    def prop(self, key, default_value=None):
        """
        Get the string value for the given key. Will return the given default_value if key is not found.
        :param key: the key for the property.
        :param default_value: the default value of the property (default = None).
        :return: string property for the given key or default_value if key is not found.
        """
        value = default_value
        try:
            value = self.props[key]
        except KeyError:
            pass
        return value

    def boolean_prop(self, key, default_value=False):
        """
        Get the boolean value for the given key or default_value if key not found.
        :param key: the key for the property
        :param default_value: the default value of the property (default = False).
        :return: boolean value for the given key or default_value if key not found
        """
        value = self.prop(key, str(default_value))
        return "True" == value

    def int_prop(self, key, default_value=0):
        """
        Get the integer value for the given key or default_value if key not found.
        :param key:
        :param default_value:
        :return:
        """
        value = self.prop(key, str(default_value))
        if value is None:
            return value
        return int(value)

    def list_prop(self, key, default_value=[]):
        """
        Get the list value for the given key or default_value if key not found.
        :param key:
        :param default_value:
        :return:
        """
        value = self.prop(key)
        if value is None:
            return default_value
        else:
            list = []
            values = value.split(",")
            for v in values:
                list.append(v.strip())
            return list

    def __set_prop__(self, key, value):
        self.props[key] = value

