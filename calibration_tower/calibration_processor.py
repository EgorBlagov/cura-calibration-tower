import re
from collections import OrderedDict

from .gcode import GCodeCommand, GCodeDescr

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
