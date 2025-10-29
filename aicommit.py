"""A script that generate a commit message using the Gemini API."""

import argparse
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
        GEMINI_API_KEY (str): API key for the Gemini API.
        MISTRAL_API_KEY (str): API key for the Mistral API.
        LLM_MODEL (str): The name of the Gemini model to use.
        BASE_URL (str): The base url for the Gemini and Mistral API.
        repo_path (str): Path to the Git repository.

    """

    def __init__(self, model: str = "gemini", service: str = None):
        """
        Initialize the CommitMessageGenerator with the API key and model.

        Args:
            model (str): The name of the Gemini model to use.
                Default is "gemini-2.5-flash".
            service (str): The API service to use.
                Default is "None".

        """
        self.SERVICE = service
        LLM_MODELS = {
            "gemini": "gemini-2.5-flash",
            "gemini-2": "gemini-2.0-flash",
            "mistral-small": "mistral-small-latest",
            "mistral-large": "mistral-large-latest",
        }
        self.LLM_MODEL = LLM_MODELS.get(model, model)
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        if "ollama" in service:
            self.OLLAMA_BASE_URL = os.getenv(
                "OLLAMA_BASE_URL", "http://localhost:11434"
            )
            self.BASE_URL = f"{self.OLLAMA_BASE_URL}/v1/chat/completions"
        elif "gemini" in model:
            self.BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
        elif "mistral" in model:
            self.BASE_URL = "https://api.mistral.ai/v1/chat/completions"
        if (
            "ollama" not in service
            and not self.GEMINI_API_KEY
            and not self.MISTRAL_API_KEY
        ):
            raise OSError(
                "GEMINI_API_KEY or MISTRAL_API_KEY environment variable is not set."
            )
        self.repo_path = os.getcwd()

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
            - Do NOT use code blocks or markdown formatting.
            - Always include a bullet point summary of the changes, using '-' as the bullet character.
            - Follow the 50/70 rule: the summary line should be ≤ 50 characters, and each line in the description should be ≤ 70 characters.
            - Use plain English with no special characters or emojis.
            - Avoid putting a period at the end of sentences.
            - Give me only the commit message as output, without any additional text.
            - Do NOT use multi-line code blocks or markdown formatting in the commit message.
            - Always return the commit message as plain text, without any additional formatting.
            - Leave a blank line between the commit message and the change summary.
            - Format the output as follows:

            <commit message>

            <description or summary in bullet point format>

            Git diff:
            ```
            {git_diff}
            ```
        """  # noqa: E501
        return prompt

    def call_gemini_api(self, prompt: str) -> str:
        """
        Send the prompt to the Gemini API and retrieve the response.

        Args:
            prompt (str): The prompt to send.

        Returns:
            str: The commit message returned by the model.

        """
        url = (
            f"{self.BASE_URL}{self.LLM_MODEL}:generateContent?key={self.GEMINI_API_KEY}"
        )
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

    def call_mistral_api(self, prompt: str) -> str:
        """
        Send the prompt to the Mistral API and retrieve the response.

        Args:
            prompt (str): The prompt to send.

        Returns:
            str: The commit message returned by the model.

        """
        payload = {
            "model": self.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }
        request = urllib.request.Request(
            self.BASE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.MISTRAL_API_KEY}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                response_data = response.read()
                response_json = json.loads(response_data)
        except urllib.error.HTTPError as e:
            print("Errore HTTP:", e.code)
            print("Dettagli:", e.read().decode())
            raise ValueError("HTTP error occurred while calling Mistral API.") from e
        else:
            return response_json["choices"][0]["message"]["content"]

    def call_ollama_api(self, prompt: str) -> str:
        """
        Send the prompt to the Ollama API and retrieve the response.

        Args:
            prompt (str): The prompt to send.

        Returns:
            str: The commit message returned by the model.

        """
        payload = {
            "model": self.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "chat_template_kwargs": {"enable_thinking": False},
        }
        request = urllib.request.Request(
            self.BASE_URL,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                response_data = response.read()
                response_json = json.loads(response_data)
        except urllib.error.HTTPError as e:
            print("Errore HTTP:", e.code)
            print("Dettagli:", e.read().decode())
            raise ValueError("HTTP error occurred while calling Ollama API.") from e
        else:
            return response_json["choices"][0]["message"]["content"]

    def call_api(self, prompt: str) -> str:
        """
        Call the appropriate API based on the model specified.

        Args:
            prompt (str): The prompt to send.

        Returns:
            str: The commit message returned by the model.

        """
        if "ollama" in self.SERVICE:
            return self.call_ollama_api(prompt)
        elif "gemini" in self.SERVICE:
            return self.call_gemini_api(prompt)
        elif "mistral" in self.SERVICE:
            return self.call_mistral_api(prompt)
        else:
            raise ValueError("Unsupported model specified.")

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
        commit_message = self.call_api(prompt)
        self.commit_changes(commit_message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI commit message generator.")
    parser.add_argument(
        "model",
        nargs="?",
        default="gemini",
        help="LLM model to use (e.g., mistral, llama3.2, "
        "gemini, mistral-small, mistral-large)",
    )
    parser.add_argument(
        "service",
        nargs="?",
        default="gemini",
        help="API service to use (e.g., ollama, gemini, mistral)",
    )
    args = parser.parse_args()
    AICommitMessageGenerator(model=args.model, service=args.service).run()
