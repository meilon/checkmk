#!/usr/bin/env python3
# Copyright (C) 2025 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import datetime
import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from livestatus import SiteConfigurations, SiteId

from cmk.ccc import store

from cmk.utils import paths
from cmk.utils.user import UserId

import cmk.ec.export as ec  # pylint: disable=cmk-module-layer-violation

from cmk.gui.config import active_config
from cmk.gui.cron import CronJob, CronJobRegistry
from cmk.gui.http import request
from cmk.gui.i18n import _
from cmk.gui.job_scheduler import load_last_job_runs, save_last_job_runs
from cmk.gui.log import logger
from cmk.gui.message import get_gui_messages, Message, message_gui
from cmk.gui.site_config import get_site_config, is_wato_slave_site
from cmk.gui.sites import states
from cmk.gui.userdb import load_users
from cmk.gui.utils import gen_id
from cmk.gui.utils.roles import user_may
from cmk.gui.watolib.analyze_configuration import ACResultState, ACTestResult, perform_tests

from cmk.discover_plugins import addons_plugins_local_path, plugins_local_path
from cmk.mkp_tool import get_stored_manifests, Manifest, PackageStore, PathConfig


def reset_scheduling() -> None:
    save_last_job_runs(
        {
            ident: datetime
            for ident, datetime in load_last_job_runs().items()
            if ident != "execute_deprecation_tests_and_notify_users"
        }
    )


@dataclass(frozen=True)
class _MarkerFileStore:
    _folder: Path

    def save(
        self, site_id: SiteId, site_version: str, ac_test_results: Sequence[ACTestResult]
    ) -> None:
        marker_file = self._folder / str(site_id) / site_version
        store.makedirs(marker_file.parent)
        store.save_text_to_file(marker_file, json.dumps([repr(r) for r in ac_test_results]))

    def cleanup_site_dir(self, site_id: SiteId) -> None:
        for filepath, _mtime in sorted(
            [
                (marker_file, marker_file.stat().st_mtime)
                for marker_file in list((self._folder / site_id).iterdir())
            ],
            key=lambda t: t[1],
            reverse=True,
        )[5:]:
            filepath.unlink(missing_ok=True)

    def cleanup_empty_dirs(self) -> None:
        for path in self._folder.iterdir():
            if path.is_dir() and not list(path.iterdir()):
                try:
                    path.rmdir()
                except OSError:
                    logger.error("Cannot remove %r", path)


def _filter_non_ok_ac_test_results(
    ac_test_results_by_site_id: Mapping[SiteId, Sequence[ACTestResult]],
) -> Mapping[SiteId, Sequence[ACTestResult]]:
    return {
        s: not_ok_rs
        for s, rs in ac_test_results_by_site_id.items()
        if (not_ok_rs := [r for r in rs if r.state is not ACResultState.OK])
    }


def _filter_extension_managing_users(user_ids: Sequence[UserId]) -> Sequence[UserId]:
    return [u for u in user_ids if user_may(u, "wato.manage_mkps")]


def _make_path_config() -> PathConfig | None:
    local_path = plugins_local_path()
    addons_path = addons_plugins_local_path()
    if local_path is None:
        return None
    if addons_path is None:
        return None
    return PathConfig(
        cmk_plugins_dir=local_path,
        cmk_addons_plugins_dir=addons_path,
        agent_based_plugins_dir=paths.local_agent_based_plugins_dir,
        agents_dir=paths.local_agents_dir,
        alert_handlers_dir=paths.local_alert_handlers_dir,
        bin_dir=paths.local_bin_dir,
        check_manpages_dir=paths.local_legacy_check_manpages_dir,
        checks_dir=paths.local_checks_dir,
        doc_dir=paths.local_doc_dir,
        gui_plugins_dir=paths.local_gui_plugins_dir,
        installed_packages_dir=paths.installed_packages_dir,
        inventory_dir=paths.local_inventory_dir,
        lib_dir=paths.local_lib_dir,
        locale_dir=paths.local_locale_dir,
        local_root=paths.local_root,
        mib_dir=paths.local_mib_dir,
        mkp_rule_pack_dir=ec.mkp_rule_pack_dir(),
        notifications_dir=paths.local_notifications_dir,
        pnp_templates_dir=paths.local_pnp_templates_dir,
        manifests_dir=paths.tmp_dir,
        web_dir=paths.local_web_dir,
    )


def _group_manifests_by_path(
    path_config: PathConfig, manifests: Sequence[Manifest]
) -> Mapping[Path, Manifest]:
    manifests_by_path: dict[Path, Manifest] = {}
    for manifest in manifests:
        for part, files in manifest.files.items():
            for file in files:
                manifests_by_path[Path(path_config.get_path(part)).resolve() / file] = manifest
    return manifests_by_path


