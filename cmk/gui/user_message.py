#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import time
from collections.abc import Iterator

from cmk.gui import message
from cmk.gui.breadcrumb import Breadcrumb, make_simple_page_breadcrumb
from cmk.gui.htmllib.header import make_header
from cmk.gui.htmllib.html import html
from cmk.gui.http import request
from cmk.gui.i18n import _, ungettext
from cmk.gui.logged_in import user
from cmk.gui.main_menu import mega_menu_registry
from cmk.gui.page_menu import (
    make_simple_link,
    PageMenu,
    PageMenuDropdown,
    PageMenuEntry,
    PageMenuTopic,
)
from cmk.gui.pages import Page, PageRegistry
from cmk.gui.table import table_element
from cmk.gui.utils.csrf_token import check_csrf_token
from cmk.gui.utils.flashed_messages import flash, get_flashed_messages
from cmk.gui.utils.transaction_manager import transactions
from cmk.gui.utils.urls import make_confirm_delete_link, makeactionuri


def register(page_registry: PageRegistry) -> None:
    page_registry.register_page("user_message")(PageUserMessage)
    page_registry.register_page_handler("ajax_delete_user_message", ajax_delete_user_message)
    page_registry.register_page_handler(
        "ajax_acknowledge_user_message", ajax_acknowledge_user_message
    )


class PageUserMessage(Page):
    def title(self) -> str:
        return _("User messages")

    def page_menu(self, breadcrumb: Breadcrumb) -> PageMenu:
        return PageMenu(
            dropdowns=[
                PageMenuDropdown(
                    name="messages",
                    title=_("Messages"),
                    topics=[
                        PageMenuTopic(
                            title=_("Received messages"),
                            entries=list(_page_menu_entries_ack_all_messages()),
                        ),
                    ],
                ),
                PageMenuDropdown(
                    name="related",
                    title=_("Related"),
                    topics=[
                        PageMenuTopic(
                            title=_("User"),
                            entries=list(_page_menu_entries_related()),
                        ),
                    ],
                ),
            ],
            breadcrumb=breadcrumb,
        )

    def page(self) -> None:
        breadcrumb = make_simple_page_breadcrumb(mega_menu_registry.menu_user(), _("Messages"))
        make_header(html, self.title(), breadcrumb, self.page_menu(breadcrumb))

        for flashed_msg in get_flashed_messages():
            html.show_message(flashed_msg.msg)

        _handle_ack_all()

        html.open_div(class_="wato")
        render_user_message_table("gui_hint")
        html.close_div()

        html.footer()


def _handle_ack_all() -> None:
    if not transactions.check_transaction():
        return

    if request.var("_ack_all"):
        num = len([msg for msg in message.get_gui_messages() if not msg.get("acknowledged")])
        message.acknowledge_all_messages()
        flash(
            _("%d %s.")
            % (
                num,
                ungettext(
                    "received message has been acknowledged",
                    "received messages have been acknowledged",
                    num,
                ),
            )
        )
        html.reload_whole_page()


def _page_menu_entries_ack_all_messages() -> Iterator[PageMenuEntry]:
    yield PageMenuEntry(
        title=_("Acknowledge all"),
        icon_name="werk_ack",
        is_shortcut=True,
        is_suggested=True,
        item=make_simple_link(
            make_confirm_delete_link(
                url=makeactionuri(request, transactions, [("_ack_all", "1")]),
                title=_("Acknowledge all received messages"),
                confirm_button=_("Acknowledge all"),
            )
        ),
        is_enabled=bool([msg for msg in message.get_gui_messages() if not msg.get("acknowledged")]),
    )


def _page_menu_entries_related() -> Iterator[PageMenuEntry]:
    yield PageMenuEntry(
        title=_("Change password"),
        icon_name="topic_change_password",
        item=make_simple_link("user_change_pw.py"),
    )

    yield PageMenuEntry(
        title=_("Edit profile"),
        icon_name="topic_profile",
        item=make_simple_link("user_profile.py"),
    )

    if user.may("general.edit_notifications"):
        yield PageMenuEntry(
            title=_("Notification rules"),
            icon_name="topic_events",
            item=make_simple_link("wato.py?mode=user_notifications_p"),
        )


def render_user_message_table(what: str) -> None:
    html.open_div()
    with table_element(
        "user_messages",
        sortable=False,
        searchable=False,
        empty_text=_("Currently you have no recieved messages"),
    ) as table:
        for entry in sorted(message.get_gui_messages(), key=lambda e: e["time"], reverse=True):
            if what not in entry["methods"]:
                continue

            table.row()

            msg_id = entry["id"]
            datetime = (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["time"]))
                if "time" in entry
                else "-"
            )
            expiretime = (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["valid_till"]))
                if "valid_till" in entry
                else "-"
            )
            msg = entry["text"].replace("\n", " ")

            table.cell(_("Actions"), css=["buttons"], sortable=False)
            if entry.get("acknowledged"):
                html.icon("checkmark", _("Acknowledged"))
            else:
                html.icon_button(
                    "",
                    _("Acknowledge message"),
                    "werk_ack",
                    onclick="cmk.utils.acknowledge_user_message('%s');cmk.utils.reload_whole_page();"
                    % msg_id,
                )

            if entry.get("security"):
                html.icon(
                    "delete", _("Cannot be deleted manually, must expire"), cssclass="colorless"
                )
            else:
                onclick = (
                    "cmk.utils.delete_user_message('%s', this);cmk.utils.reload_whole_page();"
                    % msg_id
                    if what == "gui_hint"
                    else "cmk.utils.delete_user_message('%s', this);" % msg_id
                )
                html.icon_button(
                    "",
                    _("Delete"),
                    "delete",
                    onclick=onclick,
                )

            table.cell(_("Message"), msg)
            table.cell(_("Date sent"), datetime)
            table.cell(_("Expires on"), expiretime)

    html.close_div()


def ajax_delete_user_message() -> None:
    check_csrf_token()
    msg_id = request.get_str_input_mandatory("id")
    message.delete_gui_message(msg_id)


def ajax_acknowledge_user_message() -> None:
    check_csrf_token()
    msg_id = request.get_str_input_mandatory("id")
    message.acknowledge_gui_message(msg_id)
