#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# Note: Sometimes the esx_vsphere_sensors check reports incorrect sensor data.
# The reason is that the data is cached on the esx system. In the worst case some sensors
# might get stuck in an unhealthy state. You can find more information under the following link:
# http://kb.vmware.com/selfservice/microsites/search.do?cmd=displayKC&externalId=1037330

# <<<esx_vsphere_sensors:sep(59)>>>
# VMware Rollup Health State;;0;system;0;;red;Red;Sensor is operating under critical conditions
# Power Domain 1 Power Unit 0 - Redundancy lost;;0;power;0;;yellow;Yellow;Sensor is operating under conditions that are non-critical
# Power Supply 2 Power Supply 2 0: Power Supply AC lost - Assert;;0;power;0;;red;Red;Sensor is operating under critical conditions


from cmk.agent_based.legacy.v0_unstable import LegacyCheckDefinition
from cmk.agent_based.v2 import StringTable

check_info = {}


def inventory_esx_vsphere_sensors(info):
    yield None, {}


def check_esx_vsphere_sensors(_no_item, params, info):
    mulitline = ["All sensors are in normal state", "Sensors operating normal are:"]
    mod_msg = " (Alert state has been modified by Check_MK rule)"

    for (
        name,
        _base_units,
        _current_reading,
        _sensor_type,
        _unit_modifier,
        _rate_units,
        health_key,
        health_label,
        health_summary,
    ) in info:
        sensor_state = {"green": 0, "yellow": 1, "red": 2, "unknown": 3}.get(health_key.lower(), 2)
        txt = f"{name}: {health_label} ({health_summary})"

        for entry in params["rules"]:
            if name.startswith(entry.get("name", "")):
                new_state = entry.get("states", {}).get(str(sensor_state))
                if new_state is not None:
                    sensor_state = new_state
                    txt += mod_msg
                    break
        if sensor_state > 0 or txt.endswith(mod_msg):
            yield sensor_state, txt
            mulitline[:2] = "", "At least one sensor reported. Sensors readings are:"
        mulitline.append(txt)

    yield 0, "\n".join(mulitline)


def parse_esx_vsphere_sensors(string_table: StringTable) -> StringTable:
    return string_table


check_info["esx_vsphere_sensors"] = LegacyCheckDefinition(
    name="esx_vsphere_sensors",
    parse_function=parse_esx_vsphere_sensors,
    service_name="Hardware Sensors",
    discovery_function=inventory_esx_vsphere_sensors,
    check_function=check_esx_vsphere_sensors,
    check_ruleset_name="hostsystem_sensors",
    check_default_parameters={"rules": []},
)
