from llm_sdk import Small_LLM_Model
from typing import Generator, List, Tuple

class Model(Small_LLM_Model):
    '''Wrapper with additional functionality for Small_LLM_Model'''

    def generate_stream(
        self,
        prompt: str,
        max_new_tokens: int = 1000
    ) -> Generator[str, None, None]:
        base_prompt: str = self.build_prompt(prompt)
        generated: str = ''

        for _ in range(max_new_tokens):
            full_prompt: str = base_prompt + generated
            token_id, token_str = self._next_token(full_prompt)
            generated += token_str

            yield token_str

            if token_id == self._tokenizer.eos_token_id:
                break
            if "<|im_end|>" in generated:
                break

    def _next_token(
        self,
        full_prompt: str,
    ) -> Tuple[int, str]:
        input_ids: List[int] = self.encode(full_prompt).tolist()[0]
        logits: List[float] = self.get_logits_from_input_ids(input_ids)
        sorted_logits: List[float] = sorted(logits, reverse=True)
        token_id: int = logits.index(sorted_logits[0])
        return token_id, self.decode([token_id])

    def build_prompt(self, user_message: str, think: bool = False) -> str:
        '''Builds well formatted prompt given a user message,
            allows for think which defaults to False'''
        messages = [
            {"role": "user", "content": user_message}
        ]

        return self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=think
        )
