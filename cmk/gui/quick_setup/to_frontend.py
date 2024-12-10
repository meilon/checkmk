#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
import os
import traceback
import uuid
from collections.abc import Iterable, Mapping, MutableMapping, MutableSequence, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel

from cmk.ccc import store
from cmk.ccc.exceptions import MKGeneralException
from cmk.ccc.i18n import _

from cmk.utils.encoding import json_encode

from cmk.gui.background_job import (
    BackgroundJob,
    BackgroundJobDefines,
    BackgroundProcessInterface,
    InitialStatusArgs,
)
from cmk.gui.exceptions import MKUserError
from cmk.gui.form_specs.vue.form_spec_visitor import (
    parse_value_from_frontend,
    serialize_data_for_frontend,
    validate_value_from_frontend,
)
from cmk.gui.form_specs.vue.visitors import DEFAULT_VALUE
from cmk.gui.form_specs.vue.visitors._type_defs import DataOrigin
from cmk.gui.logged_in import user
from cmk.gui.quick_setup.config_setups import register as register_config_setups
from cmk.gui.quick_setup.private.widgets import ConditionalNotificationStageWidget
from cmk.gui.quick_setup.v0_unstable._registry import quick_setup_registry
from cmk.gui.quick_setup.v0_unstable.definitions import QuickSetupSaveRedirect
from cmk.gui.quick_setup.v0_unstable.predefined import (
    build_quick_setup_formspec_map,
    stage_components,
)
from cmk.gui.quick_setup.v0_unstable.setups import (
    CallableValidator,
    FormspecMap,
    QuickSetup,
    QuickSetupAction,
    QuickSetupActionMode,
    QuickSetupStage,
    QuickSetupStageAction,
)
from cmk.gui.quick_setup.v0_unstable.type_defs import (
    ActionId,
    GeneralStageErrors,
    ParsedFormData,
    QuickSetupId,
    RawFormData,
    StageIndex,
)
from cmk.gui.quick_setup.v0_unstable.widgets import (
    Collapsible,
    FormSpecId,
    FormSpecWrapper,
    ListOfWidgets,
    Widget,
)

from cmk.rulesets.v1.form_specs import FormSpec

GUIDED_MODE_STRING = _("Guided mode")
OVERVIEW_MODE_STRING = _("Overview mode")
LOAD_WAIT_LABEL = _("Please wait...")
PREV_BUTTON_LABEL = _("Back")
PREV_BUTTON_ARIA_LABEL = _("Go to the previous stage")
NEXT_BUTTON_LABEL = _("Next")
NEXT_BUTTON_ARIA_LABEL = _("Go to the next stage")
COMPLETE_BUTTON_ARIA_LABEL = _("Save")


class InvalidStageException(MKGeneralException):
    pass


# TODO: This dataclass is already defined in
# cmk.gui.form_specs.vue.autogen_type_defs.vue_formspec_components
# but can't be imported here. Once we move this module, we can remove this
# and use the one from the other module.
@dataclass
class QuickSetupValidationError:
    message: str
    invalid_value: Any
    location: Sequence[str] = field(default_factory=list)


ValidationErrorMap = MutableMapping[FormSpecId, MutableSequence[QuickSetupValidationError]]


@dataclass
class Button:
    label: str
    aria_label: str


@dataclass
class Action:
    id: ActionId
    button: Button
    load_wait_label: str = field(default=LOAD_WAIT_LABEL)


@dataclass
class StageOverview:
    title: str
    sub_title: str | None


@dataclass
class Errors:
    """Data class representing errors that occurred during the validation process

    Attributes:
        stage_index:
            The index of the stage where the error occurred. If None, the error is stage independent
            (for example a Quick setup (not stage) custom validation failed when attempting to
            perform the complete action)
        formspec_errors:
            A mapping of form spec ids to a list of validation errors that occurred for the
            respective form spec. These are usually stage specific
        stage_errors:
            A list of general stage errors that occurred during the validation process (besides the
            formspecs)
    """

    stage_index: StageIndex | None
    formspec_errors: ValidationErrorMap = field(default_factory=dict)
    stage_errors: GeneralStageErrors = field(default_factory=list)

    def exist(self) -> bool:
        return bool(self.formspec_errors or self.stage_errors)


@dataclass
class NextStageStructure:
    components: Sequence[dict]
    actions: Sequence[Action]
    prev_button: Button | None = None


@dataclass
class Stage:
    next_stage_structure: NextStageStructure | None = None
    errors: Errors | None = None
    stage_recap: Sequence[Widget] = field(default_factory=list)


