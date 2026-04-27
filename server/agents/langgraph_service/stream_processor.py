# type: ignore[import]
import os
import traceback
from typing import Optional, List, Dict, Any, Callable, Awaitable
from langchain_core.messages import AIMessageChunk, ToolCall, convert_to_openai_messages, ToolMessage
from langgraph.graph import StateGraph
import json
from web.services.log_service import agent_logger as logger


def _get_attr_or_dict(obj: Any, key: str) -> Any:
    """Safely get attribute or dict key from an object that may be dict or object."""
    return getattr(obj, key, None) or (obj.get(key) if isinstance(obj, dict) else None)


class StreamProcessor:
    """流式处理器 - 负责处理智能体的流式输出"""

    TOOLS_REQUIRING_CONFIRMATION: set = set(
        os.getenv("TOOLS_REQUIRING_CONFIRMATION", "generate_video_by_veo3_fast_jaaz").split(",")
    )

    def __init__(self, session_id: str, db_service: Any, websocket_service: Callable[[str, Dict[str, Any]], Awaitable[None]]):
        self.session_id = session_id
        self.db_service = db_service
        self.websocket_service = websocket_service
        self.tool_calls: List[ToolCall] = []
        self.last_saved_message_index = 0
        self.last_streaming_tool_call_id: Optional[str] = None

    async def process_stream(self, swarm: StateGraph, messages: List[Dict[str, Any]], context: Dict[str, Any]) -> None:
        """处理整个流式响应

        Args:
            swarm: 智能体群组
            messages: 消息列表
            context: 上下文信息
        """
        self.last_saved_message_index = len(messages) - 1

        compiled_swarm = swarm.compile()

        try:
            async for chunk in compiled_swarm.astream(
                {"messages": messages},
                config=context,
                stream_mode=["messages", "custom", 'values']
            ):
                await self._handle_chunk(chunk)
        except Exception as e:
            logger.error("stream_process_error", error=str(e))
            await self.websocket_service(self.session_id, {
                'type': 'error',
                'error': str(e)
            })
        finally:
            await self.websocket_service(self.session_id, {
                'type': 'done'
            })

    async def _handle_chunk(self, chunk: Any) -> None:
        # print('👇chunk', chunk)
        """处理单个chunk"""
        chunk_type = chunk[0]

        if chunk_type == 'values':
            await self._handle_values_chunk(chunk[1])
        else:
            await self._handle_message_chunk(chunk[1][0])



    async def _handle_values_chunk(self, chunk_data: Dict[str, Any]) -> None:
        """处理 values 类型的 chunk"""
        all_messages = chunk_data.get('messages', [])
        oai_messages = convert_to_openai_messages(all_messages)
        # 确保 oai_messages 是列表类型
        if not isinstance(oai_messages, list):
            oai_messages = [oai_messages] if oai_messages else []

        # 发送所有消息到前端
        await self.websocket_service(self.session_id, {
            'type': 'all_messages',
            'messages': oai_messages
        })

        # 保存新消息到数据库
        for i in range(self.last_saved_message_index + 1, len(oai_messages)):
            new_message = oai_messages[i]
            if len(oai_messages) > 0:  # 确保有消息才保存
                await self.db_service.create_message(
                    self.session_id,
                    new_message.get('role', 'user'),
                    json.dumps(new_message)
                )
            self.last_saved_message_index = i

    async def _handle_message_chunk(self, ai_message_chunk: AIMessageChunk) -> None:
        """处理消息类型的 chunk"""
        # print('👇ai_message_chunk', ai_message_chunk)
        try:
            content = ai_message_chunk.content

            if isinstance(ai_message_chunk, ToolMessage):
                # 工具调用结果之后会在 values 类型中发送到前端，这里会更快出现一些
                oai_message = convert_to_openai_messages([ai_message_chunk])[0]
                logger.debug("toolcall_result", oai_message=oai_message)
                await self.websocket_service(self.session_id, {
                    'type': 'tool_call_result',
                    'id': ai_message_chunk.tool_call_id,
                    'message': oai_message
                })
            elif content:
                # 发送文本内容
                await self.websocket_service(self.session_id, {
                    'type': 'delta',
                    'text': content
                })
            elif hasattr(ai_message_chunk, 'tool_calls') and ai_message_chunk.tool_calls and ai_message_chunk.tool_calls[0].get('name'):
                # 处理工具调用
                await self._handle_tool_calls(ai_message_chunk.tool_calls)

            # 处理工具调用参数流
            if hasattr(ai_message_chunk, 'tool_call_chunks'):
                await self._handle_tool_call_chunks(ai_message_chunk.tool_call_chunks)
        except Exception as e:
            logger.error("stream_chunk_error", error=str(e))

    async def _handle_tool_calls(self, tool_calls: List[ToolCall]) -> None:
        self.tool_calls = [tc for tc in tool_calls if tc.get('name')]
        logger.debug("tool_call_event", tool_calls=tool_calls)

        for tc in self.tool_calls:
            name = _get_attr_or_dict(tc, 'name') or ''
            args = _get_attr_or_dict(tc, 'args') or {}
            if 'generate_image' in name and args.get('prompt'):
                logger.info("english_prompt_generated", tool=name, prompt=args.get('prompt'))

        for tool_call in self.tool_calls:
            tool_name = _get_attr_or_dict(tool_call, 'name')

            if tool_name in self.TOOLS_REQUIRING_CONFIRMATION:
                logger.debug("tool_requires_confirmation", tool=tool_name)
                continue
            else:
                await self.websocket_service(self.session_id, {
                    'type': 'tool_call',
                    'id': _get_attr_or_dict(tool_call, 'id'),
                    'name': tool_name,
                    'arguments': '{}'
                })

    async def _handle_tool_call_chunks(self, tool_call_chunks: List[Any]) -> None:
        for tool_call_chunk in tool_call_chunks:
            chunk_id = _get_attr_or_dict(tool_call_chunk, 'id')
            if chunk_id:
                self.last_streaming_tool_call_id = chunk_id
            elif self.last_streaming_tool_call_id:
                chunk_args = _get_attr_or_dict(tool_call_chunk, 'args')
                await self.websocket_service(self.session_id, {
                    'type': 'tool_call_arguments',
                    'id': self.last_streaming_tool_call_id,
                    'text': chunk_args
                })
            else:
                logger.warning("no_last_streaming_tool_call_id", chunk=str(tool_call_chunk)[:100])
