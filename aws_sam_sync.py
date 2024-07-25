import os

import boto3
import click
from botocore.exceptions import ClientError, ProfileNotFound
from git import Repo
from mypy_boto3_cloudformation.client import CloudFormationClient
from mypy_boto3_cloudformation.type_defs import StackSummaryTypeDef


def get_cloudformation_client(region: str, profile: str) -> CloudFormationClient:
    if profile:
        boto3.setup_default_session(profile_name=profile)
    return boto3.client("cloudformation", region_name=region)


def get_cloudformation_stacks(cloudformation_client: CloudFormationClient) -> list[StackSummaryTypeDef]:
    """Return all cloudformation stacks"""
    stacks = []
    response = cloudformation_client.list_stacks()
    stacks.extend(response["StackSummaries"])
    next_token = response.get("NextToken")
    while next_token:
        cloudformation_client.list_stacks(NextToken=next_token)
        stacks.extend(response["StackSummaries"])
        next_token = response["NextToken"]
    return stacks


def get_closest_stack_name(stacks: list[StackSummaryTypeDef], partial_stack_name: str) -> str:
    """Find the shortest and closest stack name"""
    possible_stacks = []
    for stack in stacks:
        if partial_stack_name in stack["StackName"]:
            possible_stacks.append(stack["StackName"])
    if not possible_stacks:
        raise NotEnoughCloudformationStacks("There is not enough matching cloudformation stacks to compare.")
    return min(possible_stacks, key=len)


class NotExistingRepo(Exception):
    pass


class NotEnoughCloudformationStacks(Exception):
    pass


def current_branch() -> str:
    """Return current branch if .git folder exists"""
    if not os.path.exists(os.path.join(os.getcwd(), ".git/")):
        raise NotExistingRepo("There is not .git folder")
    repo = Repo(os.getcwd())
    if not repo or not repo.active_branch:
        raise NotExistingRepo("There is no git repository")
    return str(repo.active_branch)


def sam_sync(stack_name: str, profile=None, build_image=None):
    pass


def info(message: str):
    click.echo(click.style(message, fg="yellow"))


def success(message: str):
    click.echo(click.style(message, fg="green"))


def error(message: str):
    click.echo(click.style(message, fg="red"))


@click.command()
@click.option("--build-image")
@click.option("--region")
@click.option("--profile")
def cli(*,build_image=None, profile=None, region="eu-central-1"):
    click.clear()
    try:
        cb = current_branch()
        success(f"Current branch: {cb}")
    except NotExistingRepo as ne:
        error(str(ne))
        exit(0)
    info("Retrieving cloudformation stacks...")
    try:
        cloudformation_client = get_cloudformation_client(region, profile)
        cloudformation_stacks = get_cloudformation_stacks(cloudformation_client)
    except (ClientError, ProfileNotFound) as e:
        error(str(e))
        exit(0)
    success("Done!")
    try:
        stack_name = get_closest_stack_name(cloudformation_stacks, cb)
    except NotEnoughCloudformationStacks as ne:
        error(str(ne))
        exit(0)
    info("Starting sam sync...")
    sam_sync(stack_name, profile, build_image)


if __name__ == "__main__":
    cli()
