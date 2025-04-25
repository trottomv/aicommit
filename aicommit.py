"""A script that generate a commit message using the Gemini API."""

import json
import logging
import os
import subprocess
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AICommitMessageGenerator:
    """
    A class to generate commit messages using the Gemini API based on a Git diff.

    Attributes:
        API_KEY (str): API key for the Gemini API.
        LLM_MODEL (str): The name of the Gemini model to use.
        BASE_URL (str): The base url for the Gemini API.
        repo_path (str): Path to the Git repository.

    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the CommitMessageGenerator with the API key and model.

        Args:
            model (str): The name of the Gemini model to use.
                Default is "gemini-2.0-flash".

        """
        self.API_KEY = os.getenv("GEMINI_API_KEY")
        self.LLM_MODEL = model
        self.BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
        self.repo_path = os.getcwd()

        if not self.API_KEY:
            raise OSError("GEMINI_API_KEY environment variable is not set.")

    def check_git_status(self) -> None | OSError:
        """
        Check the Git status to see if there are changes to commit.

        Raises:
            OSError: If there are no changes to commit.

        """
        git_status = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True,
        )
        if error := git_status.stderr:
            raise OSError(error)

    def get_git_diff(self) -> str:
        """
        Get the current Git diff from the repository.

        Returns:
            str: The output of `git diff`.

        """
        subprocess.run(["git", "add", "."])
        return subprocess.run(
            ["git", "diff", "--cached"], capture_output=True, text=True
        ).stdout

    def build_prompt(self, git_diff: str) -> str:
        """
        Build the prompt to send to the LLM using the Git diff.

        Args:
            git_diff (str): The Git diff to include in the prompt.

        Returns:
            str: The prompt for the LLM.

        """
        prompt = f"""
            This is a Git diff from a repository.

            Generate a commit message with changes summary.

            Guidelines:
            - Do NOT include prefixes like 'feat:' or 'fix:' in the commit message.
            - Do NOT include the given git diff in the commit message.
            - Always include a bullet point summary of the changes,
              using '-' as the bullet character.
            - Follow the 50/70 rule: the summary line should be ≤ 50 characters,
              and each line in the description should be ≤ 70 characters.
            - Use plain English with no special characters or emojis.
            - Format the output as follows:

            <commit message>

            <description or summary in bullet point format>

            {git_diff}
        """
        return prompt

    def call_gemini_api(self, prompt: str) -> str:
        """
        Send the prompt to the Gemini API and retrieve the response.

        Args:
            prompt (str): The prompt to send.

        Returns:
            str: The commit message returned by the model.

        """
        url = f"{self.BASE_URL}{self.LLM_MODEL}:generateContent?key={self.API_KEY}"

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request) as response:
            response_data = response.read()
            response_json = json.loads(response_data)

        return response_json["candidates"][0]["content"]["parts"][0]["text"]

    def commit_changes(self, message: str):
        """
        Add all changes, commit them with the generated message, and unstage files.

        Args:
            message (str): The commit message.

        """
        subprocess.run(["git", "commit", "--edit", "--message", message])
        subprocess.run(["git", "restore", "--staged", "."])

    def run(self):
        """Execute the full commit message generation and Git commit process."""
        logger.info(f"Current repo path: {self.repo_path}")
        try:
            self.check_git_status()
        except OSError as err:
            logger.error(err)
            return

        diff = self.get_git_diff()

        if not diff.strip():
            logger.warning("No changes to commit.")
            return

        prompt = self.build_prompt(diff)
        commit_message = self.call_gemini_api(prompt)
        self.commit_changes(commit_message)


if __name__ == "__main__":
    AICommitMessageGenerator().run()
