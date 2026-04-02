from src import Parser, Model, PromptProcessor
from typing import List, Dict
import os
import json
import argparse


def main() -> None:
    parser_cli = argparse.ArgumentParser(
        description=(
            "Generate structured JSON from"
            "prompts using function definitions"
        )
    )

    parser_cli.add_argument(
        "--input",
        type=str,
        default=os.path.join(
            'data', 'input', 'function_calling_tests.json'),
        help=(
            "Path to the prompts JSON file (default: "
            "data/input/function_calling_tests.json)"
        )
    )

    parser_cli.add_argument(
        "--functions_definition",
        type=str,
        default=os.path.join('data', 'input', 'functions_definition.json'),
        help=(
            "Path to the function definitions JSON file "
            "(default: data/input/functions_definition.json)"
        )
    )

    parser_cli.add_argument(
        "--output",
        type=str,
        default=os.path.join('data', 'output', 'results.json'),
        help=(
            "Path to save the generated JSON output "
            "(default: data/output/results.json)"
        )
    )

    parser_cli.add_argument(
        "--silent",
        action='store_true',
        help=(
            "Run silently "
        )
    )

    args = parser_cli.parse_args()

    print(f"\nUsing input prompts file: {args.input}")
    print(f"Using function definitions file: {args.functions_definition}")
    print(f"Output will be saved to: {args.output}\n\n")

    parser_obj: Parser = Parser(args.input, args.functions_definition)

    # Initialize model and processor
    model: Model = Model()
    processor: PromptProcessor = PromptProcessor(
        model,
        parser_obj.get_prompts(),
        parser_obj.get_function_definitions(),
        verbose=not args.silent
    )

    output: List[Dict] = processor.process_prompts()
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved successfully to {args.output}")


if __name__ == '__main__':
    main()
