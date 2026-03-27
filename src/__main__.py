from src import Parser, Model

def main() -> None:
    print("Executing main...")
    prompts_file_path: str = "data/input/function_calling_tests.json"
    definitions_file_path: str = "data/input/functions_definition.json"
    parser: Parser = Parser(
        prompts_file_path, definitions_file_path
    )

    model: Model = Model()
    stream = model.generate_stream('Who is the richest man on earth?', max_new_tokens= 10000)
    for token in stream:
        print(token, end="")


if __name__ == '__main__':
    main()
