import logging
import json
from requests.exceptions import ConnectionError as ConnectError, HTTPError, Timeout
import voluptuous as vol
import time
from datetime import timedelta
from homeassistant.const import (CONF_NAME)
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

import requests
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'weiguoairSensor'
WEIGUOURL = 'http://weiguo.airradio.cn/smart/hwmobile/smart/'
KEY = 'ssdVBdpdshnefs'
_Log=logging.getLogger(__name__)


TYPES = {
    'temperature': ['temperature', '°C'],
    'co2': ['co2', 'ppm'],
    'voc': ['voc', None],
    'humidity': ['humidity', '%'],
    'pm25': ['pm25', 'μg/m3']
}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    sensor_name = config.get(CONF_NAME)

    dev = []
    if discovery_info is not None:
        # Not using hostname, as it seems to vary.
        # device = {'name': discovery_info['name'], 'mac': discovery_info['mac'],
        #           'update_interval': discovery_info['update_interval']}
        device = {'name': discovery_info['name'], 'mac': discovery_info['mac']}
        dev.append(weiguoairSensor(hass, device, None))
    else:
        for mac, device_config in config['devices'].items():
            # device = {'name': device_config['name'], 'mac': mac,
            #           'update_interval': device_config['update_interval']}
            device = {'name': device_config['name'], 'mac': mac}
            dev.append(weiguoairSensor(hass, device, device_config))

    add_devices(dev, True)

    # device update data
    def handle_data_update_event(call):
        # now = time.time()
        for device in dev:
            interval = 30
            # if device._update_interval is not None:
            #     interval = device._update_interval
            # else:
            #     interval = 60
            if device is not None:
                device.update(device._mac)
        hass.loop.call_later(30, handle_data_update_event, '')

    hass.loop.call_later(30, handle_data_update_event, '')
    return True

class weiguoairSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, hass, device, dev_conf):
        self._hass = hass
        self._device = device
        self._name = device['name']
        self._mac = device['mac']
        # self._update_interval = device['update_interval']
        self._config = dev_conf
        self._data = None
        self._icon = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    def update(self, mac):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        url = WEIGUOURL+'d002!retrieveRealData?SENSORID={0}&KEY={1}'.format(mac, KEY)
        resp = None
        try:
            resp = requests.get(url)
        except (ConnectError, HTTPError, Timeout, ValueError) as error:
            _LOGGER.error("Unable to connect to Dark Sky. %s", error)
            return

        rst_json = resp.json()
        print(rst_json)
        self._data = {}
        if rst_json is not None:
            if 'code' in rst_json and 'message' in rst_json:
                code = rst_json['code']
                message = rst_json['message']
                if code == '1' and message == '查询数据成功':
                    sensor_data = rst_json['dataObject'][0]['sensorList'][0]['air']
                    temperature = sensor_data['temperature']
                    co2 = sensor_data['co2']
                    voc = sensor_data['voc']
                    humidity = sensor_data['humidity']
                    pm25 = sensor_data['pm25']
                    self._data['temperature'] = temperature + TYPES['temperature'][1]
                    self._data['co2'] = temperature + TYPES['co2'][1]
                    self._data['voc'] = temperature
                    self._data['humidity'] = temperature + TYPES['humidity'][1]
                    self._data['pm25'] = temperature + TYPES['pm25'][1]