def _find_manifest(
    manifests_by_path: Mapping[Path, Manifest], ac_test_result_path: Path
) -> Manifest | None:
    for path, manifest in manifests_by_path.items():
        if str(ac_test_result_path.resolve()).endswith(str(path)):
            return manifest
    return None


def _try_rel_path(site_id: SiteId, abs_path: Path) -> Path:
    try:
        return abs_path.relative_to(Path("/omd/sites", site_id))
    except ValueError:
        # Not a subpath, should not happen
        return abs_path


@dataclass(frozen=True)
class _ACTestResultProblem:
    ident: str
    type: Literal["mkp", "file", "unsorted"]
    _ac_test_results: dict[SiteId, list[ACTestResult]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert self.ident

    def add_ac_test_result(self, site_id: SiteId, ac_test_result: ACTestResult) -> None:
        self._ac_test_results.setdefault(site_id, []).append(ac_test_result)

    def __str__(self) -> str:
        match self.type:
            case "mkp":
                title = _("Extension package %r") % self.ident
            case "file":
                title = _("Unpackaged file %r") % self.ident
            case "unsorted":
                title = _("Unsorted")
        site_ids = sorted(self._ac_test_results)
        details = [
            f"{r.text} (file: {_try_rel_path(sid, r.path)})" if r.path else r.text
            for sid, rs in self._ac_test_results.items()
            for r in rs
        ]
        return f"{title}, sites: {', '.join(site_ids)}:<br>{',<br>'.join(details)}"


def _find_ac_test_result_problems(
    not_ok_ac_test_results: Mapping[SiteId, Sequence[ACTestResult]],
    manifests_by_path: Mapping[Path, Manifest],
) -> Sequence[_ACTestResultProblem]:
    problem_by_ident: dict[str, _ACTestResultProblem] = {}
    for site_id, ac_test_results in not_ok_ac_test_results.items():
        for ac_test_result in ac_test_results:
            if ac_test_result.path:
                path = _try_rel_path(site_id, ac_test_result.path)

                if manifest := _find_manifest(manifests_by_path, ac_test_result.path):
                    problem = problem_by_ident.setdefault(
                        manifest.name,
                        _ACTestResultProblem(manifest.name, "mkp"),
                    )
                else:
                    problem = problem_by_ident.setdefault(
                        str(path),
                        _ACTestResultProblem(str(path), "file"),
                    )

            else:
                problem = problem_by_ident.setdefault(
                    "unsorted",
                    _ACTestResultProblem("unsorted", "unsorted"),
                )

            problem.add_ac_test_result(site_id, ac_test_result)

    return list(problem_by_ident.values())


def execute_deprecation_tests_and_notify_users() -> None:
    if is_wato_slave_site():
        return

    marker_file_store = _MarkerFileStore(Path(paths.var_dir) / "deprecations")

    site_versions_by_site_id = {
        site_id: site_version
        for site_id, site_state in states().items()
        if (site_version := site_state.get("program_version"))
    }

    if not (
        not_ok_ac_test_results := _filter_non_ok_ac_test_results(
            perform_tests(
                logger,
                active_config,
                request,
                SiteConfigurations(
                    {
                        site_id: get_site_config(active_config, site_id)
                        for site_id in site_versions_by_site_id
                    }
                ),
                categories=["deprecations"],
            )
        )
    ):
        return

    for site_id, ac_test_results in not_ok_ac_test_results.items():
        marker_file_store.save(site_id, site_versions_by_site_id[site_id], ac_test_results)
        marker_file_store.cleanup_site_dir(site_id)

    marker_file_store.cleanup_empty_dirs()

    manifests_by_path = (
        _group_manifests_by_path(
            path_config,
            get_stored_manifests(
                PackageStore(
                    shipped_dir=paths.optional_packages_dir,
                    local_dir=paths.local_optional_packages_dir,
                    enabled_dir=paths.local_enabled_packages_dir,
                )
            ).local,
        )
        if (path_config := _make_path_config())
        else {}
    )

    ac_test_results_messages = [
        str(p) for p in _find_ac_test_result_problems(not_ok_ac_test_results, manifests_by_path)
    ]

    now = int(time.time())
    for user_id in _filter_extension_managing_users(list(load_users())):
        sent_messages = [m["text"] for m in get_gui_messages(user_id)]
        for ac_test_results_message in ac_test_results_messages:
            if ac_test_results_message in sent_messages:
                continue
            message_gui(
                user_id,
                Message(
                    dest=("list", [user_id]),
                    methods=["gui_hint"],
                    text=ac_test_results_message,
                    id=gen_id(),
                    time=now,
                    security=False,
                    acknowledged=False,
                ),
            )


def register(cron_job_registry: CronJobRegistry) -> None:
    cron_job_registry.register(
        CronJob(
            name="execute_deprecation_tests_and_notify_users",
            callable=execute_deprecation_tests_and_notify_users,
            interval=datetime.timedelta(days=1),
        )
    )
