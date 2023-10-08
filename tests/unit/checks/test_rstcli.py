#!/usr/bin/env python3
# Copyright (C) 2023 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from tests.testlib import Check

# Taken from https://forum.checkmk.com/t/monitoring-intel-vroc-with-rstcli/38613
INFO = [
    ["--VOLUME INFORMATION--"],
    ["Name", "                  System"],
    ["Raid Level", "            1"],
    ["Size", "                  300.00 GB"],
    ["StripeSize", "            N/A"],
    ["Num Disks", "             2"],
    ["State", "                 Normal"],
    ["System", "                True"],
    ["Bootable", "              True"],
    ["Initialized", "           False"],
    ["Cache Policy", "          Off"],
    ["--DISKS IN VOLUME", " System --"],
    ["ID", "                    0-0-0-0"],
    ["Type", "                  Disk"],
    ["Disk Type", "             SATA"],
    ["State", "                 Normal"],
    ["Size", "                  3576.98 GB"],
    ["System Disk", "           False"],
    ["Usage", "                 Array member"],
    ["Serial Number", "         123456789"],
    ["Model", "                 SAMSUNG MZ799999999999BLT-00A07"],
    ["Logical sector size", "   512 B"],
    ["ID", "                    0-1-0-0"],
    ["Type", "                  Disk"],
    ["Disk Type", "             SATA"],
    ["State", "                 Normal"],
    ["Size", "                  3576.98 GB"],
    ["System Disk", "           False"],
    ["Usage", "                 Array member"],
    ["Serial Number", "         987654321"],
    ["Model", "                 SAMSUNG MZ9999999T-00A07"],
    ["Logical sector size", "   512 B"],
    ["--VOLUME INFORMATION--"],
    ["Name", "                  SSD-SATA"],
    ["Raid Level", "            1"],
    ["Size", "                  3276.97 GB"],
    ["StripeSize", "            N/A"],
    ["Num Disks", "             2"],
    ["State", "                 Normal"],
    ["System", "                False"],
    ["Bootable", "              True"],
    ["Initialized", "           True"],
    ["Cache Policy", "          Off"],
    ["--DISKS IN VOLUME", " SSD-SATA --"],
    ["ID", "                    0-0-0-0"],
    ["Type", "                  Disk"],
    ["Disk Type", "             SATA"],
    ["State", "                 Normal"],
    ["Size", "                  3576.98 GB"],
    ["System Disk", "           False"],
    ["Usage", "                 Array member"],
    ["Serial Number", "         BBBBBBB"],
    ["Model", "                 SAMSUNG MZ99999999-00A07"],
    ["Logical sector size", "   512 B"],
    ["ID", "                    0-1-0-0"],
    ["Type", "                  Disk"],
    ["Disk Type", "             SATA"],
    ["State", "                 Normal"],
    ["Size", "                  3576.98 GB"],
    ["System Disk", "           False"],
    ["Usage", "                 Array member"],
    ["Serial Number", "         CCCCCC"],
    ["Model", "                 SAMSUNG MZ79999999999-00A07"],
    ["Logical sector size", "   512 B"],
    ["--VOLUME INFORMATION--"],
    ["Name", "                  SSD-NVME"],
    ["Raid Level", "            1"],
    ["Size", "                  3398.13 GB"],
    ["StripeSize", "            N/A"],
    ["Num Disks", "             2"],
    ["State", "                 Normal"],
    ["System", "                False"],
    ["Bootable", "              True"],
    ["Initialized", "           True"],
    ["Cache Policy", "          Off"],
    ["--DISKS IN VOLUME", " SSD-NVME --"],
    ["ID", "                    1-0-0-0"],
    ["Type", "                  Disk"],
    ["Disk Type", "             NVMe*"],
    ["State", "                 Normal"],
    ["Size", "                  3576.98 GB"],
    ["System Disk", "           False"],
    ["PCH Connected", "         False"],
    ["Usage", "                 Array member"],
    ["Serial Number", "         AAAAA"],
    ["Model", "                 Micron_7300_XXXXXX"],
    ["Logical sector size", "   512 B"],
    ["Socket Number", "         0"],
    ["Vmd Controller Number", " 4"],
    ["Root Port Offset", "      0"],
    ["Slot Number", "           272"],
    ["ID", "                    1-0-1-0"],
    ["Type", "                  Disk"],
    ["Disk Type", "             NVMe*"],
    ["State", "                 Normal"],
    ["Size", "                  3576.98 GB"],
    ["System Disk", "           False"],
    ["PCH Connected", "         False"],
    ["Usage", "                 Array member"],
    ["Serial Number", "         XXXXX"],
    ["Model", "                 Micron_7300_XXXXXXTDF"],
    ["Logical sector size", "   512 B"],
    ["Socket Number", "         0"],
    ["Vmd Controller Number", " 4"],
    ["Root Port Offset", "      1"],
    ["Slot Number", "           288"],
]

