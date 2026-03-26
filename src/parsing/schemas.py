from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Tuple

class Prompt(BaseModel):
    '''Prompt Schema'''
    prompt: str = Field(min_length=1)

SUPPORTED_TYPES: Tuple[str] = (
    'number', 'string', 'list', 'dictionary'
)

class FunctionDefinition(BaseModel):
    '''Functiont Definition Schema'''
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=0, max_length=500)
    parameters: Dict[str, Dict[str, str]]
    returns: Dict[str, str]
    full_definition: str

    @model_validator(mode='after')
    def validate(self) -> 'FunctionDefinition':
        '''Validates schema'''

        for param, value in self.parameters.items():
            if 'type' not in value.keys():
               raise ValueError(
                   f'Missing type for parameter {param}'
                   f' in function {self.name}'
               )
            ptype: str = value.get('type', '')
            if ptype not in SUPPORTED_TYPES:
               raise ValueError(
                   f'Unsupported parameter type {ptype}'
                   f' in function {self.name}'
               )
        return self
