from typing import List, Dict, Generator, Callable
from src import Model, Prompt, FunctionDefinition
import re


class JSONState:
    """Tracks JSON generation state at token level"""
    def __init__(self):
        self.stack: List[str] = []
        self.start: bool = True
        self.in_string: bool = False
        self.expect_key: bool = False
        self.expect_colon: bool = False
        self.expect_value: bool = False
        self.current_key: str = None
        self.expect_parameters: bool = False
        self.current_param_index = 0


class PromptProcessor:
    """Generates structured JSON output for a given prompt"""

    def __init__(self, model: Model, prompts: List[Prompt], function_defs: List[FunctionDefinition]):
        self.model: Model = model
        self.prompts: List[Prompt] = prompts
        self.function_defs: List[FunctionDefinition] = function_defs

    def get_function_def(self, prompt: Prompt) -> FunctionDefinition:
        available_functions: List[Dict[str, str]] = [
            {"name": f.name, "description": f.description} for f in self.function_defs
        ]
        available_function_defs: List[FunctionDefinition] = self.function_defs
        generated_function: str = ''

        full_prompt: str = 'Which of the following available functions:\n' + \
        f'{available_functions}\n' + \
        f'Should be used to resolve this "{prompt}"?'
        stream: Generator[Tuple[int, str], None, None] = self.model.generate_stream(full_prompt)
        function_name_gen: str = ''
        for _, token_str in stream:
            if any(
                f.name.startswith(function_name_gen + token_str)
                for f in available_function_defs
            ):
                function_name_gen += token_str
                available_function_defs = [
                    f for f in available_function_defs
                    if f.name.startswith(function_name_gen)
                ]
            if len(available_function_defs) == 1:
                return available_function_defs[0]
        raise Exception("No function found for prompt")

    def generate_json_from_prompt(self, prompt: Prompt) -> str:
        function_def: FunctionDefinition = self.get_function_def(prompt)
        full_prompt = (
            f'Generate a JSON object based on this prompt:\n"{prompt}"\n'
            f'Use this given function:\n{function_def.full_definition}\n'
            'Output a valid JSON object with exactly these keys:\n'
            '"prompt": string\n"name": string\n"parameters": object\n'
            'Do not invent new keys or change parameter names.'
        )

        state = JSONState()
        output = ''

        def get_valid_tokens() -> List[int]:
            if state.start:
                return self.model.get_valid_token_ids_by_predicate(lambda t: t.strip() == '{')

            if state.expect_key or state.expect_value:
                if state.in_string:
                    # inside a string, allow anything except unescaped double quote
                    return None
                else:
                    # outside a string, must start with double quote for key or string value
                    return self.model.get_valid_token_ids_by_predicate(lambda t: t == '"')

            if state.expect_colon:
                return self.model.get_valid_token_ids_by_predicate(lambda t: t == ':')

            if not state.in_string:
                # allow only JSON punctuation outside string
                return self.model.get_valid_token_ids_by_predicate(lambda t: t.strip() in {',', '}'})

            return None

        def update_state(token_str: str):
            for char in token_str:
                if char == '"':
                    state.in_string = not state.in_string
                    if not state.in_string:
                        if state.expect_key:
                            state.expect_key = False
                            state.expect_colon = True
                        elif state.expect_value:
                            state.expect_value = False
                    continue

                if state.in_string:
                    continue

                if char == '{':
                    state.start = False
                    state.stack.append('{')
                    state.expect_key = True
                elif char == '}':
                    if state.stack:
                        state.stack.pop()
                elif char == ':':
                    state.expect_colon = False
                    state.expect_value = True
                elif char == ',':
                    state.expect_key = True
                    state.expect_value = False

        # Token-by-token generation
        for token_id, token_str in self.model.generate_stream(full_prompt, get_valid_tokens):
            if not state.stack and not state.start:
                break
            output += token_str
            if not state.expect_parameters and re.search(r'"parameters"\s*:\s*$', output):
                state.expect_parameters = True
                state.current_param_index = 0
                print("Entered parameters state")
            update_state(token_str)
            print(output)




        return output
