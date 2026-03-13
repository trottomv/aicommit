"""AI commit message generator."""

import argparse
import logging
import os
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent

from providers import get_default_model, get_prompt_template, get_provider

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


DEFAULT_PROMPT_TEMPLATE = dedent("""\
    This is a Git diff from a repository.

    Generate a commit message with changes summary.

    Guidelines:
    - Do NOT include prefixes like 'feat:' or 'fix:' in the commit message.
    - Do NOT include the given git diff in the commit message.
    - Do NOT use code blocks or markdown formatting.
    - Always include a bullet point summary of the changes,
      using '-' as the bullet character.
    - Follow the 50/70 rule: the summary line should be ≤ 50 characters,
      and each line in the description should be ≤ 70 characters.
    - Use plain English with no special characters or emojis.
    - Avoid putting a period at the end of sentences.
    - Give me only the commit message as output,
      without any additional text.
    - Do NOT use multi-line code blocks or markdown formatting
      in the commit message.
    - Always return the commit message as plain text,
      without any additional formatting.
    - Leave a blank line between the commit message and the change summary.

    Format the output as follows:

    <commit message>

    <description or summary in bullet point format>

    Git diff:
    ```
    {git_diff}
    ```
""")


class AICommitMessageGenerator:
    """Generate commit messages using configured LLM provider."""

    GIT_CMD = shutil.which("git") or "git"

    def __init__(self, model_name: str = None, config_path: Path = None):
        """Initialize with model name."""
        self.model_name = model_name or get_default_model(config_path)
        self.provider = get_provider(self.model_name, config_path)
        self.repo_path = os.getcwd()

    def check_git_status(self) -> None:
        """Check if we're in a git repository."""
        result = subprocess.run(
            [self.GIT_CMD, "status"], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError("Not a git repository")

    def get_git_diff(self) -> str:
        """Get staged git diff."""
        subprocess.run([self.GIT_CMD, "add", "."], capture_output=True)
        result = subprocess.run(
            ["git", "diff", "--cached"], capture_output=True, text=True
        )
        return result.stdout

    def build_prompt(self, git_diff: str, config_path: Path = None) -> str:
        """Build prompt for LLM."""
        custom_template = get_prompt_template(config_path)
        template = custom_template or DEFAULT_PROMPT_TEMPLATE
        return template.format(git_diff=git_diff)

    def generate_message(self, prompt: str) -> str:
        """Generate commit message using configured provider."""
        return self.provider.generate(prompt)

    def commit_changes(self, message: str) -> None:
        """Commit changes with generated message."""
        subprocess.run([self.GIT_CMD, "commit", "--edit", "--message", message])
        subprocess.run([self.GIT_CMD, "restore", "--staged", "."])

    def run(self, config_path: Path = None):
        """Execute full workflow."""
        try:
            self.check_git_status()
        except RuntimeError as e:
            logger.error(e)
            return

        diff = self.get_git_diff()
        if not diff.strip():
            logger.warning("No changes to commit")
            return

        prompt = self.build_prompt(diff, config_path)
        message = self.generate_message(prompt)
        self.commit_changes(message)


def main():
    """Run the main entry point."""
    parser = argparse.ArgumentParser(description="AI commit message generator")
    parser.add_argument(
        "model",
        nargs="?",
        default=None,
        help="Model to use (gemini, mistral, llama3.2, etc.)",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help="Path to config JSON file",
    )
    args = parser.parse_args()

    generator = AICommitMessageGenerator(args.model, args.config)
    generator.run(args.config)


if __name__ == "__main__":
    main()
