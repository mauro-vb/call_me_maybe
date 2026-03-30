from src import Parser, Model, PromptProcessor
import os

def main() -> None:
    print("Executing main...")
    prompts_file_path: str = os.path.join(
        'data', 'input', 'function_calling_tests.json')
    definitions_file_path: str = os.path.join(
        'data', 'input', 'functions_definition.json')
    parser: Parser = Parser(
        prompts_file_path, definitions_file_path
    )

    model: Model = Model()
    processor = PromptProcessor(
        model,
        parser.get_prompts(),
        parser.get_function_definitions())

    print(processor.generate_json_from_prompt("What is the sum of 2 and 3?"))

if __name__ == '__main__':
    main()
