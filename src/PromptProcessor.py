from typing import List, Dict, Generator
from src import Model
from src import Prompt, FunctionDefinition


class PromptProcessor:
    '''Translator class that prompts Model to generate
    structured function calls based on natural language'''
    def __init__(
        self,
        model: Model,
        prompts: List[Prompt],
        function_defs: List[FunctionDefinition],
    ) -> None:
        self.model = Model()
        self.prompts: List[Prompt] = prompts,
        self.function_defs: List[FunctionDefinition] = function_defs

    def get_available_functions(self) -> List[Dict[str, str]]:
        '''Returns list of get_available_functions'''
        return [
            {'name': f.name, 'description': f.description}
            for f in self.function_defs
        ]

    def generate_function_name(self, prompt: str) -> str:
        available_functions: List[Dict[str, str]] = self.get_available_functions()
        generated_function: str = ''

        full_prompt: str = 'Which of the following available functions:\n' + \
        f'{available_functions}\n' + \
        f'Should be used to resolve this "{prompt}"?'
        stream: Generator[str, None, None] = self.model.generate_stream(full_prompt)
        function_name_gen: str = ''
        for generation in stream:
            if any(
                f['name'].startswith(function_name_gen + generation)
                for f in available_functions
            ):
                function_name_gen += generation
                available_functions = [
                    f for f in available_functions
                    if f['name'].startswith(function_name_gen)
                ]
            if len(available_functions) == 1:
                return available_functions[0]['name']

        return 'NO FUNCTION FOUND'


    def generate_parameters(self, prompt: Prompt, function_name: str) -> Dict[str, str]:
        pass

    #def generate_number_parameter

    #def generate_str_parameter
