import json
import re
from typing import List, Dict

from collections import OrderedDict

from ..Script import Script

class GCodeDescr:
    def __init__(self, code, arguments):
        self.code = code
        self.arguments = OrderedDict(arguments)

    @staticmethod
    def get_all_commands():
        result = []
        for param in dir(GCodeDescr):
            if param.endswith('_COMMAND'):
                result.append(getattr(GCodeDescr, param))

        return result

    @staticmethod
    def get(code):
        for c in GCodeDescr.get_all_commands():
            if c.code == code:
                return c

        return None

GCodeDescr.LINEAR_MOTION_COMMAND          = GCodeDescr('G0',   [('F', float), ('X', float), ('Y', float), ('Z', float), ('E', float)])
GCodeDescr.LINEAR_MOTION_EXTRUDED_COMMAND = GCodeDescr('G1',   [('F', float), ('X', float), ('Y', float), ('Z', float), ('E', float)])
GCodeDescr.SET_HOTENT_TEMP_COMMAND        = GCodeDescr('M104', [('B', int), ('F', type(None)), ('I', int), ('S', int), ('T', int)])
GCodeDescr.SET_FLOW_COMMAND               = GCodeDescr('M221', [('S', int), ('T', int)])
GCodeDescr.SET_FEEDRATE_COMMAND           = GCodeDescr('M220', [('S', int), ('B', type(None)), ('R', type(None))])
GCodeDescr.SET_FAN_SPEED_COMMAND          = GCodeDescr('M106', [('I', int), ('P', int), ('S', int), ('T', int)])
GCodeDescr.SET_LINEAR_ADVANCE_FACTOR      = GCodeDescr('M900', [('K', float), ('L', float), ('S', int), ('T', int)])

class GCodeCommand:
    '''
    >>> GCodeCommand.parse('some line')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "test.py", line 136, in parse
        raise ValueError('Invalid GCode "{}"'.format(line))
    ValueError: Invalid GCode "some line"

    >>> x = GCodeCommand.parse('G0 F10 E20 X10; what is that')
    >>> assert x.code == 'G0'
    >>> assert x.args == {'F': 10.0, 'E': 20.0, 'X': 10.0}
    >>> assert str(x) == 'G0 F10.0 X10.0 E20.0; what is that', '{} != {}'.format(str(x), 'G0 F10.0 E20.0 X10.0; what is that')
    >>> assert x.comment == ' what is that'
    >>> assert x.command == GCodeDescr.LINEAR_MOTION_COMMAND

    >>> x = GCodeCommand.new(GCodeDescr.LINEAR_MOTION_COMMAND, F=10.0)
    >>> assert x.code == 'G0'
    >>> assert x.args == {'F': 10.0}
    >>> assert str(x) == 'G0 F10.0'
    >>> assert x.comment == ''
    >>> x.comment = 'heh'
    >>> assert str(x) == 'G0 F10.0;heh'

    >>> x = GCodeCommand.parse(';Some Comment line')
    >>> assert x.comment == 'Some Comment line'
    >>> assert x.code == None
    >>> assert x.args == {}
    >>> assert str(x) == ';Some Comment line'

    >>> x = GCodeCommand.new_comment('comment')
    >>> assert str(x) == ';comment'
    >>> assert x.comment == 'comment'

    >>> x = GCodeCommand.new(GCodeDescr.LINEAR_MOTION_EXTRUDED_COMMAND, comment='constructor comment', X=10.0, Y=20.0, E=120.0)
    >>> assert x.comment == 'constructor comment'
    >>> assert x.args == {'X': 10.0, 'Y': 20.0, 'E': 120.0}
    >>> assert x.code == 'G1'
    '''

    PRECISION = 5

    def __init__(self, code=None, args=None, comment=''):
        self.code = code
        self.args = args if args else {}
        self.comment = comment

    @property
    def command(self):
        if self.code is None:
            return None

        return GCodeDescr.get(self.code)
    

    def __str__(self):
        result = ''
        if self.code:
            result += self.code

        if self.args:
            for k, v in self.args.items():
                result += ' {}{}'.format(k, round(v, GCodeCommand.PRECISION))

        if self.comment:
            result += ';{}'.format(self.comment)

        return result

    @staticmethod
    def parse(line):
        if not line:
            return GCodeCommand()

        if line[0] not in "GM;":
            raise ValueError('Invalid GCode "{}"'.format(line))

        command_tokens = line.split(';')
        tokens = [t for t in command_tokens[0].split(' ') if t] # split into non empty tokens
        comment = ' '.join(command_tokens[1:])

        if not tokens:
            return GCodeCommand(comment=comment)

        code = tokens[0]
        command = GCodeDescr.get(code)

        if command is None:
            raise ValueError('Unsupported GCode "{}"'.format(line))

        args = {}
        for arg, _type in command.arguments.items():
            for t in tokens[1:]:
                given_name = t[0]
                given_value = t[1:] if t[1:] else None

                if given_name == arg:
                    args[arg] = None if _type == type(None) else _type(given_value)
                    break

        return GCodeCommand(code=code, comment=comment, args=args)

        
    @staticmethod
    def new_comment(comment):
        return GCodeCommand(comment=comment)

    @staticmethod
    def new(command, comment='', **kwargs):
        result_args = {}
        for arg, value in kwargs.items():
            if arg not in command.arguments:
                raise ValueError('Invalid argument {} for command {}, supported are: {}'.format(
                    arg,
                    command.code,
                    ', '.join(list(command.arguments))
                ))

            if type(value) != command.arguments[arg]:
                raise ValueError('Invalid argument type for command {}, argument {} must be {}, but it is {}'.format(
                    command.code,
                    arg,
                    command.arguments[arg],
                    type(value)
                ))

            result_args[arg] = value

        return GCodeCommand(code=command.code, comment=comment, args=result_args)


