from llm_sdk import Small_LLM_Model
from typing import Generator, List, Tuple

class Model(Small_LLM_Model):
    '''Wrapper with additional functionality for Small_LLM_Model'''

    def generate_stream(
        self,
        prompt: str,
        previous_tokens: str = '',
    ):
        base_ids: List[int] = self.encode(self.build_prompt(prompt)).tolist()[0]
        prev_ids: List[int] = self.encode(previous_tokens).tolist()[0]

        input_ids: List[int] = base_ids + prev_ids

        while True:
            token_id: int = self._next_token_ids(input_ids)
            input_ids.append(token_id)

            token_str: str = self.decode([token_id])
            yield token_str

            if token_id == self._tokenizer.eos_token_id:
                break
            if "<|im_end|>" in token_str:
                break


    def generate_token(self, prompt: str, previous_tokens: str) -> str:
        base_prompt: str = self.build_prompt(prompt)
        full_prompt: str = base_prompt + previous_tokens
        return self._next_token(full_prompt)[1]

    def _next_token(
        self,
        full_prompt: str,
    ) -> Tuple[int, str]:
        input_ids: List[int] = self.encode(full_prompt).tolist()[0]
        logits: List[float] = self.get_logits_from_input_ids(input_ids)
        sorted_logits: List[float] = sorted(logits, reverse=True)
        token_id: int = logits.index(sorted_logits[0])
        return token_id, self.decode([token_id])

    def _next_token_ids(
        self,
        input_ids: List[int],
    ) -> Tuple[int, str]:
        logits: List[float] = self.get_logits_from_input_ids(input_ids)
        return max(range(len(logits)), key=lambda i: logits[i])

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
