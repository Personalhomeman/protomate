import getpass
import os
import shutil
import subprocess
import sys
from pprint import pprint

import colorama
import questionary
from github import Github
from loguru import logger
from prompt_toolkit.styles import Style
from pyfiglet import figlet_format
from termcolor import cprint

import protomate.languages as languages

colorama.init(strip=not sys.stdout.isatty())

LOG_FILENAME = "logs/logfile.log"

logger.remove(0)
logger.add(
    LOG_FILENAME,
    format="-------------||time:{time}||level:{level}||-------------\n{message}\n",
    level="ERROR",
    backtrace=True,
    diagnose=False,
    enqueue=True,
    rotation="1 MB",
)


def cli():

    text = "protomate"
    ascii_banner = figlet_format(text, font="standard")
    cprint(ascii_banner, "cyan", attrs=["bold"])

    style = Style(
        [
            ("qmark", "fg:#E91E63 bold"),
            ("answer", "fg:#fac731 bold"),
            ("instruction", "fg:#ef8a62"),
            ("separator", "fg:#cc5454"),
            ("selected", "fg:#7fc97f"),
            ("pointer", "fg:#fdc086"),
            ("question", ""),
        ]
    )

    questions = [
        {"type": "text", "name": "github_username", "message": "GitHub Username:"},
        {"type": "password", "name": "github_password", "message": "GitHub Password:"},
        {"type": "text", "name": "repo_name", "message": "Repository Name:"},
        {
            "type": "select",
            "name": "repo_type",
            "message": "Repository Type:",
            "choices": ["Public", "Private"],
        },
        {
            "type": "text",
            "name": "gitignore",
            "message": "(Optional) Please enter language name to create .gitignore file,\n press enter if you don't want to:",
        },
    ]

    answers = questionary.prompt(questions, style=style)

    github_username = answers["github_username"]
    github_password = answers["github_password"]
    repo_name = answers["repo_name"]
    repo_type = answers["repo_type"]
    gitignore = answers["gitignore"]

    return github_username, github_password, repo_name, repo_type, gitignore


def authentication(github_username, github_password):

    g = Github(github_username, github_password)
    user = g.get_user()

    try:
        user.login

    except Exception as e:
        logger.exception(e)
        sys.exit("AuthError: Username or password is incorrect")

    return (g, user)


def create_local_repo(repo_name):

    try:
        os.mkdir(repo_name)

    except Exception as e:
        logger.error(e)
        sys.exit(f"LocalExistsError: Local repository '{repo_name}' already exists")


def create_remote_repo(g, github_username, repo_name, repo_type):

    user = g.get_user()

    try:
        if repo_type == "Private":
            user.create_repo(repo_name, private=True)

        else:
            user.create_repo(repo_name, private=False)
    except Exception as e:
        logger.exception(e)
        sys.exit(
            f"RemoteCreationError: Remote repository '{repo_name}' already exists "
        )


def connect_local_to_remote(repo_name, github_username, gitignore):

    cmd = f"""
            cd {repo_name}
            git init
            git remote add origin git@github.com:{github_username}/{repo_name}.git
            touch README.md
            git add .
            git commit -m "Initial commit"
            git push -u origin master
            code .
                """

    cmd_gitignore = f"""
                cd {repo_name}
                git init
                git remote add origin git@github.com:{github_username}/{repo_name}.git
                touch README.md
                curl -X GET https://www.gitignore.io/api/{gitignore} > .gitignore
                git add .
                git commit -m "Initial commit"
                git push -u origin master
                code .
                """

    try:
        if gitignore != "" and gitignore.lower() in languages.PROGRAMMING_LANGUAGES:
            cmd_gitignore
            subprocess.check_output(cmd_gitignore, shell=True)

        elif (
            gitignore != "" and gitignore.lower() not in languages.PROGRAMMING_LANGUAGES
        ):
            print("Language not supported:\n Creating repository without .gitignore")
            cmd
            subprocess.check_output(cmd, shell=True)

        else:
            cmd
            subprocess.check_output(cmd, shell=True)

        print("Local and remote repository successfully created")

    except Exception as e:
        logger.exception(e)
        sys.exit("Local and remote repository cannot be connected")


def main():
    github_username, github_password, repo_name, repo_type, gitignore = cli()
    print("")
    print("Thanks for all your information, hang tight while we are at it...")

    g, user = authentication(github_username, github_password)

    create_local_repo(repo_name)

    create_remote_repo(g, github_username, repo_name, repo_type)

    connect_local_to_remote(repo_name, github_username, gitignore)


if __name__ == "__main__":
    main()
