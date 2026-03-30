from llm_sdk import Small_LLM_Model
import json
from typing import Callable, Dict, List, Tuple, Generator, Any


class Model(Small_LLM_Model):
    """Wrapper around Small_LLM_Model with token-level constrained decoding"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        vocab_path: str = self.get_path_to_vocab_file()
        with open(vocab_path) as f:
            self._vocab: Dict[str, int] = json.load(f)

    def get_masked_logits(
        self, logits: List[float], valid_token_ids: List[int]
    ) -> List[float]:
        masked = [-float("inf")] * len(logits)
        for token_id in valid_token_ids:
            masked[token_id] = logits[token_id]
        return masked

    def _next_valid_token_id(
        self, input_ids: List[int], valid_token_ids: List[int] | None
    ) -> int:
        logits = self.get_logits_from_input_ids(input_ids)
        if valid_token_ids is not None:
            logits = self.get_masked_logits(logits, valid_token_ids)
        return max(range(len(logits)), key=lambda i: logits[i])

    def generate_stream(
        self, prompt: str,
        get_valid_tokens: Callable | None = None
    ) -> Generator[Tuple[int, str], None, None]:
        input_ids: List[int] = self.encode(
            self.build_prompt(prompt)).tolist()[0]
        while True:
            if get_valid_tokens is not None:
                valid_tokens = get_valid_tokens()
            else:
                valid_tokens = None
            token_id = self._next_valid_token_id(input_ids, valid_tokens)
            input_ids.append(token_id)
            token_str = self.decode([token_id])
            yield token_id, token_str
            if token_id == self._tokenizer.eos_token_id:
                break

    def build_prompt(self, user_message: str, think: bool = False) -> Any:
        messages = [{"role": "user", "content": user_message}]
        return self._tokenizer.apply_chat_template(
            messages, tokenize=False,
            add_generation_prompt=True,
            enable_thinking=think
        )

    def get_valid_token_ids_by_predicate(
        self, predicate: Callable[[str], bool]
    ) -> List[int]:
        return [
            int(token_id) for token_str, token_id
            in self._vocab.items()
            if predicate(token_str)
        ]
