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
        self.number_has_digit = False
        self.bool_written = False


class PromptProcessor:
    """Generates structured JSON output for a given prompt"""

    def __init__(
        self,
        model: Model,
        prompts: List[Prompt],
        function_defs: List[FunctionDefinition],
        verbose: bool = True
    ) -> None:
        self.model: Model = model
        self.prompts: List[Prompt] = prompts
        self.function_defs: List[FunctionDefinition] = function_defs
        self.verbose: bool = verbose

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
        if self.verbose:
            print(f'\nGenerating json for "{prompt.prompt}":')
        try:
            function_def: FunctionDefinition = self.get_function_def(prompt)
        except Exception:
            raise ValueError('No valid function found...')
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

            def is_valid_bool_token(t: str) -> bool:
                candidate = state.bool_buffer + t.strip()
                return any(
                    b.startswith(candidate) for b in ["true", "false"]
                )

            def is_valid_number_token(t: str, is_integer: bool) -> bool:
                t = t.strip()
                dot = '' if is_integer else '.'
                return all(c in "0123456789-" + dot for c in t)

            def is_valid_number_or_end(t: str, is_integer: bool) -> bool:
                if is_end_token(t):
                    return state.number_has_digit
                return is_valid_number_token(t, is_integer)

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
                        if value['type'] in ('number', 'integer', 'double', 'float'):
                            return self.model.get_valid_token_ids_by_predicate(
                                lambda t: is_valid_number_or_end(
                                    t, value['type'] == 'integer'
                                ) or is_end_token(t)
                            )
                        if value['type'] == 'boolean':
                            if state.bool_written:
                                return self.model.get_valid_token_ids_by_predicate(
                                    lambda t: is_end_token(t)
                                )
                            state.bool_written = True
                            return self.model.get_valid_token_ids_by_predicate(
                                    lambda t: t.strip() in {"true", "false"}
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
                if char.isdigit():
                    state.number_has_digit = True
                if char == '"':
                    state.in_string = not state.in_string
                    if state.in_string:
                        state.buffer = ''
                    else:
                        if state.expect_key:
                            state.current_key = state.buffer
                            state.bool_written = False
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
                    state.number_has_digit = False

        for token_id, token_str in self.model.generate_stream(
            full_prompt, get_valid_tokens
        ):
            if not state.stack and not state.start:
                break
            output += token_str
            if self.verbose:
                print("\r" + output, end="", flush=True)
            update_state(token_str)
        try:
            return dict(json.loads(output))
        except (json.JSONDecodeError, ValueError):
            if self.verbose:
                print(f"Couldn't parse dictionary from LLM Output.\n{output}")
            return {"prompt": prompt.prompt}

    def process_prompts(self) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []
        for prompt in self.prompts:
            output.append(self.generate_dict_from_prompt(prompt))
        return output
