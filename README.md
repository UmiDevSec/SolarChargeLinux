# SolarChargeLinux
Get realtime stats from your solar charge controller via Python for controllers that use PVChargePro app

Steps to get this to work:
1. Run `sudo hcitool lescan` to identify the MAC of our solar charge controller
2. In `main.py` put the MAC of your charge controller in the `ADDRESS` variable
