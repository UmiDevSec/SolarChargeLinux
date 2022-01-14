#!/usr/bin/env python

import asyncio

from bleak import BleakClient


CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
# Run `hcitool lescan` to find the mac address of your Solar Controller
ADDRESS = "00:11:22:33:44:55"
BATTERY_CMD = bytes([0x01, 0x03, 0x01, 0x01, 0x00, 0x03, 0x55, 0xF7])
SECOND_CMD = bytes([0x01, 0x03, 0x01, 0x04, 0x00, 0x05, 0xC5, 0xF4])
THIRD_CMD = bytes([0x01, 0x03, 0x01, 0x09, 0x00, 0x07, 0xD5, 0xF6])
TURN_LOAD_ON_CMD = bytes([0x01, 0x06, 0x01, 0x20, 0xFF, 0xFF, 0x88, 0x4C])
TURN_LOAD_OFF_CMD = bytes([0x01, 0x06, 0x01, 0x20, 0x00, 0x00, 0x89, 0xFC])

# ENUM
BATT_V = "battery_voltage"
BATT_I = "battery_current"
BATT_W = "battery_watts"
LOAD_V = "load_voltage"
LOAD_I = "load_current"
LOAD_W = "load_watts"
LOAD_ON = "is_load_on"
PV_V = "solar_voltage"

ENUMS = [BATT_V, BATT_I, BATT_W, LOAD_V, LOAD_I, LOAD_W, LOAD_ON, PV_V]

status = {BATT_V: -1, BATT_I: -1, BATT_W: -1, LOAD_V: -
          1, LOAD_I: -1, LOAD_W: -1, LOAD_ON: None, PV_V: -1}


def update(item, value):
    """Keep track of metrics (voltage, amps, etc.) and persist to disk."""
    if status[item] != value:
        status[item] = value
        f = open("/tmp/"+item, "w")
        f.write(str(value))
        f.close()


def check_load_action():
    """Look for a file indicating the load should be turned on or off."""
    try:
        f = open("/tmp/load_action", "r")
        load_action = f.read().rstrip('\n')
        f.close()
        if(load_action == "on" and (not status[LOAD_ON])):
            return True
        if(load_action == "off" and status[LOAD_ON]):
            return False
        # TODO(UmiDevSec): Should probably unlink the tmp file.
    except FileNotFoundError:
        pass
    return None


def load_last_statuses():
    """Load metrics (voltage, amps, etc.) persisted to disk (if they exist)."""
    for item in ENUMS:
        try:
            filename = "/tmp/"+item
            f = open(filename, "r")
            value = f.read().rstrip('\n')
            try:
                status[item] = float(value)
            except ValueError:
                if value == "True":
                    status[item] = True
                elif value == "False":
                    status[item] = False
                else:
                    status[item] = value
            f.close()
        except FileNotFoundError:
            pass


def notification_handler(_, data):
    """Recieve data from charge controller via notificaitons.."""
    # Different lengths of responses indicate the type
    # of message. Wish there were a better way ...
    data_len = len(data)
    if data_len == 11:
        update(BATT_V, ((data[5] * 256 + data[6])/10))
        update(BATT_I, ((data[7] * 256 + data[8])/100))
    if data_len == 15:
        update(BATT_W, (data[3] * 256 + data[4]))
        update(LOAD_V, ((data[7] * 256 + data[8])/10))
        update(LOAD_I, ((data[9] * 256 + data[10])/100))
        update(LOAD_W, (data[11] * 256 + data[12]))
    if data_len == 19:
        update(PV_V, (data[3] * 256 + data[4]) / 10)
        update(LOAD_ON, ((data[11] / 256) > 0))


async def turn_load_on(client):
    """Causes charge controller to turn on load."""
    await client.write_gatt_char(CHARACTERISTIC_UUID, TURN_LOAD_ON_CMD)


async def turn_load_off(client):
    """Causes charge controller to turn off load."""
    await client.write_gatt_char(CHARACTERISTIC_UUID, TURN_LOAD_OFF_CMD)


async def main(address, char_uuid):
    """Connects to charge controller, toggles load, retrieves latest metrics."""
    # If volts, amps, etc. persisted to disk from previous run
    # load them to compare against. This avoid excess disk writes.
    load_last_statuses()
    async with BleakClient(address) as client:

        await client.start_notify(char_uuid, notification_handler)
        # If a temp file exists indicating that the load should be
        # turned on or off then issue the respective command.
        load_action = check_load_action()
        if load_action is not None:
            if load_action:
                await turn_load_on(client)
            else:
                await turn_load_off(client)
            await asyncio.sleep(5.0)
        await asyncio.sleep(1.0)
        await client.write_gatt_char(CHARACTERISTIC_UUID, BATTERY_CMD)
        await asyncio.sleep(0.5)
        await client.write_gatt_char(CHARACTERISTIC_UUID, SECOND_CMD)
        await asyncio.sleep(0.5)
        await client.write_gatt_char(CHARACTERISTIC_UUID, THIRD_CMD)
        await asyncio.sleep(2.0)
        await client.stop_notify(char_uuid)


if __name__ == "__main__":
    asyncio.run(
        main(ADDRESS, CHARACTERISTIC_UUID)
    )