@dataclass
class AllStageErrors:
    all_stage_errors: Sequence[Errors]


@dataclass
class QuickSetupOverview:
    quick_setup_id: QuickSetupId
    overviews: list[StageOverview]
    stage: Stage
    actions: list[Action]
    prev_button: Button
    mode: str = field(default="guided")
    guided_mode_string: str = field(default=GUIDED_MODE_STRING)
    overview_mode_string: str = field(default=OVERVIEW_MODE_STRING)


@dataclass
class CompleteStage:
    title: str
    sub_title: str | None
    components: Sequence[dict]
    actions: Sequence[Action]
    prev_button: Button


@dataclass
class QuickSetupAllStages:
    quick_setup_id: QuickSetupId
    stages: list[CompleteStage]
    actions: list[Action]
    mode: str = field(default="overview")
    guided_mode_string: str = field(default=GUIDED_MODE_STRING)
    overview_mode_string: str = field(default=OVERVIEW_MODE_STRING)


def _get_stage_components_from_widget(widget: Widget, prefill_data: ParsedFormData | None) -> dict:
    if isinstance(widget, (ListOfWidgets, Collapsible, ConditionalNotificationStageWidget)):
        widget_as_dict = asdict(widget)
        widget_as_dict["items"] = [
            _get_stage_components_from_widget(item, prefill_data) for item in widget.items
        ]
        return widget_as_dict

    if isinstance(widget, FormSpecWrapper):
        form_spec = cast(FormSpec, widget.form_spec)
        return {
            "widget_type": widget.widget_type,
            "form_spec": asdict(
                serialize_data_for_frontend(
                    form_spec=form_spec,
                    field_id=str(widget.id),
                    origin=DataOrigin.DISK,
                    value=prefill_data.get(widget.id) if prefill_data else DEFAULT_VALUE,
                    do_validate=False,
                )
            ),
        }

    return asdict(widget)


def _stage_validate_all_form_spec_keys_existing(
    current_stage_form_data: RawFormData,
    expected_formspecs_map: Mapping[FormSpecId, FormSpec],
) -> GeneralStageErrors:
    return [
        f"Formspec id '{form_spec_id}' not found"
        for form_spec_id in current_stage_form_data.keys()
        if form_spec_id not in expected_formspecs_map
    ]


def _form_spec_validate(
    current_stage_form_data: RawFormData,
    expected_formspecs_map: Mapping[FormSpecId, FormSpec],
) -> ValidationErrorMap:
    return {
        form_spec_id: [QuickSetupValidationError(**asdict(error)) for error in errors]
        for form_spec_id, form_data in current_stage_form_data.items()
        if (errors := validate_value_from_frontend(expected_formspecs_map[form_spec_id], form_data))
    }


def _form_spec_parse(
    all_stages_form_data: Sequence[RawFormData],
    expected_formspecs_map: Mapping[FormSpecId, FormSpec],
) -> ParsedFormData:
    return {
        form_spec_id: parse_value_from_frontend(expected_formspecs_map[form_spec_id], form_data)
        for current_stage_form_data in all_stages_form_data
        for form_spec_id, form_data in current_stage_form_data.items()
    }


def quick_setup_guided_mode(
    quick_setup: QuickSetup, prefill_data: ParsedFormData | None
) -> QuickSetupOverview:
    stages = [stage() for stage in quick_setup.stages]
    return QuickSetupOverview(
        quick_setup_id=quick_setup.id,
        overviews=[
            StageOverview(
                title=stage.title,
                sub_title=stage.sub_title,
            )
            for stage in stages
        ],
        stage=Stage(
            next_stage_structure=NextStageStructure(
                components=[
                    _get_stage_components_from_widget(widget, prefill_data)
                    for widget in stage_components(stages[0])
                ],
                actions=[
                    Action(
                        id=action.id,
                        button=Button(
                            label=action.next_button_label or NEXT_BUTTON_LABEL,
                            aria_label=NEXT_BUTTON_ARIA_LABEL,
                        ),
                        load_wait_label=action.load_wait_label or LOAD_WAIT_LABEL,
                    )
                    for action in stages[0].actions
                ],
            ),
        ),
        actions=[
            Action(
                id=action.id,
                button=Button(label=action.label, aria_label=COMPLETE_BUTTON_ARIA_LABEL),
                load_wait_label=LOAD_WAIT_LABEL,
            )
            for action in quick_setup.actions
        ],
        prev_button=Button(
            label=PREV_BUTTON_LABEL,
            aria_label=PREV_BUTTON_ARIA_LABEL,
        ),
    )


