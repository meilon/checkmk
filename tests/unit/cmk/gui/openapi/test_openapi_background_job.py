#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import pytest

from tests.testlib.rest_api_client import ClientRegistry

from cmk.gui.watolib.bulk_discovery import BulkDiscoveryBackgroundJob


class TestBackgroundJobSnapshot:
    @pytest.mark.usefixtures("inline_background_jobs")
    def test_openapi_background_job_snapshot(self, base: str, clients: ClientRegistry) -> None:
        clients.HostConfig.create(host_name="foobar")
        clients.ServiceDiscovery.bulk_discovery(hostnames=["foobar"])

        job_id = BulkDiscoveryBackgroundJob.job_prefix
        resp = clients.BackgroundJob.get(job_id=job_id)

        assert resp.json["id"] == BulkDiscoveryBackgroundJob.job_prefix
