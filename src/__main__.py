from src import Parser

def main() -> None:
    print("Executing main...")
    prompts_file_path: str = "data/input/function_calling_tests.json"
    definitions_file_path: str = "data/input/functions_definition.json"
    parser: Parser = Parser(
        prompts_file_path, definitions_file_path
    )

    defs = parser.get_function_definitions()
    prompts = parser.get_prompts()

    print(len(prompts), type(prompts))
    print(len(defs), defs)


if __name__ == '__main__':
    main()
