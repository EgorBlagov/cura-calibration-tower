import json
from collections import OrderedDict

from ...Script import Script
from .calibration_processor import (CalibrationProcessor, LayerHeightDetector, MillimeterHeightDetector,
                              HotendTempProcessor, FlowProcessor, SpeedProcessor, FanProcessor,
                              PrintSpeedProcessor, RetractionSpeedProcessor, RetractionLengthProcessor,
                              LinearAdvanceProcessor)

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

