import typing
import traceback
import uuid
import random


from free_one_api.entities import request, response

from ...models import adapter
from ...models.adapter import llm
from ...entities import request, response, exceptions
from ...models.channel import evaluation

from claude2_api.client import (
    ClaudeAPIClient,
    SendMessageResponse,
)
from claude2_api.session import SessionData, get_session_data
from claude2_api.errors import ClaudeAPIError, MessageRateLimitError, OverloadError


@adapter.llm_adapter
class ClaudeAdapter(llm.LLMLibAdapter):
    
    @classmethod
    def name(cls) -> str:
        return "KoushikNavuluri/Claude-API"
    
    @classmethod
    def description(self) -> str:
        return "Use KoushikNavuluri/Claude-API to access Claude web edition."

    def supported_models(self) -> list[str]:
        return [
            "gpt-3.5-turbo",
            "gpt-4",
            "claude-3-opus"
        ]

    def function_call_supported(self) -> bool:
        return False

    def stream_mode_supported(self) -> bool:
        return False

    def multi_round_supported(self) -> bool:
        return True
    

    @classmethod
    def config_comment(cls) -> str:
        return """
        To use the unofficial-claude2-api with this adapter, you need to provide 
        configuration details including 'cookie', 'user-agent', and 'org-id'. 
        These values are necessary for establishing a session with the Claude API. 
        Here's an example of the required configuration in JSON format:
        
        {
            "cookie": "Your_Claude_Session_Cookie_Value",
            "user-agent": "Your_Web_Browser_User_Agent",
            "org-id": "Your_Organization_ID"
        }
        
        The 'cookie' should be the entire Cookie header value string when visiting Claude's website.
        The 'user-agent' is required for the session to mimic a real browser session.
        'org-id' can be found in your Claude account details or API settings.

        Please ensure these values are kept secure and are not exposed to unauthorized users.
        """


    @classmethod
    def supported_path(cls) -> str:
        return "/v1/chat/completions"
    
    _chatbot: ClaudeAPIClient = None

    @property
    def chatbot(self) -> ClaudeAPIClient:
        if self._chatbot is None:
            cookie_header_value = self.config["cookie"]
            user_agent = self.config["user-agent"]
            organization_id = self.config.get('org-id', None)
            session = SessionData(cookie_header_value, user_agent, organization_id)
            self._chatbot =  ClaudeAPIClient(session, timeout=240)
        return self._chatbot
    
    def __init__(self, config: dict, eval: evaluation.AbsChannelEvaluation):
        self.config = config
        self.eval = eval
        
    async def test(self) -> (bool, str):
        try:
            chat_id = self.chatbot.create_chat()
            self.chatbot.send_message(chat_id,"Hello, Claude!")
            self.chatbot.delete_chat(chat_id)
            return True, ""
        except Exception as e:
            traceback.print_exc()
            return False, str(e)
        
    async def query(self, req: request.Request) -> typing.AsyncGenerator[response.Response, None]:
        prompt = ""
        
        for msg in req.messages:
            prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += "assistant: "
        
        random_int = random.randint(0, 1000000000)
        
        try:
            # 使用新的方法创建聊天并发送消息
            chat_id = self.chatbot.create_chat()
            res: SendMessageResponse = self.chatbot.send_message(chat_id, prompt)
            resp_text = res.answer if res.answer else "Error in getting response"
            
            # 删除聊天的步骤可能需要根据实际情况调整
            self.chatbot.delete_chat(chat_id)
            
        except ClaudeAPIError as e:
            # 处理可能的错误
            resp_text = f"Error: {str(e)}"
        
        yield response.Response(
            id=random_int,
            finish_reason=response.FinishReason.STOP,
            normal_message=resp_text,
            function_call=None
        )