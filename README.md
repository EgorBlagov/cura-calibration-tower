# CalibrationTower

This is a Script for **[Ultimaker's CURA](!https://github.com/Ultimaker/Cura)** **PostProcessing Plugin**, providing simple way to configure calibration towers (for retraction, nozzle temperature and so on...).

# Features

When you want to find out what retraction length you need, or what temperature works best for your filament you want to run some kind of tower from thingiverse, but in CURA you don't have simple option for that. You can use **ChangeAtZ** post processing script, but you'll have to add it 8-10 times and each time configure what option you want to change and at what layer/height. It's not handy enough.

With this script you can specify initial offset, step height (mm or layers count), number of steps, options you want to modify, it's step and that's it.

## Supported options

- Feedrate multiplier (`M220`)
- Print speed multiplier (Modifying `G1` commands)
- Flow rate (`M221`)
- Extruder 1 nozzle temperature (`M104`, only 1 extruder supported at the moment)
- Fan speed percentage (`M106`)
- Retraction length and feedrate (Modifying `G1` commands)
- Linear Advance K-Factor (`M900`)

Tested with retraction length and feedrate, Linear Advance K-Factor and Hotend temperature, to find optimal values in my own prints (Ender 3 Pro, PLA and PETG).

# Installation and Usage

1. Go to CURA's Menu Bar -> Help -> Show Configuration Folder.
2. Place `CalibrationTower.py` to `scripts` directory in just opened folder.
3. Restart CURA
4. Menu Bar -> Extensions -> Post Processing -> Modify G-Code
5. Add a script -> **CalibrationTower**

# Support

- [PayPal](https://www.paypal.com/paypalme/emblagov)
- [Qiwi](https://qiwi.com/n/STRAL577)

# Contribution

Please, don't hesitate to submit a Pull-Request, or raise an Issue. I don't guarantee to resolve everything quickly, but at least I will know about issues or users wishes.

# For Devs

**PostProcessingPlugin** doesn't support packages, only single file scripts, that's why `bundler.py` was added. It reads source code starting from entry point and collects all importable code into single python script. But if I'll be able to contribute package support to **PostProcessingPlugin** the bundler won't be required anymore.

Under `tests` directory there are two files for now:

1. `debug.py` -- Reads data from sample GCODE, post processes it and saves to the file, so it can be debugged and compared using diff software.
2. `test_unit.py` -- Supposed to have unittests, at the moment it has only tests for GCODE manipulation classes.

# License

ISC © [Egor Blagov](https://github.com/EgorBlagov)
