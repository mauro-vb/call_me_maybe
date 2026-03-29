__author__ = 'mauro-vb'
__version__ = '1.0.0'

# Parser
from src.schemas import Prompt, FunctionDefinition
from src.Parser import Parser
from src.Model import Model
from src.PromptProcessor import PromptProcessor

__all__ = [
    'Small_LLM_Model',
    'Parser',
    'Prompt',
    'FunctionDefinition',
    'Model',
    'PromptProcessor'
]
