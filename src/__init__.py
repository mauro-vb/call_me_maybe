__author__ = 'mauro-vb'
__version__ = '1.0.0'

# LLM SDK and Model Wrapper
from src.processing.Model import Model

# Parser
from src.parsing.schemas import Prompt, FunctionDefinition
from src.parsing.Parser import Parser

__all__ = [
    'Small_LLM_Model',
    'Parser',
    'Prompt',
    'FunctionDefinition'
]
