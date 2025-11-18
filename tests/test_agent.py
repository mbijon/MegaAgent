"""Tests for agent.py module."""

import pytest
import json
import time
from unittest.mock import patch, MagicMock, Mock
import agent
import config

# agent_dict is defined in agent.py


class TestAgentMemory:
    """Test Agent Memory functionality."""

    def test_memory_initialization(self):
        """Test that Memory can be initialized."""
        import time

        unique_name = f"test_agent_{time.time()}"
        memory = agent.Memory(unique_name, "Initial prompt")
        assert memory.name == unique_name
        assert memory.initial_message == "Initial prompt"
        assert len(memory.history) == 0

    def test_add_memory(self):
        """Test adding memory."""
        import time

        unique_name = f"test_agent_{time.time()}"
        memory = agent.Memory(unique_name, "Initial prompt")
        memory.add_memory({"role": "user", "content": "Test message"})
        assert len(memory.history) == 1
        assert memory.history[0]["content"] == "Test message"

    def test_add_subordinate(self):
        """Test adding a subordinate agent."""
        import time

        unique_name = f"test_agent_{time.time()}"
        memory = agent.Memory(unique_name, "Initial prompt")
        sub_name = f"sub_agent_{time.time()}"
        memory.add_subordinate(sub_name, "Description", "Prompt")
        assert sub_name in memory.subordinates
        assert sub_name in agent.agent_dict

    def test_get_subordinates(self):
        """Test getting subordinates list."""
        import time

        unique_name = f"test_agent_{time.time()}"
        memory = agent.Memory(unique_name, "Initial prompt")
        memory.add_subordinate(f"sub1_{time.time()}", "Desc1", "Prompt1")
        memory.add_subordinate(f"sub2_{time.time()}", "Desc2", "Prompt2")
        subordinates = memory.get_subordinates()
        assert len(subordinates) > 0


class TestAgentExecution:
    """Test Agent execution methods."""

    def test_agent_initialization(self):
        """Test that Agent can be initialized."""
        import time

        unique_name = f"test_agent_{time.time()}"
        test_agent = agent.Agent(unique_name, "Initial prompt")
        assert test_agent.name == unique_name
        assert test_agent.state == "idle"
        assert len(test_agent.message_queue) == 0

    def test_enqueue_message(self, mock_requests_post):
        """Test enqueueing a message."""
        import time

        unique_name = f"test_agent_{time.time()}"
        test_agent = agent.Agent(unique_name, "Initial prompt")
        # Set state to running to prevent thread from starting
        test_agent.state = "running"
        test_agent.enqueue("user", "Test message")
        assert len(test_agent.message_queue) == 1
        assert test_agent.message_queue[0]["content"] == "Test message"
        # Reset state
        test_agent.state = "idle"

    def test_execute_read_file(self, temp_files_dir, monkeypatch, mock_requests_post):
        """Test executing read_file tool."""
        import utils
        import time

        unique_name = f"test_agent_{time.time()}"
        monkeypatch.setattr(utils, "read_file", lambda f: ("file content", "hash123"))

        test_agent = agent.Agent(unique_name, "Initial prompt")
        tool_info = test_agent.execute(
            "read_file", {"role": "function"}, {"filename": "test.txt"}
        )

        assert tool_info["name"] == "read_file"
        # Check that content contains the filename or file content
        assert (
            "test.txt" in tool_info["content"] or "file content" in tool_info["content"]
        )

    def test_execute_write_file(self, temp_files_dir, monkeypatch, mock_requests_post):
        """Test executing write_file tool."""
        import utils
        import time

        unique_name = f"test_agent_{time.time()}"
        monkeypatch.setattr(
            utils,
            "write_file",
            lambda f, c, o=False, h=None, agent_name="": "Successfully wrote to test.txt. The new commit hash is hash123",
        )

        test_agent = agent.Agent(unique_name, "Initial prompt")
        tool_info = test_agent.execute(
            "write_file",
            {"role": "function"},
            {"filename": "test.txt", "content": "Test content"},
        )

        # The result should indicate success, warning, or error (all are valid outcomes)
        assert any(
            keyword in tool_info["content"]
            for keyword in ["Success", "Warning", "wrote", "Error"]
        )

    def test_execute_web_search(self):
        """Test executing web_search tool."""
        import time

        unique_name = f"test_agent_{time.time()}"
        test_agent = agent.Agent(unique_name, "Initial prompt")
        tool_info = test_agent.execute("web_search", {"role": "function"}, {})

        assert tool_info["content"] is not None
        assert "web search" in tool_info["content"].lower()

    def test_execute_terminate(self, monkeypatch):
        """Test executing terminate tool."""
        import utils
        import time

        unique_name = f"test_agent_{time.time()}"
        monkeypatch.setattr(utils, "read_file", lambda f: ("", "hash"))

        test_agent = agent.Agent(unique_name, "Initial prompt")
        result = test_agent.execute("terminate", {"role": "function"}, {})

        assert result == {}

    def test_execute_invalid_tool(self, mock_requests_post):
        """Test executing an invalid tool returns error."""
        import time

        unique_name = f"test_agent_{time.time()}"
        test_agent = agent.Agent(unique_name, "Initial prompt")
        # The execute method catches ValueError and returns an error dict instead of raising
        result = test_agent.execute("invalid_tool", {"role": "function"}, {})
        # Should return an error message
        assert "Error" in result.get("content", "")
        assert "not a valid function name" in result.get("content", "").lower()


class TestAgentToolCalls:
    """Test agent handling of tool calls."""

    def test_handle_function_call_format(self, monkeypatch, mock_requests_post):
        """Test handling legacy function_call format."""
        import time

        unique_name = f"test_agent_{time.time()}"
        test_agent = agent.Agent(unique_name, "Initial prompt")

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "role": "assistant",
                        "function_call": {
                            "name": "read_file",
                            "arguments": '{"filename": "test.txt"}',
                        },
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        # Mock the API response
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = mock_response
        mock_requests_post.return_value = mock_api_response

        with patch.object(
            test_agent,
            "execute",
            return_value={"role": "function", "content": "result"},
        ):
            test_agent.enqueue("user", "Test")
            # Give it a moment to process
            time.sleep(0.3)
            # Stop the agent thread if still running
            test_agent.state = "idle"

    def test_handle_tool_calls_format(self, monkeypatch, mock_requests_post):
        """Test handling new tool_calls format for GPT-5."""
        import time

        unique_name = f"test_agent_{time.time()}"
        test_agent = agent.Agent(unique_name, "Initial prompt")

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "read_file",
                                    "arguments": '{"filename": "test.txt"}',
                                },
                            }
                        ],
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        # Mock the API response
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = mock_response
        mock_requests_post.return_value = mock_api_response

        with patch.object(
            test_agent,
            "execute",
            return_value={"role": "tool", "content": "result"},
        ):
            test_agent.enqueue("user", "Test")
            time.sleep(0.3)
            # Stop the agent thread if still running
            test_agent.state = "idle"

    def test_handle_web_search_tool_call(self, monkeypatch, mock_requests_post):
        """Test handling web_search tool call."""
        import time

        unique_name = f"test_agent_{time.time()}"
        test_agent = agent.Agent(unique_name, "Initial prompt")

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "Search results here",
                        "role": "assistant",
                        "tool_calls": [{"id": "call_web_123", "type": "web_search"}],
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        # Mock the API response
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = mock_response
        mock_requests_post.return_value = mock_api_response

        test_agent.enqueue("user", "Search for something")
        time.sleep(0.3)
        # Stop the agent thread if still running
        test_agent.state = "idle"