class Retraction:
    NONE, RETRACTING, PRIMING, JUST_PRIMED = range(4)
    def __init__(self):
        self._last_e = 0
        self._e = 0
        self._last_retract = 0
        self._state = Retraction.NONE

    @property
    def last_retraction_length(self):
        return self._last_retract

    @property
    def state(self):
        return self._state

    def handle_new_line(self):
        if self._state == Retraction.PRIMING:
            self._state = Retraction.JUST_PRIMED
        elif self._state == Retraction.JUST_PRIMED:
            self._state = Retraction.NONE

    def handle_linear_motion(self, cmd):
        if cmd.command == GCodeDescr.LINEAR_MOTION_EXTRUDED_COMMAND:
            if 'E' in cmd.args:
                self._update_e(cmd.args['E'])

            if not any(k in cmd.args for k in 'XYZ') and 'E' in cmd.args:
                if self._last_e > self._e:
                    self._state = Retraction.RETRACTING
                    self._last_retract = self._last_e - self._e

                elif self._last_e < self._e:
                    self._state = Retraction.PRIMING

    def _update_e(self, new_e):
        self._last_e = self._e
        self._e = new_e

class PrinterHead:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.e = 0
        self.feedrate = 0
        self.temp = 0
        self.retraction = Retraction()

    def handle(self, line):
        self.retraction.handle_new_line()

        try:
            cmd = GCodeCommand.parse(line)

            if cmd.command in [GCodeDescr.LINEAR_MOTION_COMMAND, GCodeDescr.LINEAR_MOTION_EXTRUDED_COMMAND]:
                self._handle_linear_motion(cmd.args)
                self.retraction.handle_linear_motion(cmd)
            elif cmd.command in [GCodeDescr.SET_HOTENT_TEMP_COMMAND]:
                self._handle_set_hotend_temp(cmd.args)
        except:
            pass

    def _handle_linear_motion(self, args):
        if 'X' in args:
            self.x = args['X']

        if 'Y' in args:
            self.y = args['Y']

        if 'Z' in args:
            self.z = args['Z']

        if 'E' in args:
            self.e = args['E']

        if 'F' in args:
            self.feedrate = args['F']

    def _handle_set_hotend_temp(self, args):
        if 'S' in args:
            self.temp = args['S']


class HeightDetector:
    def __init__(self, offset, step_size, count):
        self._offset = offset
        self._step_size = step_size
        self._count = count
        self._just_reached_new_step = False
        self._current_step = 0

    @property
    def just_reached_new_step(self):
        return self._just_reached_new_step

    @property
    def current_step(self):
        return self._current_step

    def handle(self, line, head, layer):
        self._just_reached_new_step = False
        if layer is None:
            self._current_step = 0
            return

        step = self._calculate_step(line, head, layer)
        step = min(step, self._count)

        if step != self._current_step:
            self._just_reached_new_step = True

        self._current_step = step



    def normalize(self, current, offset, step):
        result = max(0, current - offset + 1)
        return (result + step - 1) // step

    def _calculate_step(self, line, head, layer):
        raise NotImplementedError

