import tiktoken
from openai import AsyncOpenAI
from app.logger import logger


class ContextManager:

    def __init__(
        self,
        max_total_tokens: int = 8000,
        recent_turns_to_keep: int = 10,
        openai_api_key: str = "",
    ):
        self._max_total_tokens = max_total_tokens
        self._recent_turns = recent_turns_to_keep
        self._encoder = tiktoken.encoding_for_model("gpt-4o")
        self._context_summary: str | None = None
        self._critical_facts: dict[str, str] = {}
        self._all_messages: list[dict] = []
        self._client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None

    def count_tokens(self, text: str) -> int:
        return len(self._encoder.encode(text))

    def add_message(self, role: str, content: str) -> None:
        self._all_messages.append({"role": role, "content": content})

    def set_critical_fact(self, key: str, value: str) -> None:
        if value:
            self._critical_facts[key] = value

    async def maybe_summarize(self) -> None:
        """Check if context exceeds budget and summarize old turns if needed."""
        total = sum(self.count_tokens(m["content"]) for m in self._all_messages)
        if total <= self._max_total_tokens:
            return

        if len(self._all_messages) <= self._recent_turns:
            return

        old_messages = self._all_messages[:-self._recent_turns]
        self._context_summary = await self._summarize_old_messages(old_messages)
        logger.info(f"Context summarized: {len(old_messages)} old messages compressed")

    async def _summarize_old_messages(self, messages: list[dict]) -> str:
        facts_str = ", ".join(f"{k}: {v}" for k, v in self._critical_facts.items())
        transcript = "\n".join(f"{m['role']}: {m['content']}" for m in messages)

        if not self._client:
            # Fallback: simple truncation with critical facts
            return f"Earlier in this conversation: {facts_str}. {transcript[:500]}"

        try:
            response = await self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"Summarize this conversation excerpt in 2-3 sentences. "
                               f"Always include these facts: {facts_str}\n\n{transcript}"
                }],
                max_tokens=200,
                timeout=5.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Context summarization failed: {e}")
            return f"Earlier: {facts_str}. {transcript[:500]}"

    def get_messages_for_llm(self, system_prompt: str, state_context: str = "") -> list[dict]:
        """Build message list for the LLM with context management."""
        messages = [{"role": "system", "content": f"{system_prompt}\n\n{state_context}"}]

        if self._context_summary:
            messages.append({
                "role": "system",
                "content": f"Context from earlier in this conversation: {self._context_summary}"
            })

        # Add recent messages
        recent = self._all_messages[-self._recent_turns:] if len(self._all_messages) > self._recent_turns else self._all_messages
        messages.extend(recent)

        return messages

    def get_full_history(self) -> list[dict]:
        return self._all_messages.copy()
