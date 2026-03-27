from typing import List, Dict, Any
import json
from src import Prompt, FunctionDefinition
from pydantic import ValidationError

class Parser:
    '''Parsing helper to extract prompts and function definitions'''
    def __init__(self, prompts_file: str, fn_definitions_path: str) -> None:
        '''Sets up helper, expects paths to prompt and definition jsons.'''
        self._prompts = self._parse_prompts(prompts_file)
        self._function_defs = self._parse_function_defs(fn_definitions_path)

    def get_function_definitions(self) -> List[FunctionDefinition]:
        return self._function_defs

    def get_prompts(self) -> List[Prompt]:
        return self._prompts

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

    def _parse_prompts(self, f: str) -> List[Prompt]:
        prompt_dicts: List[Dict[str, str]] = self._parse_file(f)
        try:
            prompts: List[Dict[str, str]] = []
            for prompt_dict in prompt_dicts:
                prompts.append(Prompt(prompt=prompt_dict['prompt']))
            return prompts
        except KeyError as e:
            print(f'Missing key in prompt: {e}')
        except ValidationError as e:
            print(f'Error while validating prompts: {e}')
            quit()

    def _parse_function_defs(self, f: str) -> List[FunctionDefinition]:
        def_dicts: List[Dict[str, Any]] = self._parse_file(f)
        try:
            defs: List[FunctionDefinition] = []
            for def_dict in def_dicts:
                defs.append(
                    FunctionDefinition(
                        name=def_dict['name'],
                        description=def_dict['description'],
                        parameters=def_dict['parameters'],
                        returns=def_dict['returns'],
                        full_definition=str(def_dict)
                    )
                )
            return defs
        except KeyError as e:
            print(f'Missing key in function definition: {e}')
        except ValidationError as e:
            print(f'Error while validating prompts: {e}')
            quit()