class LayerHeightDetector(HeightDetector):
    def _calculate_step(self, line, head, layer):
        return self.normalize(layer, self._offset, self._step_size)

class MillimeterHeightDetector(HeightDetector):
    def __init__(self, offset, step_size, count):
        super().__init__(offset, step_size, count)
        self._last_z = 0
    
    def _calculate_step(self, line, head, layer):
        if head.z != self._last_z:
            self._last_z = head.z
            return self.normalize(self._last_z, self._offset, self._step_size)

        return self._current_step

class Processor:
    def __init__(self, start, step):
        self.start = start
        self.step = step

    def _get_current_value(self, current_step):
        return self.start + (current_step - 1) * self.step

    def handle(self, marker, height_detector, head):
        raise NotImplementedError

class Marker:
    def __init__(self, line):
        self.lines_after = []
        self.line = line
        self.lines_before = []

class CalibrationProcessor:
    def __init__(self, height_detector, processors):
        self.height_detector = height_detector
        self.processors = processors
        self.head = PrinterHead()

    def process_data(self, data):
        new_data = []
        for group in data:
            new_lines = []
            current_layer = None
            for line in group.split('\n'):
                line = line.strip()
                if not line:
                    continue

                if current_layer is None:
                    current_layer = self._check_layer(line)

                self.head.handle(line)
                self.height_detector.handle(line, self.head, current_layer)

                marker = Marker(line)
                for processor in self.processors:
                    processor.handle(marker, self.height_detector, self.head)

                new_lines += marker.lines_before
                new_lines.append(marker.line)
                new_lines += marker.lines_after

            new_data.append('\n'.join(new_lines) + '\n')

        return new_data

    def _check_layer(self, line):
        m = re.match(r'^;LAYER:(\d+)', line)
        if m:
            return int(m.group(1))

        return None

class SingleCommandProcessor(Processor):
    def __init__(self, start, step):
        self.start = start
        self.step = step

    def handle(self, marker, height_detector, head):
        if height_detector.just_reached_new_step:
            value = self._get_current_value(height_detector.current_step)
            marker.lines_before.append(self._create_command(value))

    def _create_command(self, value):
        raise NotImplementedError

class HotendTempProcessor(SingleCommandProcessor):
    def _create_command(self, value):
        return str(GCodeCommand.new(GCodeDescr.SET_HOTENT_TEMP_COMMAND, S=int(value)))

class FlowProcessor(SingleCommandProcessor):
    def _create_command(self, value):
        return str(GCodeCommand.new(GCodeDescr.SET_FLOW_COMMAND, S=int(value)))

class SpeedProcessor(SingleCommandProcessor):
    def _create_command(self, value):
        return str(GCodeCommand.new(GCodeDescr.SET_FEEDRATE_COMMAND, S=int(value)))

class FanProcessor(SingleCommandProcessor):
    def _create_command(self, value):
        return str(GCodeCommand.new(GCodeDescr.SET_FAN_SPEED_COMMAND, S=int(min(100, value) / 100 * 255)))

class LinearAdvanceProcessor(SingleCommandProcessor):
    def _create_command(self, value):
        return str(GCodeCommand.new(GCodeDescr.SET_LINEAR_ADVANCE_FACTOR, K=float(value)))

class PrintSpeedProcessor(Processor):
    def handle(self, marker, height_detector, head):
        if height_detector.current_step:
            cmd = GCodeCommand.parse(marker.line)

            if cmd.command == GCodeDescr.LINEAR_MOTION_EXTRUDED_COMMAND:
                if head.retraction.state == Retraction.JUST_PRIMED or (head.retraction.state == Retraction.NONE and 'F' in cmd.args):
                    cmd.args['F'] = head.feedrate / 100 * self._get_current_value(height_detector.current_step)
                    marker.line = str(cmd)

