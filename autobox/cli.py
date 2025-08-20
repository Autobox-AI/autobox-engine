"""CLI entry points for autobox."""
import asyncio
import os


def main():
    """Main entry point for autobox command."""
    from autobox.main import main as async_main
    asyncio.run(async_main())


def run_with_env():
    """Entry point that sets OBJC_DISABLE_INITIALIZE_FORK_SAFETY environment variable."""
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "TRUE"
    main()


if __name__ == "__main__":
    main()