import pytest
from unittest.mock import patch, MagicMock


class TestAgentManagerImports:
    """Test agent_manager imports"""

    def test_agent_manager_exists(self):
        from agents.langgraph_service.agent_manager import AgentManager
        assert AgentManager is not None

    def test_create_agents_method_exists(self):
        from agents.langgraph_service.agent_manager import AgentManager
        assert hasattr(AgentManager, 'create_agents')

    def test_get_last_active_agent_method_exists(self):
        from agents.langgraph_service.agent_manager import AgentManager
        assert hasattr(AgentManager, 'get_last_active_agent')


class TestCreateAgents:
    """Test AgentManager.create_agents method"""

    @pytest.fixture
    def agent_manager(self):
        from agents.langgraph_service.agent_manager import AgentManager
        return AgentManager

    def test_create_agents_returns_list(self, agent_manager):
        with patch('agents.langgraph_service.agent_manager.PlannerAgentConfig') as mock_planner, \
             patch('agents.langgraph_service.agent_manager.ImageVideoCreatorAgentConfig') as mock_ivc, \
             patch('agents.langgraph_service.agent_manager.create_react_agent') as mock_agent, \
             patch('agents.langgraph_service.agent_manager.tool_service') as mock_tool_svc:
            mock_planner_instance = MagicMock()
            mock_planner_instance.name = 'planner'
            mock_planner_instance.tools = []
            mock_planner_instance.handoffs = []
            mock_planner_instance.system_prompt = ''
            mock_planner.return_value = mock_planner_instance

            mock_ivc_instance = MagicMock()
            mock_ivc_instance.name = 'image_video_creator'
            mock_ivc_instance.tools = []
            mock_ivc_instance.handoffs = []
            mock_ivc_instance.system_prompt = ''
            mock_ivc.return_value = mock_ivc_instance

            mock_agent.return_value = MagicMock()

            result = agent_manager.create_agents(
                model=MagicMock(),
                tool_list=[]
            )

            assert isinstance(result, list)
            assert len(result) == 3  # planner + image_video_creator + pneumat_enhancer

    def test_create_agents_filters_image_tools(self, agent_manager):
        with patch('agents.langgraph_service.agent_manager.PlannerAgentConfig') as mock_planner, \
             patch('agents.langgraph_service.agent_manager.ImageVideoCreatorAgentConfig') as mock_ivc, \
             patch('agents.langgraph_service.agent_manager.create_react_agent') as mock_agent, \
             patch('agents.langgraph_service.agent_manager.tool_service') as mock_tool_svc, \
             patch('agents.langgraph_service.agent_manager.logger') as mock_logger:
            mock_planner_instance = MagicMock()
            mock_planner_instance.name = 'planner'
            mock_planner_instance.tools = []
            mock_planner_instance.handoffs = []
            mock_planner_instance.system_prompt = ''
            mock_planner.return_value = mock_planner_instance

            mock_ivc_instance = MagicMock()
            mock_ivc_instance.name = 'image_video_creator'
            mock_ivc_instance.tools = []
            mock_ivc_instance.handoffs = []
            mock_ivc_instance.system_prompt = ''
            mock_ivc.return_value = mock_ivc_instance

            mock_agent.return_value = MagicMock()

            tool_list = [
                {'id': 'img_gen', 'type': 'image', 'name': 'ImageGen'},
                {'id': 'vid_gen', 'type': 'video', 'name': 'VideoGen'},
            ]

            agent_manager.create_agents(
                model=MagicMock(),
                tool_list=tool_list
            )

            # Verify logger was called with filtered tools
            mock_logger.debug.assert_called()


class TestGetLastActiveAgent:
    """Test AgentManager.get_last_active_agent method"""

    @pytest.fixture
    def agent_manager(self):
        from agents.langgraph_service.agent_manager import AgentManager
        return AgentManager

    def test_returns_none_when_no_messages(self, agent_manager):
        result = agent_manager.get_last_active_agent([], ['planner', 'image_creator'])
        assert result is None

    def test_returns_none_when_no_assistant_message(self, agent_manager):
        messages = [
            {'role': 'user', 'content': 'hello'},
            {'role': 'system', 'content': 'you are helpful'}
        ]
        result = agent_manager.get_last_active_agent(messages, ['planner', 'image_creator'])
        assert result is None

    def test_returns_agent_name_from_assistant_message(self, agent_manager):
        messages = [
            {'role': 'user', 'content': 'hello'},
            {'role': 'assistant', 'name': 'planner', 'content': 'I am the planner'}
        ]
        result = agent_manager.get_last_active_agent(messages, ['planner', 'image_creator'])
        assert result == 'planner'

    def test_returns_last_active_agent(self, agent_manager):
        messages = [
            {'role': 'user', 'content': 'hello'},
            {'role': 'assistant', 'name': 'image_creator', 'content': 'creating image'},
            {'role': 'assistant', 'name': 'planner', 'content': 'planning next step'}
        ]
        result = agent_manager.get_last_active_agent(messages, ['planner', 'image_creator'])
        assert result == 'planner'

    def test_returns_none_when_name_not_in_agent_list(self, agent_manager):
        messages = [
            {'role': 'assistant', 'name': 'unknown_agent', 'content': 'hello'}
        ]
        result = agent_manager.get_last_active_agent(messages, ['planner', 'image_creator'])
        assert result is None

    def test_handles_empty_agent_names_list(self, agent_manager):
        messages = [
            {'role': 'assistant', 'name': 'planner', 'content': 'hello'}
        ]
        result = agent_manager.get_last_active_agent(messages, [])
        assert result is None


class TestCreateLangGraphAgent:
    """Test AgentManager._create_langgraph_agent method"""

    @pytest.fixture
    def agent_manager(self):
        from agents.langgraph_service.agent_manager import AgentManager
        return AgentManager

    def test_creates_agent_with_handoff_tools(self, agent_manager):
        with patch('agents.langgraph_service.agent_manager.create_react_agent') as mock_create_agent, \
             patch('agents.langgraph_service.agent_manager.create_handoff_tool') as mock_handoff, \
             patch('agents.langgraph_service.agent_manager.tool_service') as mock_tool_svc:
            mock_handoff.return_value = MagicMock()
            mock_tool_svc.get_tool.return_value = MagicMock()
            mock_tool_svc.get_all_tools.return_value = {}
            mock_create_agent.return_value = MagicMock()

            mock_config = MagicMock()
            mock_config.name = 'test_agent'
            mock_config.tools = []
            mock_config.handoffs = [{'agent_name': 'other', 'description': 'handoff'}]
            mock_config.system_prompt = ''

            agent_manager._create_langgraph_agent(
                model=MagicMock(),
                config=mock_config
            )

            mock_create_agent.assert_called_once()

    def test_creates_agent_with_business_tools(self, agent_manager):
        with patch('agents.langgraph_service.agent_manager.create_react_agent') as mock_create_agent, \
             patch('agents.langgraph_service.agent_manager.tool_service') as mock_tool_svc:
            mock_tool = MagicMock()
            mock_tool_svc.get_tool.return_value = mock_tool
            mock_tool_svc.get_all_tools.return_value = {'system_tool': {'provider': 'system'}}
            mock_create_agent.return_value = MagicMock()

            mock_config = MagicMock()
            mock_config.name = 'test_agent'
            mock_config.tools = [{'id': 'business_tool'}]
            mock_config.handoffs = []
            mock_config.system_prompt = ''

            agent_manager._create_langgraph_agent(
                model=MagicMock(),
                config=mock_config
            )

            mock_create_agent.assert_called_once()
