from typing import List, Dict, Any
import json
from src import Prompt, FunctionDefinition
from Pydantic import ValidationError

class Parser:
    def __init__(self, prompts_file: str, fn_definitions_path: str) -> None:
        self._prompts = self._parse_file(file_path)

    @staticmethod
    def _parse_file(file_path: str) -> List[Dict]:
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)

            if not data:
                raise ValueError("File is empty")

            return data

        except FileNotFoundError:
            raise FileNotFoundError(f'Could not find file: {file_path}')
        except PermissionError:
            raise PermissionError(f'No permission to read: {file_path}')
        except json.JSONDecodeError:
            raise ValueError(f'Invalid JSON in file: {file_path}')

    def _parse_prompts(prompt_dicts: List[Dict[str, str]]) -> List[Prompts]:
        try:
            return [
                Prompt(prompt=prompt) for prompt in prompt_dicts.values()
            ]
        except ValidationError as e:
            print(f'Error while validating prompts: {e}')
            quit()

    def _parse_function_definitons(
        function_definition_dicts: List[Dict[str, Any]]
    ) -> List[FunctionDefinition]:
        try:
            return [
                FunctionDefinition(
                    name=tmp['name'],
                    name
                    description=
                ) for prompt in prompt_dicts.values()
            ]
        except ValidationError as e:
            print(f'Error while validating prompts: {e}')
            quit()

    def get_function_definitions(self) -> List[FunctionDefinition]:
        return self._funcs

    def get_prompts(self) -> List[Prompt]:
        return self._prompts
