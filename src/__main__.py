from src import PromptParser

def main() -> None:
    print("Executing main...")
    prompts_file_path: str = "/goinfre/mvazquez/call_me_maybe/data/input/function_calling_tests.json"
    PromptParser(prompts_file_path)


if __name__ == '__main__':
    main()