def get_stages_and_formspec_map(
    quick_setup: QuickSetup,
    stage_index: StageIndex,
) -> tuple[Sequence[QuickSetupStage], FormspecMap]:
    stages = [stage() for stage in quick_setup.stages[: stage_index + 1]]
    quick_setup_formspec_map = build_quick_setup_formspec_map(stages)
    return stages, quick_setup_formspec_map


def matching_stage_action(
    stage: QuickSetupStage, stage_action_id: ActionId
) -> QuickSetupStageAction:
    for action in stage.actions:
        if action.id == stage_action_id:
            return action
    raise InvalidStageException(f"Stage action '{stage_action_id}' not found")


def validate_stage(
    quick_setup: QuickSetup,
    stages_raw_formspecs: Sequence[RawFormData],
    stage_index: StageIndex,
    stage_action_id: ActionId,
    stages: Sequence[QuickSetupStage],
    quick_setup_formspec_map: FormspecMap,
) -> Errors | None:
    """Validate the form data of a Quick setup stage.

    Notes:
        * The validation process consists of three steps:
            1. (Quick setup specific) Validate that all form spec keys are existing.
            2. (Form spec specific) Validate the form data against the respective form spec.
            3. (Quick setup specific) Validate against custom validators that are defined in the stage action.

    Args:
        quick_setup:
            The quick setup object.

        stages_raw_formspecs:
            The form data of all stages (the user input)

        stage_index:
            The index of the stage to validate.

        stage_action_id:
            The id of the stage action to validate against

        stages:
            The stages of the quick setup.

        quick_setup_formspec_map:
            The form spec map of the quick setup across all stages. This map is based on the stages
            definition
    """
    errors = validate_stage_formspecs(stage_index, stages_raw_formspecs, quick_setup_formspec_map)
    if errors.exist():
        return errors

    custom_validators = matching_stage_action(
        stages[stage_index], stage_action_id
    ).custom_validators
    errors.stage_errors.extend(
        validate_custom_validators(
            quick_setup.id, custom_validators, stages_raw_formspecs, quick_setup_formspec_map
        ).stage_errors
    )
    return errors if errors.exist() else None


def validate_stage_formspecs(
    stage_index: StageIndex,
    stages_raw_formspecs: Sequence[RawFormData],
    quick_setup_formspec_map: FormspecMap,
) -> Errors:
    errors = Errors(stage_index=stage_index)
    errors.stage_errors.extend(
        _stage_validate_all_form_spec_keys_existing(
            stages_raw_formspecs[stage_index], quick_setup_formspec_map
        )
    )
    if errors.exist():
        return errors

    errors.formspec_errors = _form_spec_validate(
        stages_raw_formspecs[stage_index],
        quick_setup_formspec_map,
    )
    return errors


def validate_custom_validators(
    quick_setup_id: QuickSetupId,
    custom_validators: Iterable[CallableValidator],
    stages_raw_formspecs: Sequence[RawFormData],
    quick_setup_formspec_map: FormspecMap,
) -> Errors:
    errors = Errors(stage_index=None)
    for custom_validator in custom_validators:
        errors.stage_errors.extend(
            custom_validator(
                quick_setup_id,
                _form_spec_parse(stages_raw_formspecs, quick_setup_formspec_map),
            )
        )
    return errors


def validate_stages_formspecs(
    stages_raw_formspecs: Sequence[RawFormData],
    quick_setup_formspec_map: FormspecMap,
) -> Sequence[Errors] | None:
    stages_errors = []
    for stage_index in range(len(stages_raw_formspecs)):
        errors = validate_stage_formspecs(
            stage_index=StageIndex(stage_index),
            stages_raw_formspecs=stages_raw_formspecs[: stage_index + 1],
            quick_setup_formspec_map=quick_setup_formspec_map,
        )
        if errors.exist():
            stages_errors.append(errors)
    return stages_errors or None


def recap_stage(
    quick_setup_id: QuickSetupId,
    stage_index: StageIndex,
    stages: Sequence[QuickSetupStage],
    stage_action_id: ActionId,
    stages_raw_formspecs: Sequence[RawFormData],
    quick_setup_formspec_map: FormspecMap,
) -> Sequence[Widget]:
    parsed_formspec = _form_spec_parse(stages_raw_formspecs, quick_setup_formspec_map)
    recap_widgets: list[Widget] = []
    for recap_callable in matching_stage_action(stages[stage_index], stage_action_id).recap:
        recap_widgets.extend(
            recap_callable(
                quick_setup_id,
                stage_index,
                parsed_formspec,
            )
        )
    return recap_widgets


