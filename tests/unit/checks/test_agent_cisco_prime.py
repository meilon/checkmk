#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Mapping

import pytest

from tests.testlib import SpecialAgent

from cmk.base.command_config import SpecialAgentInfoFunctionResult

pytestmark = pytest.mark.checks


@pytest.mark.parametrize(
    "params, hostname, ipaddress, args",
    [
        (
            {
                "basicauth": ("bla", ("password", "123")),
                "port": 8080,
                "no-tls": True,
                "no-cert-check": True,
                "timeout": 60,
            },
            "myhost",
            "127.0.0.1",
            [
                "--hostname",
                "127.0.0.1",
                "-u",
                "bla:123",
                "--port",
                "8080",
                "--no-tls",
                "--no-cert-check",
                "--timeout",
                "60",
            ],
        ),
        (
            {},
            "hostname",
            "ipaddress",
            [
                "--hostname",
                "ipaddress",
            ],
        ),
        (
            {
                "host": "host_name",
            },
            "hostname",
            "ipaddress",
            [
                "--hostname",
                "hostname",
            ],
        ),
        (
            {"host": ("custom", {"host": "custom"})},
            "hostname",
            "ipaddress",
            [
                "--hostname",
                "custom",
            ],
        ),
    ],
)
def test_cisco_prime_argument_parsing(
    params: Mapping[str, object],
    hostname: str,
    ipaddress: str,
    args: SpecialAgentInfoFunctionResult,
) -> None:
    agent = SpecialAgent("agent_cisco_prime")
    arguments = agent.argument_func(params, hostname, ipaddress)
    assert arguments == args
