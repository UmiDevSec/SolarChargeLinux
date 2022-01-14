# SolarChargeLinux
Get realtime stats from your Bluetooth equipped solar charge controller. \
Should work for any controller that uses the PVChargePro app (no guarantees).

## QuickStart
Steps to get this to work:
1. Run `sudo hcitool lescan` to identify the MAC of our solar charge controller
2. In `main.py` put the MAC of your charge controller in the `ADDRESS` variable
3. Run with `python main.py`


## Where's the data?
Voltage, Current, and Watts (realtime) for the Battery, Load, and Solar are save to seperate files in /tmp.

   - /tmp/battery_voltage
   - /tmp/battery_current
   - /tmp/battery_watts
   - /tmp/load_voltage
   - /tmp/load_current
   - /tmp/load_watts
   - /tmp/solar_voltage

If the Load is currently enabled `/tmp/is_load_on` will have the value `True` otherwise `False`.

   - /tmp/is_load_on

## How do I turn the load on/off?

To turn ON: `echo "on" > /tmp/load_action`

To turn OFF: `echo "off" > /tmp/load_action`