def get_stage_structure(
    stage: QuickSetupStage,
    prefill_data: ParsedFormData | None = None,
) -> NextStageStructure:
    return NextStageStructure(
        components=[
            _get_stage_components_from_widget(widget, prefill_data)
            for widget in stage_components(stage)
        ],
        prev_button=Button(label=stage.prev_button_label, aria_label=PREV_BUTTON_ARIA_LABEL)
        if stage.prev_button_label
        else None,
        actions=[
            Action(
                id=action.id,
                load_wait_label=action.load_wait_label or LOAD_WAIT_LABEL,
                button=Button(
                    label=action.next_button_label or NEXT_BUTTON_LABEL,
                    aria_label=NEXT_BUTTON_ARIA_LABEL,
                ),
            )
            for action in stage.actions
        ],
    )


@dataclass()
class ValidationAndNextStage:
    next_stage_structure: NextStageStructure | None = None
    errors: Errors | None = None
    stage_recap: Sequence[Widget] = field(default_factory=list)


def validate_stage_and_retrieve_next_stage_structure(
    quick_setup: QuickSetup,
    stage_index: StageIndex,
    stage_action_id: ActionId,
    input_stages: Sequence[dict],
    object_id: str | None,
) -> ValidationAndNextStage:
    stages, form_spec_map = get_stages_and_formspec_map(
        quick_setup=quick_setup,
        stage_index=stage_index,
    )

    response = ValidationAndNextStage()
    if (
        errors := validate_stage(
            quick_setup=quick_setup,
            stages_raw_formspecs=[RawFormData(stage["form_data"]) for stage in input_stages],
            stage_index=stage_index,
            stage_action_id=stage_action_id,
            stages=stages,
            quick_setup_formspec_map=form_spec_map,
        )
    ) is not None:
        response.errors = errors
        return response

    prefill_data: ParsedFormData | None = None
    if object_id := object_id:
        prefill_data = quick_setup.load_data(object_id)
        if not prefill_data:
            raise MKGeneralException(f"Object with id '{object_id}' does not exist.")

    response.stage_recap = recap_stage(
        quick_setup_id=quick_setup.id,
        stage_index=stage_index,
        stages=stages,
        stage_action_id=stage_action_id,
        stages_raw_formspecs=[RawFormData(stage["form_data"]) for stage in input_stages],
        quick_setup_formspec_map=form_spec_map,
    )
    if stage_index == StageIndex(len(quick_setup.stages) - 1):
        return response

    response.next_stage_structure = get_stage_structure(
        stage=quick_setup.stages[stage_index + 1](),
        prefill_data=prefill_data,
    )
    return response


def complete_quick_setup(
    action: QuickSetupAction,
    mode: QuickSetupActionMode,
    stages_raw_formspecs: Sequence[RawFormData],
    quick_setup_formspec_map: FormspecMap,
    object_id: str | None = None,
) -> QuickSetupSaveRedirect:
    return QuickSetupSaveRedirect(
        redirect_url=action.action(
            _form_spec_parse(stages_raw_formspecs, quick_setup_formspec_map),
            mode,
            object_id,
        )
    )


def quick_setup_overview_mode(
    quick_setup: QuickSetup,
    prefill_data: ParsedFormData | None,
) -> QuickSetupAllStages:
    stages = [stage() for stage in quick_setup.stages]
    return QuickSetupAllStages(
        quick_setup_id=quick_setup.id,
        stages=[
            CompleteStage(
                title=stage.title,
                sub_title=stage.sub_title,
                components=[
                    _get_stage_components_from_widget(widget, prefill_data)
                    for widget in stage_components(stage)
                ],
                # TODO: the actions as well the prev_button should be removed from the overview mode
                #  as they are not rendered. The removal must be performed alongside adjustment
                #  of the frontend code.
                actions=[
                    Action(
                        id=action.id,
                        button=Button(
                            label=action.next_button_label or NEXT_BUTTON_LABEL,
                            aria_label=NEXT_BUTTON_ARIA_LABEL,
                        ),
                        load_wait_label=action.load_wait_label or LOAD_WAIT_LABEL,
                    )
                    for action in stage.actions
                ],
                prev_button=Button(
                    label=stage.prev_button_label or PREV_BUTTON_LABEL,
                    aria_label=PREV_BUTTON_ARIA_LABEL,
                ),
            )
            for stage in stages
        ],
        actions=[
            Action(
                id=action.id,
                button=Button(
                    label=action.label,
                    aria_label=COMPLETE_BUTTON_ARIA_LABEL,
                ),
                load_wait_label=LOAD_WAIT_LABEL,
            )
            for action in quick_setup.actions
        ],
    )


