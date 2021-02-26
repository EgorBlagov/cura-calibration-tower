from collections import OrderedDict

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

