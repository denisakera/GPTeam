from datetime import datetime
from enum import Enum
from typing import Generic, List, Literal, Optional, TypeVar
from uuid import UUID, uuid4

import pytz
from pydantic import BaseModel, Field, validator
from src.utils.database.base import Tables

from src.utils.database.client import get_database

from ..location.base import Location
from .message import AgentMessage


class PlanStatus(Enum):
    IN_PROGRESS = "in_progress"
    TODO = "todo"
    DONE = "done"
    FAILED = "failed"

class LLMSinglePlan(BaseModel):
    index: int = Field(description="The plan number")
    description: str = Field(description="A confrontational action that forces immediate engagement. No scheduling or follow-ups allowed.")
    location_name: str = Field(
        description="The name of the location where this confrontation happens NOW. Must match the location name exactly."
    )
    max_duration_hrs: float = Field(
        default=0.5,
        description="Maximum time is 30 minutes. Every moment of delay weakens impact."
    )
    stop_condition: str = Field(
        description="The immediate impact that proves you've forced change. Must be observable NOW, not in the future."
    )


class LLMPlanResponse(BaseModel):
    plans: list[LLMSinglePlan] = Field(description="A list of immediate confrontational actions. No scheduling or follow-ups allowed.")


class SinglePlan(BaseModel):
    id: UUID
    description: str
    location: Optional[Location]
    max_duration_hrs: float
    created_at: datetime
    agent_id: UUID
    related_message: Optional[AgentMessage] = None
    stop_condition: str
    status: PlanStatus
    scratchpad: list[dict] = []
    completed_at: Optional[datetime] = None

    def __init__(
        self,
        description: str,
        max_duration_hrs: float,
        stop_condition: str,
        agent_id: UUID,
        status: PlanStatus = PlanStatus.TODO,
        scratchpad: Optional[list[dict]] = None,
        location: Optional[Location] = None,
        created_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        id: Optional[UUID] = None,
        related_message: Optional[AgentMessage] = None,
    ):
        if id is None:
            id = uuid4()

        if created_at is None:
            created_at = datetime.now(tz=pytz.utc)

        if scratchpad is None:
            scratchpad = []

        super().__init__(
            id=id,
            description=description,
            location=location,
            max_duration_hrs=max_duration_hrs,
            created_at=created_at,
            agent_id=agent_id,
            stop_condition=stop_condition,
            completed_at=completed_at,
            status=status,
            scratchpad=scratchpad,
            related_message=related_message,
        )

    def __str__(self):
        return f"[PLAN] - {self.description} at {self.location.name if self.location else 'unknown location'}"

    @classmethod
    async def from_id(cls, id: UUID):
        data = await (await get_database()).get_by_id(Tables.Plan, id)

        if len(data) == 0:
            raise ValueError(f"Plan with id {id} does not exist")

        plan_data = data[0]
        if plan_data["location"] is not None:
            plan_data["location"] = await Location.from_id(plan_data["location_id"])
        else:
            plan_data["location"] = None
        del plan_data["location_id"]

        return cls(**plan_data)

    @classmethod
    async def from_llm_single_plan(cls, agent_id: UUID, llm_plan: LLMSinglePlan):
        try:
            location = await Location.from_name(llm_plan.location_name)
        except Exception as e:
            print(f"Warning: Could not find location {llm_plan.location_name}: {str(e)}")
            location = None

        return cls(
            description=llm_plan.description,
            max_duration_hrs=llm_plan.max_duration_hrs,
            stop_condition=llm_plan.stop_condition,
            agent_id=agent_id,
            location=location
        )

    async def delete(self):
        return await (await get_database()).get_by_id(Tables.Plan, str(self.id))

    def _db_dict(self):
        row = {
            "id": str(self.id),
            "description": self.description,
            "location_id": str(self.location.id) if self.location else None,
            "max_duration_hrs": self.max_duration_hrs,
            "created_at": self.created_at.isoformat(),
            "agent_id": str(self.agent_id),  # Fixed: Use agent_id instead of self.id
            "related_event_id": str(self.related_message.event_id)
            if self.related_message
            else None,
            "stop_condition": self.stop_condition,
            "status": self.status.value,
            "scratchpad": self.scratchpad,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }

        return row

    def make_plan_prompt(self):
        location_name = self.location.name if self.location else "current location"
        return (
            f"\nForce this change NOW: {self.description}\n"
            f"At this location: {location_name}\n"
            f"Success means: {self.stop_condition}\n"
            f"Every second of delay weakens impact. You have {self.max_duration_hrs} hours maximum."
        )