class RetractionLengthProcessor(Processor):
    def handle(self, marker, height_detector, head):
        if height_detector.current_step:
            cmd = GCodeCommand.parse(marker.line)

            if cmd.command == GCodeDescr.LINEAR_MOTION_EXTRUDED_COMMAND:
                if head.retraction.state == Retraction.RETRACTING:
                    cmd.args['E'] = head.e + head.retraction.last_retraction_length - self._get_current_value(height_detector.current_step)
                    marker.line = str(cmd)

class RetractionSpeedProcessor(Processor):
    def __init__(self, start, step):
        super().__init__(start, step)
        self.start *= 60.0
        self.step *= 60.0

    def handle(self, marker, height_detector, head):
        if height_detector.current_step:
            cmd = GCodeCommand.parse(marker.line)

            if cmd.command == GCodeDescr.LINEAR_MOTION_EXTRUDED_COMMAND:
                if head.retraction.state in [Retraction.RETRACTING, Retraction.PRIMING]:
                    cmd.args['F'] = self._get_current_value(height_detector.current_step)
                    marker.line = str(cmd)
                    marker.lines_after.append(str(GCodeCommand.new(GCodeDescr.LINEAR_MOTION_EXTRUDED_COMMAND, F=head.feedrate)))


ENABLE_PROCESSING_PARAM = "enable_processing"
STEP_COUNT_PARAM = "step_count"

STEP_TYPE_PARAM = "step_type"
STEP_TYPE_MM = "mm"
STEP_TYPE_LAYER_COUNT = "layer_count"

START_MM_PARAM = "start_mm"
START_LC_PARAM = "start_lc"

STEP_MM_PARAM = "step_mm"
STEP_LC_PARAM = "step_lc"

CHANGE_SPEED_ENABLED_PARAM = "change_speed_enabled"
CHANGE_SPEED_VALUE_PARAM = "change_speed_value"
CHANGE_SPEED_STEP_PARAM = "change_speed_step"

CHANGE_PRINT_SPEED_ENABLED_PARAM = "change_print_speed_enabled"
CHANGE_PRINT_SPEED_VALUE_PARAM = "change_print_speed_value"
CHANGE_PRINT_SPEED_STEP_PARAM = "change_print_speed_step"

CHANGE_FLOW_ENABLED_PARAM = "change_flow_enabled"
CHANGE_FLOW_VALUE_PARAM = "change_flow_value"
CHANGE_FLOW_STEP_PARAM = "change_flow_step"

CHANGE_HOTEND_TEMP_ENABLED_PARAM = "change_hotend_temp_enabled"
CHANGE_HOTEND_TEMP_VALUE_PARAM = "change_hotend_temp_value"
CHANGE_HOTEND_TEMP_STEP_PARAM = "change_hotend_temp_step"

CHANGE_FAN_ENABLED_PARAM = "change_fan_enabled"
CHANGE_FAN_VALUE_PARAM = "change_fan_value"
CHANGE_FAN_STEP_PARAM = "change_fan_step"

CHANGE_RETRACT_ENABLED_PARAM = "change_retract_enabled"
CHANGE_RETRACT_LENGTH_ENABLED_PARAM = "change_retract_length_enabled"
CHANGE_RETRACT_LENGTH_VALUE_PARAM = "change_retract_length_value"
CHANGE_RETRACT_LENGTH_STEP_PARAM = "change_retract_length_step"

CHANGE_RETRACT_SPEED_ENABLED_PARAM = "change_retract_speed_enabled"
CHANGE_RETRACT_SPEED_VALUE_PARAM = "change_retract_speed_value"
CHANGE_RETRACT_SPEED_STEP_PARAM = "change_retract_speed_step"

CHANGE_LINEAR_ADVANCE_ENABLED_PARAM = "change_linear_advance_enabled"
CHANGE_LINEAR_ADVANCE_VALUE_PARAM = "change_linear_advance_value"
CHANGE_LINEAR_ADVANCE_STEP_PARAM = "change_linear_advance_step"
       