EXPECTED = {
    "SSD-NVME": {
        "Bootable": "True",
        "Cache Policy": "Off",
        "Disks": [
            {
                "Disk Type": "NVMe*",
                "ID": "1-0-0-0",
                "Logical sector size": "512 B",
                "Model": "Micron_7300_XXXXXX",
                "PCH Connected": "False",
                "Root Port Offset": "0",
                "Serial Number": "AAAAA",
                "Size": "3576.98 GB",
                "Slot Number": "272",
                "Socket Number": "0",
                "State": "Normal",
                "System Disk": "False",
                "Type": "Disk",
                "Usage": "Array member",
                "Vmd Controller Number": "4",
            },
            {
                "Disk Type": "NVMe*",
                "ID": "1-0-1-0",
                "Logical sector size": "512 B",
                "Model": "Micron_7300_XXXXXXTDF",
                "PCH Connected": "False",
                "Root Port Offset": "1",
                "Serial Number": "XXXXX",
                "Size": "3576.98 GB",
                "Slot Number": "288",
                "Socket Number": "0",
                "State": "Normal",
                "System Disk": "False",
                "Type": "Disk",
                "Usage": "Array member",
                "Vmd Controller Number": "4",
            },
        ],
        "Initialized": "True",
        "Num Disks": "2",
        "Raid Level": "1",
        "Size": "3398.13 GB",
        "State": "Normal",
        "StripeSize": "N/A",
        "System": "False",
    },
    "SSD-SATA": {
        "Bootable": "True",
        "Cache Policy": "Off",
        "Disks": [
            {
                "Disk Type": "SATA",
                "ID": "0-0-0-0",
                "Logical sector size": "512 B",
                "Model": "SAMSUNG MZ99999999-00A07",
                "Serial Number": "BBBBBBB",
                "Size": "3576.98 GB",
                "State": "Normal",
                "System Disk": "False",
                "Type": "Disk",
                "Usage": "Array member",
            },
            {
                "Disk Type": "SATA",
                "ID": "0-1-0-0",
                "Logical sector size": "512 B",
                "Model": "SAMSUNG MZ79999999999-00A07",
                "Serial Number": "CCCCCC",
                "Size": "3576.98 GB",
                "State": "Normal",
                "System Disk": "False",
                "Type": "Disk",
                "Usage": "Array member",
            },
        ],
        "Initialized": "True",
        "Num Disks": "2",
        "Raid Level": "1",
        "Size": "3276.97 GB",
        "State": "Normal",
        "StripeSize": "N/A",
        "System": "False",
    },
    "System": {
        "Bootable": "True",
        "Cache Policy": "Off",
        "Disks": [
            {
                "Disk Type": "SATA",
                "ID": "0-0-0-0",
                "Logical sector size": "512 B",
                "Model": "SAMSUNG MZ799999999999BLT-00A07",
                "Serial Number": "123456789",
                "Size": "3576.98 GB",
                "State": "Normal",
                "System Disk": "False",
                "Type": "Disk",
                "Usage": "Array member",
            },
            {
                "Disk Type": "SATA",
                "ID": "0-1-0-0",
                "Logical sector size": "512 B",
                "Model": "SAMSUNG MZ9999999T-00A07",
                "Serial Number": "987654321",
                "Size": "3576.98 GB",
                "State": "Normal",
                "System Disk": "False",
                "Type": "Disk",
                "Usage": "Array member",
            },
        ],
        "Initialized": "False",
        "Num Disks": "2",
        "Raid Level": "1",
        "Size": "300.00 GB",
        "State": "Normal",
        "StripeSize": "N/A",
        "System": "True",
    },
}


def test_parse():
    check = Check("rstcli")
    assert check.run_parse(INFO) == EXPECTED
