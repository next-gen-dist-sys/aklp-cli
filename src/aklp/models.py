"""Data models for AKLP CLI Agent."""

from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request model for LLM analysis."""

    prompt: str = Field(..., description="User's natural language request")


class AnalysisResult(BaseModel):
    """Response model from LLM service analysis."""

    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed description in markdown")
    filename: str = Field(..., description="Name of file to create")
    file_content: str = Field(..., description="Content of file to create")
    shell_command: str = Field(..., description="Shell command to execute")


class NoteRequest(BaseModel):
    """Request model for Note service."""

    filename: str = Field(..., description="Name of file to create")
    content: str = Field(..., description="Content of the file")


class NoteResponse(BaseModel):
    """Response model from Note service."""

    success: bool = Field(..., description="Whether file creation succeeded")
    message: str = Field(..., description="Success or error message")
    filepath: str | None = Field(None, description="Path to created file")


class TaskRequest(BaseModel):
    """Request model for Task service."""

    command: str = Field(..., description="Shell command to execute")


class TaskResponse(BaseModel):
    """Response model from Task service."""

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
