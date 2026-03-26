from src import Small__LLM_Model

def main() -> None:
    print("Executing main...")
    model = Small__LLM_Model()
    print(model.encode("Hello world!"))


if __name__ == '__main__':
    main()