class StageActionResult(BaseModel):
    next_stage_structure: NextStageStructure | None = None
    errors: Errors | None = None
    stage_recap: Sequence[Widget] = field(default_factory=list)
    background_job_exception: str | None = None

    @classmethod
    def load_from_job_result(cls, job_id: str) -> "StageActionResult":
        work_dir = str(Path(BackgroundJobDefines.base_dir) / job_id)
        result = store.load_text_from_file(cls._file_path(work_dir))
        return cls.model_validate_json(result)

    def save_to_file(self, work_dir: str) -> None:
        store.save_text_to_file(self._file_path(work_dir), self.model_dump_json())

    @staticmethod
    def _file_path(work_dir: str) -> str:
        return os.path.join(
            work_dir,
            "validation_and_next_structure_result.json",
        )


class QuickSetupStageActionBackgroundJob(BackgroundJob):
    housekeeping_max_age_sec = 1800
    housekeeping_max_count = 10

    job_prefix = "quick_setup_stage_action"

    @classmethod
    def gui_title(cls) -> str:
        return _("Run Quick Setup Stage Action")

    @classmethod
    def create_job_id(
        cls,
        quick_setup_id: str,
        stage_index: int,
        job_uuid: str,
    ) -> str:
        return f"{cls.job_prefix}-{quick_setup_id.replace(":", "_")}-stage_{stage_index}-{job_uuid}"

    def __init__(
        self,
        job_uuid: str,
        quick_setup_id: QuickSetupId,
        action_id: ActionId,
        stage_index: StageIndex,
        user_input_stages: Sequence[dict],
        object_id: str | None,
    ) -> None:
        self._quick_setup_id = quick_setup_id
        self._action_id = action_id
        self._stage_index = stage_index
        self._user_input_stages = user_input_stages
        self._object_id = object_id
        super().__init__(job_id=self.create_job_id(quick_setup_id, stage_index, job_uuid))

    def run_quick_setup_stage_action(self, job_interface: BackgroundProcessInterface) -> None:
        job_interface.get_logger().debug("Running Quick setup stage action finally")
        with job_interface.gui_context():
            try:
                self._run_quick_setup_stage_action(job_interface)
            except Exception as e:
                job_interface.get_logger().debug(
                    "Exception raised while the Quick setup stage action: %s", e
                )
                job_interface.send_exception(str(e))
                StageActionResult(background_job_exception=traceback.format_exc()).save_to_file(
                    job_interface.get_work_dir()
                )

    def _run_quick_setup_stage_action(self, job_interface: BackgroundProcessInterface) -> None:
        job_interface.send_progress_update(_("Starting Quick stage action..."))

        register_config_setups(quick_setup_registry)
        quick_setup = quick_setup_registry[self._quick_setup_id]
        action_result = validate_stage_and_retrieve_next_stage_structure(
            quick_setup=quick_setup,
            stage_index=self._stage_index,
            stage_action_id=self._action_id,
            input_stages=self._user_input_stages,
            object_id=self._object_id,
        )

        job_interface.send_progress_update(_("Saving the result..."))
        StageActionResult(
            next_stage_structure=action_result.next_stage_structure,
            errors=action_result.errors,
            stage_recap=action_result.stage_recap,
        ).save_to_file(job_interface.get_work_dir())
        job_interface.send_result_message("Job finished.")


def start_quick_setup_stage_job(
    quick_setup: QuickSetup,
    action_id: ActionId,
    stage_index: StageIndex,
    user_input_stages: Sequence[dict],
    object_id: str | None,
) -> str:
    job_uuid = str(uuid.uuid4())
    job = QuickSetupStageActionBackgroundJob(
        job_uuid=job_uuid,
        quick_setup_id=quick_setup.id,
        action_id=action_id,
        stage_index=stage_index,
        user_input_stages=user_input_stages,
        object_id=object_id,
    )

    job_start = job.start(
        job.run_quick_setup_stage_action,
        InitialStatusArgs(
            title=_("Running Quick setup %s stage %s action %s")
            % (quick_setup.id, stage_index, action_id),
            user=str(user.id) if user.id else None,
        ),
    )
    if job_start.is_error():
        raise MKUserError(None, str(job_start.error))

    return job.get_job_id()
