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

    function_name = processor.generate_function_name("Replace all vowels in 'Programming is fun' with asterisks")
    print(function_name)

if __name__ == '__main__':
    main()
