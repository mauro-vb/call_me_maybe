from typing import List, Dict, Generator, Any
from src import Prompt, FunctionDefinition
from src.Model import Model
import json


class JSONState:
    """Tracks JSON generation state at token level"""
    def __init__(self) -> None:
        self.generated_root_keys: set = set()
        self.stack: List[str] = []
        self.start: bool = True
        self.in_string: bool = False
        self.expect_key: bool = False
        self.expect_colon: bool = False
        self.expect_value: bool = False
        self.current_key: str = ''
        self.buffer: str = ''


class PromptProcessor:
    """Generates structured JSON output for a given prompt"""

    def __init__(
        self,
        model: Model,
        prompts: List[Prompt],
        function_defs: List[FunctionDefinition],
    ) -> None:
        self.model: Model = model
        self.prompts: List[Prompt] = prompts
        self.function_defs: List[FunctionDefinition] = function_defs

    def get_function_def(
        self, prompt: Prompt
    ) -> FunctionDefinition:
        available_functions: List[Dict[str, str]] = [
            {
                "name": f.name,
                "description": f.description
            }
            for f in self.function_defs
        ]
        available_fn_defs: List[FunctionDefinition] = self.function_defs

        full_prompt: str = (
            'Which of the following available functions:\n'
            f'{available_functions}\n'
            f'Should be used to resolve this "{prompt}"?'
        )
        stream: Generator = self.model.generate_stream(full_prompt)
        function_name_gen: str = ''
        for _, token_str in stream:
            if any(
                f.name.startswith(function_name_gen + token_str)
                for f in available_fn_defs
            ):
                function_name_gen += token_str
                available_fn_defs = [
                    f for f in available_fn_defs
                    if f.name.startswith(function_name_gen)
                ]
            if len(available_fn_defs) == 1:
                return available_fn_defs[0]
        raise Exception("No function found for prompt")

    def generate_dict_from_prompt(self, prompt: Prompt) -> Dict:
        function_def: FunctionDefinition = self.get_function_def(prompt)
        full_prompt = (
            'Generate a JSON object based on this prompt:'
            f'\n"{prompt.prompt}"\n'
            f'Use this given function:\n{function_def.full_definition}\n'
            'Here is an example:\n'
            '{"prompt":"Reverse the string \'chocolate\'"'
            ',"name":"fn_reverse_string","parameters":{"s":"hello"}}'
            'Output a valid JSON object with exactly these keys:\n'
            '"prompt": string\n"name": string\n"parameters": object\n'
            'Do not invent new keys or change parameter names.'
        )

        state = JSONState()
        output = ''

        def get_valid_tokens() -> List[int] | None:
            def is_number_token(t: str) -> bool:
                t = t.strip()
                return all(c in "0123456789-." for c in t)

            def is_valid_str_token(t: str) -> bool:
                quote_count: int = t.count('"')
                if quote_count < 2:
                    return True
                return False

            def is_end_token(t: str) -> bool:
                return t.strip() in {",", "}"}

            if state.start:
                return self.model.get_valid_token_ids_by_predicate(
                    lambda t: t.strip() == '{')

            if state.expect_key:
                if state.in_string:
                    return self.model.get_valid_token_ids_by_predicate(
                        lambda t: is_valid_str_token(t))
                else:
                    return self.model.get_valid_token_ids_by_predicate(
                        lambda t: t == '"')

            if state.expect_value:
                if state.in_string:
                    return self.model.get_valid_token_ids_by_predicate(
                        lambda t: is_valid_str_token(t))
                if state.current_key in ('prompt', 'name'):
                    return self.model.get_valid_token_ids_by_predicate(
                        lambda t: t == '"')
                if state.current_key == 'parameters':
                    return self.model.get_valid_token_ids_by_predicate(
                        lambda t: t.strip() == '{')
                for param_name, value in function_def.parameters.items():
                    if state.current_key == param_name:
                        if value['type'] == 'string':
                            return self.model.get_valid_token_ids_by_predicate(
                                lambda t: t.strip() == '"')
                        if value['type'] == 'number':
                            return self.model.get_valid_token_ids_by_predicate(
                                lambda t: is_number_token(t) or is_end_token(t)
                            )

            if state.expect_colon:
                return self.model.get_valid_token_ids_by_predicate(
                    lambda t: t == ':')

            if not state.in_string:
                return self.model.get_valid_token_ids_by_predicate(
                    lambda t: is_end_token(t))

            return None

        def update_state(token_str: str) -> None:
            for char in token_str:
                if char == '"':
                    state.in_string = not state.in_string
                    if state.in_string:
                        state.buffer = ''
                    else:
                        if state.expect_key:
                            state.current_key = state.buffer
                            state.expect_key = False
                            state.expect_colon = True
                        elif state.expect_value:
                            state.expect_value = False
                    continue

                if state.in_string:
                    state.buffer += char
                    continue

                if char == '{':
                    state.start = False
                    state.stack.append('{')
                    state.expect_key = True
                elif char == '}':
                    state.expect_value = False
                    if state.stack:
                        state.stack.pop()
                elif char == ':':
                    state.expect_colon = False
                    state.expect_value = True
                elif char == ',':
                    state.expect_key = True
                    state.expect_value = False

        for token_id, token_str in self.model.generate_stream(
            full_prompt, get_valid_tokens
        ):
            if not state.stack and not state.start:
                break
            output += token_str
            update_state(token_str)
        try:
            return dict(json.loads(output))
        except json.JSONDecodeError:
            print(f"Couldn't parse dictionary from LLM Output...\n{output}")
            return {"prompt": prompt.prompt}

    def process_prompts(self) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []
        for prompt in self.prompts:
            output.append(self.generate_dict_from_prompt(prompt))
        return output