class CalibrationTower(Script):
    version = "1.0.0"
    def getSettingDataString(self):
        return json.dumps({
            "name": "CalibrationTower {}".format(self.version),
            "key": "CalibrationTower",
            "metadata": {},
            "version": 2,
            "settings": OrderedDict([
                (ENABLE_PROCESSING_PARAM, {
                    "label": "Enable",
                    "description": "Enable procssing in that plugin",
                    "type": "bool",
                    "default_value": True,
                }),
                (STEP_COUNT_PARAM, {
                    "label" : "Step count",
                    "description": "How many sections there are on the model",
                    "type": "int",
                    "default_value": 5,
                    "minimum_value": 1,
                }),
                (STEP_TYPE_PARAM, {
                    "label": "Step type",
                    "description": "Whether to use mm or layer count to set new value",
                    "type": "enum",
                    "options": {
                        STEP_TYPE_MM: "Millimeters",
                        STEP_TYPE_LAYER_COUNT: "Layer count"
                    },
                    "default_value": STEP_TYPE_MM,
                }),
                (START_MM_PARAM, {
                    "label": "Start offset Millimeters",
                    "description": "Where to start calibration",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0,
                    "minimum_value": 0,
                    "minimum_value_warning": 0.1,
                    "maximum_value_warning": 230, # take max z from printer profile
                    "enabled": "{} == '{}'".format(STEP_TYPE_PARAM, STEP_TYPE_MM)
                }),
                (START_LC_PARAM, {
                    "label": "Start offset Layers",
                    "description": "Where to start calibration",
                    "unit": "",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": -100,
                    "minimum_value_warning": -1,
                    "enabled": "{} == '{}'".format(STEP_TYPE_PARAM, STEP_TYPE_LAYER_COUNT)
                }),
                (STEP_MM_PARAM, {
                    "label": "Step Millimeters",
                    "description": "One section size",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0,
                    "minimum_value": 0,
                    "minimum_value_warning": 0.1,
                    "maximum_value_warning": 230, # take max z from printer profile
                    "enabled": "{} == '{}'".format(STEP_TYPE_PARAM, STEP_TYPE_MM)
                }),
                (STEP_LC_PARAM, {
                    "label": "Step Layers",
                    "description": "One section size",
                    "unit": "",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": -100,
                    "minimum_value_warning": -1,
                    "enabled": "{} == '{}'".format(STEP_TYPE_PARAM, STEP_TYPE_LAYER_COUNT)
                }),
                (CHANGE_SPEED_ENABLED_PARAM, {
                    "label": "Change Speed",
                    "description": "Select if total speed (print and travel) has to be changed",
                    "type": "bool",
                    "default_value": False,
                }),
                (CHANGE_SPEED_VALUE_PARAM, {
                    "label": "Speed",
                    "description": "New total speed (print and travel)",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "200",
                    "enabled": CHANGE_SPEED_ENABLED_PARAM
                }),
                (CHANGE_SPEED_STEP_PARAM, {
                    "label": "Speed step",
                    "description": "Speed step",
                    "unit": "%",
                    "type": "int",
                    "default_value": 10,
                    "enabled": CHANGE_SPEED_ENABLED_PARAM
                }),
                (CHANGE_PRINT_SPEED_ENABLED_PARAM, {
                    "label": "Change Print Speed",
                    "description": "Select if print speed has to be changed",
                    "type": "bool",
                    "default_value": False
                }),
                (CHANGE_PRINT_SPEED_VALUE_PARAM, {
                    "label": "Print Speed",
                    "description": "New print speed",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "200",
                    "enabled": CHANGE_PRINT_SPEED_ENABLED_PARAM
                }),
                (CHANGE_PRINT_SPEED_STEP_PARAM, {
                    "label": "Print Speed step",
                    "description": "Print Speed step",
                    "unit": "%",
                    "type": "int",
                    "default_value": 10,
                    "enabled": CHANGE_PRINT_SPEED_ENABLED_PARAM
                }),
                (CHANGE_FLOW_ENABLED_PARAM, {
                    "label": "Change Flow Rate",
                    "description": "Select if flow rate has to be changed",
                    "type": "bool",
                    "default_value": False
                }),
                (CHANGE_FLOW_VALUE_PARAM, {
                    "label": "Flow Rate",
                    "description": "New Flow rate",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "200",
                    "enabled": CHANGE_FLOW_ENABLED_PARAM
                }),
                (CHANGE_FLOW_STEP_PARAM, {
                    "label": "Flow rate step",
                    "description": "Flow rate step",
                    "unit": "%",
                    "type": "int",
                    "default_value": 10,
                    "enabled": CHANGE_FLOW_ENABLED_PARAM
                }),
                (CHANGE_HOTEND_TEMP_ENABLED_PARAM, {
                    "label": "Change Extruder 1 Temp",
                    "description": "Select if First Extruder Temperature has to be changed",
                    "type": "bool",
                    "default_value": False
                }),
                (CHANGE_HOTEND_TEMP_VALUE_PARAM, {
                    "label": "Extruder 1 Temp",
                    "description": "New First Extruder Temperature",
                    "unit": "C",
                    "type": "float",
                    "default_value": 190,
                    "minimum_value": "0",
                    "minimum_value_warning": "160",
                    "maximum_value_warning": "250",
                    "enabled": CHANGE_HOTEND_TEMP_ENABLED_PARAM
                }),
                (CHANGE_HOTEND_TEMP_STEP_PARAM, {
                    "label": "Extruder Temp step",
                    "description": "Extruder Temp step",
                    "unit": "C",
                    "type": "float",
                    "default_value": 10,
                    "enabled": CHANGE_HOTEND_TEMP_ENABLED_PARAM
                }),
                (CHANGE_FAN_ENABLED_PARAM, {
                    "label": "Change Fan Speed",
                    "description": "Select if Fan Speed has to be changed",
                    "type": "bool",
                    "default_value": False
                }),
                (CHANGE_FAN_VALUE_PARAM, {
                    "label": "Fan Speed",
                    "description": "New Fan Speed (0-100)",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": CHANGE_FAN_ENABLED_PARAM
                }),
                (CHANGE_FAN_STEP_PARAM, {
                    "label": "Fan Speed step",
                    "description": "Fan Speed step",
                    "unit": "%",
                    "type": "int",
                    "default_value": 10,
                    "enabled": CHANGE_FAN_ENABLED_PARAM
                }),
                (CHANGE_RETRACT_ENABLED_PARAM, {
                    "label": "Change Retraction",
                    "description": "Indicates you would like to modify retraction properties.",
                    "type": "bool",
                    "default_value": False
                }),
                (CHANGE_RETRACT_LENGTH_ENABLED_PARAM, {
                    "label": "Change Retract Length",
                    "description": "Changes the retraction length during print",
                    "type": "bool",
                    "default_value": False,
                    "enabled": CHANGE_RETRACT_ENABLED_PARAM
                }),
                (CHANGE_RETRACT_LENGTH_VALUE_PARAM, {
                    "label": "Retract Length",
                    "description": "New Retract Length (mm)",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 6,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "20",
                    "enabled": "{} and {}".format(CHANGE_RETRACT_ENABLED_PARAM, CHANGE_RETRACT_LENGTH_ENABLED_PARAM)
                }),
                (CHANGE_RETRACT_LENGTH_STEP_PARAM, {
                    "label": "Retract Length step",
                    "description": "Retract Length step",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.5,
                    "enabled": "{} and {}".format(CHANGE_RETRACT_ENABLED_PARAM, CHANGE_RETRACT_LENGTH_ENABLED_PARAM)
                }),
                (CHANGE_RETRACT_SPEED_ENABLED_PARAM, {
                    "label": "Change Retract Feed Rate",
                    "description": "Changes the retraction feed rate during print",
                    "type": "bool",
                    "default_value": False,
                    "enabled": CHANGE_RETRACT_ENABLED_PARAM
                }),
                (CHANGE_RETRACT_SPEED_VALUE_PARAM, {
                    "label": "Retract Feed Rate",
                    "description": "New Retract Feed Rate (mm/s)",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 40,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "{} and {}".format(CHANGE_RETRACT_ENABLED_PARAM, CHANGE_RETRACT_SPEED_ENABLED_PARAM)
                }),
                (CHANGE_RETRACT_SPEED_STEP_PARAM, {
                    "label": "Retract Feed Rate step",
                    "description": "Retract Feed Rate step",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 5,
                    "enabled": "{} and {}".format(CHANGE_RETRACT_ENABLED_PARAM, CHANGE_RETRACT_SPEED_ENABLED_PARAM)
                }),
                (CHANGE_LINEAR_ADVANCE_ENABLED_PARAM, {
                    "label": "Change Linear Advance K Factor",
                    "description": "Changes Linear Advance K Factor",
                    "type": "bool",
                    "default_value": False,
                }),
                (CHANGE_LINEAR_ADVANCE_VALUE_PARAM, {
                    "label": "K Factor",
                    "description": "K Factor",
                    "type": "float",
                    "default_value": 0.2,
                    "minimum_value": 0,
                    "enabled": CHANGE_LINEAR_ADVANCE_ENABLED_PARAM
                }),
                (CHANGE_LINEAR_ADVANCE_STEP_PARAM, {
                    "label": "K Factor step",
                    "description": "K Factor step",
                    "type": "float",
                    "default_value": 0.1,
                    "enabled": CHANGE_LINEAR_ADVANCE_ENABLED_PARAM
                }),
            ])
        })

    def execute(self, data):
        if self._get(ENABLE_PROCESSING_PARAM):
            return self._create_processor().process_data(data)

        return data

    def _get(self, key, cast=None):
        result = self.getSettingValueByKey(key)
        if result is None:
            return result

        if cast is not None:
            result = cast(result)

        return result

    def _create_processor(self):
        height_detector = self._create_height_detector(
            self._get(STEP_TYPE_PARAM),
            self._get(START_MM_PARAM),
            self._get(STEP_MM_PARAM),
            self._get(START_LC_PARAM),
            self._get(STEP_LC_PARAM),
            self._get(STEP_COUNT_PARAM),
        )

        processors = []

        if self._get(CHANGE_SPEED_ENABLED_PARAM):
            processors.append(
                SpeedProcessor(
                    self._get(CHANGE_SPEED_VALUE_PARAM),
                    self._get(CHANGE_SPEED_STEP_PARAM),
                )
            )

        if self._get(CHANGE_PRINT_SPEED_ENABLED_PARAM):
            processors.append(
                PrintSpeedProcessor(
                    self._get(CHANGE_PRINT_SPEED_VALUE_PARAM),
                    self._get(CHANGE_PRINT_SPEED_STEP_PARAM),
                )
            )

        if self._get(CHANGE_FLOW_ENABLED_PARAM):
            processors.append(
                FlowProcessor(
                    self._get(CHANGE_FLOW_VALUE_PARAM),
                    self._get(CHANGE_FLOW_STEP_PARAM),
                )
            )

        if self._get(CHANGE_HOTEND_TEMP_ENABLED_PARAM):
            processors.append(
                HotendTempProcessor(
                    self._get(CHANGE_HOTEND_TEMP_VALUE_PARAM),
                    self._get(CHANGE_HOTEND_TEMP_STEP_PARAM),
                )
            )

        if self._get(CHANGE_FAN_ENABLED_PARAM):
            processors.append(
                FanProcessor(
                    self._get(CHANGE_FAN_VALUE_PARAM),
                    self._get(CHANGE_FAN_STEP_PARAM),
                )
            )

        if self._get(CHANGE_LINEAR_ADVANCE_ENABLED_PARAM):
            processors.append(
                LinearAdvanceProcessor(
                    self._get(CHANGE_LINEAR_ADVANCE_VALUE_PARAM),
                    self._get(CHANGE_LINEAR_ADVANCE_STEP_PARAM),
                )
            )

        if self._get(CHANGE_RETRACT_ENABLED_PARAM):
            if self._get(CHANGE_RETRACT_LENGTH_ENABLED_PARAM):
                processors.append(
                    RetractionLengthProcessor(
                        self._get(CHANGE_RETRACT_LENGTH_VALUE_PARAM),
                        self._get(CHANGE_RETRACT_LENGTH_STEP_PARAM),
                    )
                )

            if self._get(CHANGE_RETRACT_SPEED_ENABLED_PARAM):
                processors.append(
                    RetractionSpeedProcessor(
                        self._get(CHANGE_RETRACT_SPEED_VALUE_PARAM),
                        self._get(CHANGE_RETRACT_SPEED_STEP_PARAM),
                    )
                )

        return CalibrationProcessor(
            height_detector=height_detector,
            processors=processors
        )


    def _create_height_detector(self, _type, mm_start, mm_step, lc_start, lc_step, count):
        if _type == STEP_TYPE_MM:
            return MillimeterHeightDetector(mm_start, mm_step, count)

        return LayerHeightDetector(lc_start, lc_step, count)

