import unittest

import prepare_test_env
from calibration_tower.gcode import GCodeCommand, GCodeDescr

class test_GCode(unittest.TestCase):
    def test_parse_invalid_raises(self):
        with self.assertRaisesRegex(ValueError, 'Invalid'):
            GCodeCommand.parse('some line')

    def test_parse_valid_recognizes_parts(self):
        x = GCodeCommand.parse('G0 F10 E20 X10; what is that')

        self.assertEqual(x.code, 'G0')
        self.assertEqual(x.args, {'F': 10.0, 'E': 20.0, 'X': 10.0})
        self.assertEqual(x.comment, ' what is that')
        self.assertEqual(x.command, GCodeDescr.LINEAR_MOTION_COMMAND)

    def test_parse_valid_casts_to_string(self):
        x = GCodeCommand.parse('G0 F10 E20 X10; what is that')
        # FIXME: Order might differ
        self.assertEqual(str(x), 'G0 F10.0 X10.0 E20.0; what is that')

    def test_create_new_gcode(self):
        x = GCodeCommand.new(GCodeDescr.LINEAR_MOTION_COMMAND, F=10.0)
        self.assertEqual(x.code, 'G0')
        self.assertEqual(x.args, {'F': 10.0})
        self.assertEqual(str(x), 'G0 F10.0')
    
    def test_specify_comment_after_created_works(self):
        x = GCodeCommand.new(GCodeDescr.LINEAR_MOTION_COMMAND, F=10.0)
        x.comment = 'heh'
        self.assertEqual(str(x), 'G0 F10.0;heh')

    def test_parse_pure_comment_parse_doesnt_set_command_and_args(self):
        x = GCodeCommand.parse(';Some Comment line')
        self.assertEqual(x.comment, 'Some Comment line')
        self.assertEqual(x.code, None)
        self.assertEqual(x.args, {})
        self.assertEqual(str(x), ';Some Comment line')

    def test_create_pure_comment(self):
        x = GCodeCommand.new_comment('comment')
        self.assertEqual(str(x), ';comment')
        self.assertEqual(x.comment, 'comment')

    def test_create_complete_command_with_comment(self):
        x = GCodeCommand.new(GCodeDescr.LINEAR_MOTION_EXTRUDED_COMMAND, comment='constructor comment', X=10.0, Y=20.0, E=120.0)
        self.assertEqual(x.comment, 'constructor comment')
        self.assertEqual(x.args, {'X': 10.0, 'Y': 20.0, 'E': 120.0})
        self.assertEqual(x.code, 'G1')


if __name__ == '__main__':
    unittest.main()
