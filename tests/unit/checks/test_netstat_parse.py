#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Sequence

import pytest

from cmk.agent_based.v1.type_defs import StringTable

from .checktestlib import Check

pytestmark = pytest.mark.checks


@pytest.mark.parametrize(
    "info,expected_parsed",
    [
        ([], []),
        (
            [["tcp", "0", "0", "0.0.0.0:6556", "0.0.0.0:*", "LISTENING"]],
            [("TCP", ["0.0.0.0", "6556"], ["0.0.0.0", "*"], "LISTENING")],
        ),
        # Some AIX systems separate the port with a dot (.) instead of a colon (:)
        (
            [["tcp4", "0", "0", "127.0.0.1.1234", "127.0.0.1.5678", "ESTABLISHED"]],
            [("TCP", ["127.0.0.1", "1234"], ["127.0.0.1", "5678"], "ESTABLISHED")],
        ),
        # Solaris systems output a different format for udp (3 elements instead 5)
        (
            [["udp", "-", "-", "*.*", "0.0.0.0:*"]],
            [("UDP", ["*", "*"], ["0.0.0.0", "*"], "LISTENING")],
        ),
        # The ss command has a different order of columns
        (
            [
                ["tcp", "LISTENING", "0", "4096", "127.0.0.1:8888", "0.0.0.0:*"],
                ["udp", "UNCONN", "0", "0", "127.0.0.1:778", "0.0.0.0:*"],
            ],
            [
                ("TCP", ["127.0.0.1", "8888"], ["0.0.0.0", "*"], "LISTENING"),
                ("UDP", ["127.0.0.1", "778"], ["0.0.0.0", "*"], "LISTENING"),
            ],
        ),
    ],
)
def test_parse_netstat(
    info: StringTable, expected_parsed: Sequence[tuple[str, Sequence[str], Sequence[str], str]]
) -> None:
    parsed = Check("netstat").run_parse(info)
    assert parsed == expected_parsed
