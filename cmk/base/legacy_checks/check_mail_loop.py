#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import host_name, passwordstore_get_cmdline
from cmk.base.config import active_check_info


def check_mail_loop_arguments(params):  # pylint: disable=too-many-branches
    """
    >>> from cmk.base.api.agent_based.plugin_contexts import current_host
    >>> with current_host("hurz"):
    ...     for a in check_mail_loop_arguments(
    ...         {
    ...             "item": "MailLoop_imap",
    ...             "subject": "Some subject",
    ...             "send_server": "smtp.gmx.de",
    ...             "send_tls": True,
    ...             "send_port": 42,
    ...             "send_auth": ("me@gmx.de", ("password", "p4ssw0rd")),
    ...             "fetch": (
    ...                 "IMAP",
    ...                 {
    ...                     "server": "imap.gmx.de",
    ...                     "auth": ("basic", ("me@gmx.de", ("password", "p4ssw0rd"))),
    ...                     "connection": {"disable_tls": False, "port": 123},
    ...                 },
    ...             ),
    ...             "mail_from": "me_from@gmx.de",
    ...             "mail_to": "me_to@gmx.de",
    ...             "connect_timeout": 23,
    ...             "duration": (93780, 183840),
    ...         }
    ...     ):
    ...         print(a)
    --fetch-protocol=IMAP
    --fetch-server=imap.gmx.de
    --fetch-tls
    --fetch-port=123
    --fetch-username=me@gmx.de
    --fetch-password=p4ssw0rd
    --connect-timeout=23
    --send-server=smtp.gmx.de
    --send-tls
    --send-port=42
    --send-username=me@gmx.de
    --send-password=p4ssw0rd
    --mail-from=me_from@gmx.de
    --mail-to=me_to@gmx.de
    --status-suffix=hurz-MailLoop_imap
    --warning=93780
    --critical=183840
    --subject=Some subject
    """
    try:
        fetch_protocol, fetch_params = params["fetch"]
        connection_params = fetch_params["connection"]
        auth_type, auth_data = fetch_params["auth"]
    except KeyError as exc:
        raise ValueError(
            f"Params for check_mail_loop are faulty (missing {exc}), did you update the config?"
        )

    args: list[str | tuple[str, str, str]] = [
        f"--fetch-protocol={fetch_protocol}",
        f"--fetch-server={fetch_params.get('server', '$HOSTADDRESS$')}",
    ]

    # NOTE: this argument will be turned into `--fetch-disable-tls` when
    # refactoring all mailbox based active checks
    if not connection_params.get("disable_tls"):
        args.append("--fetch-tls")

    if connection_params.get("disable_cert_validation"):
        args.append("--fetch-disable-cert-validation")

    if (fetch_port := connection_params.get("port")) is not None:
        args.append(f"--fetch-port={fetch_port}")

    if auth_type == "basic":
        username, password = auth_data
        args += [
            f"--fetch-username={username}",
            passwordstore_get_cmdline("--fetch-password=%s", password),
        ]
    else:
        raise ValueError(f"{auth_type} authentication not (yet) supported for check_mail_loop")

    if "connect_timeout" in params:
        args.append(f"--connect-timeout={params['connect_timeout']}")

    args.append(f"--send-server={params.get('send_server', '$HOSTADDRESS$')}")

    if "send_tls" in params:
        args.append("--send-tls")

    if "send_port" in params:
        args.append(f"--send-port={params['send_port']}")

    if "send_auth" in params:
        username, password = params["send_auth"]
        args.append(f"--send-username={username}")
        args.append(passwordstore_get_cmdline("--send-password=%s", password))

    args.append(f"--mail-from={params['mail_from']}")
    args.append(f"--mail-to={params['mail_to']}")

    if "delete_messages" in params:
        args.append("--delete-messages")

    args.append(f"--status-suffix={host_name()}-{params['item']}")

    if "duration" in params:
        warning, critical = params["duration"]
        args.append(f"--warning={warning}")
        args.append(f"--critical={critical}")

    if "subject" in params:
        args.append(f"--subject={params['subject']}")

    return args


active_check_info["mail_loop"] = {
    "command_line": "check_mail_loop $ARG1$",
    "argument_function": check_mail_loop_arguments,
    "service_description": lambda params: f"Mail Loop {params['item']}",
}
