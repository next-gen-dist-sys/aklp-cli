"""Data models for AKLP CLI Agent."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


# ============== Agent Models ==============


class AgentRequest(BaseModel):
    """Request model for Agent service."""

    session_id: UUID | None = Field(default=None, description="Session ID (optional)")
    raw_command: str = Field(..., description="User's natural language command")


class AgentResponse(BaseModel):
    """Response model from Agent service."""

    session_id: UUID | None = Field(default=None, description="Session ID")
    success: bool = Field(..., description="Whether command generation succeeded")
    command: str | None = Field(default=None, description="Generated kubectl command")
    reason: str | None = Field(default=None, description="Reason for the command")
    title: str | None = Field(default=None, description="Brief summary/title")
    error_message: str | None = Field(default=None, description="Error message if failed")


# ============== Legacy Analysis Models (for backward compatibility) ==============


class AnalysisRequest(BaseModel):
    """Request model for LLM analysis (legacy)."""

    prompt: str = Field(..., description="User's natural language request")


class AnalysisResult(BaseModel):
    """Response model from LLM service analysis (legacy)."""

    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed description in markdown")
    filename: str = Field(..., description="Name of file to create")
    file_content: str = Field(..., description="Content of file to create")
    shell_command: str = Field(..., description="Shell command to execute")


# ============== Note Models ==============


class NoteCreate(BaseModel):
    """Request model for creating a note."""

    title: str = Field(..., min_length=1, max_length=255, description="Title of the note")
    content: str = Field(..., min_length=1, description="Content of the note")
    session_id: UUID | None = Field(default=None, description="Optional session ID")


class NoteUpdate(BaseModel):
    """Request model for updating a note."""

    title: str | None = Field(default=None, min_length=1, max_length=255, description="Updated title")
    content: str | None = Field(default=None, min_length=1, description="Updated content")


class NoteResponse(BaseModel):
    """Response model from Note service."""

    id: UUID
    session_id: UUID | None
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """Paginated note list response."""

    items: list[NoteResponse]
    total: int = Field(description="Total number of notes")
    page: int = Field(ge=1, description="Current page number")
    limit: int = Field(ge=1, description="Number of items per page")

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.limit - 1) // self.limit if self.total > 0 else 1

    @computed_field
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @computed_field
    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


# ============== Task Models ==============


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskCreate(BaseModel):
    """Request model for creating a task."""

    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: str | None = Field(default=None, max_length=1000, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    priority: TaskPriority | None = Field(default=None, description="Task priority")
    due_date: datetime | None = Field(default=None, description="Task due date")
    session_id: UUID | None = Field(default=None, description="AI session ID")


class TaskUpdate(BaseModel):
    """Request model for updating a task."""

    title: str | None = Field(default=None, min_length=1, max_length=255, description="Task title")
    description: str | None = Field(default=None, max_length=1000, description="Task description")
    status: TaskStatus | None = Field(default=None, description="Task status")
    priority: TaskPriority | None = Field(default=None, description="Task priority")
    due_date: datetime | None = Field(default=None, description="Task due date")


class TaskResponse(BaseModel):
    """Response model from Task service."""

    id: UUID
    session_id: UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority | None
    due_date: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Paginated task list response."""

    items: list[TaskResponse]
    total: int = Field(description="Total number of tasks")
    page: int = Field(ge=1, description="Current page number")
    limit: int = Field(ge=1, description="Number of items per page")

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.limit - 1) // self.limit if self.total > 0 else 1

    @computed_field
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @computed_field
    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


# ============== Legacy Models (for backward compatibility) ==============


class LegacyNoteRequest(BaseModel):
    """Legacy request model for Note service (for old CLI workflow)."""

    filename: str = Field(..., description="Name of file to create")
    content: str = Field(..., description="Content of the file")


class LegacyTaskRequest(BaseModel):
    """Legacy request model for Task service (for old CLI workflow)."""

    command: str = Field(..., description="Shell command to execute")


class LegacyTaskResponse(BaseModel):
    """Legacy response model from Task service (for old CLI workflow)."""

    success: bool = Field(..., description="Whether command execution succeeded")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    exit_code: int = Field(..., description="Command exit code")


class ConversationTurn(BaseModel):
    """Single conversation turn in REPL session."""

    timestamp: datetime = Field(default_factory=datetime.now, description="When this turn occurred")
    user_prompt: str = Field(..., description="User's input prompt")
    analysis: AnalysisResult | None = Field(None, description="LLM analysis result")
    executed: bool = Field(False, description="Whether user confirmed and executed")
    note_response: NoteResponse | None = Field(None, description="Note service response")
    task_response: TaskResponse | None = Field(None, description="Task service response")
    error: str | None = Field(None, description="Error message if any")


class SessionHistory(BaseModel):
    """Complete session history for REPL mode."""

    session_id: str = Field(..., description="Unique session identifier")
    started_at: datetime = Field(default_factory=datetime.now, description="Session start time")
    turns: list[ConversationTurn] = Field(default_factory=list, description="List of conversation turns")
