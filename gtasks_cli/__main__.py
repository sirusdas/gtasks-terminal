"""
Main entry point for the gtasks_cli package.

This allows the package to be executed with `python -m gtasks_cli` or `python -m gtasks_cli.setup_assistant`.
"""

import sys
import os

# Add the src directory to the path so we can import gtasks_cli modules
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Check if we're being called with a specific module like setup_assistant
if len(sys.argv) > 1:
    module_name = sys.argv[1]
    if module_name == "setup_assistant":
        # Import and run the setup assistant
        from gtasks_cli.setup_assistant import main as setup_main
        sys.exit(setup_main())
    elif module_name == "main":
        # Import and run the main CLI
        from gtasks_cli.main import main as cli_main
        cli_main()
    else:
        print(f"Unknown module: {module_name}")
        print("Available modules: setup_assistant, main")
        sys.exit(1)
else:
    # Default behavior - run the main CLI
    from gtasks_cli.main import main as cli_main
    cli_main()