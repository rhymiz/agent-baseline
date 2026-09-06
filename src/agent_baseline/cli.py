"""Inspect, maintain, and verify evidence-backed agent guidance."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import version
from pathlib import Path

from .bootstrap import initialize, link_skill
from .doctor import doctor
from .execution import execute, project_paths
from .records import InvalidBaseline
from .skills import Agent, Scope, install_skill, skill_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        action="version",
        version=f"agent-baseline {version('agent-baseline')}",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in {
        "inspect": "read candidate paths",
        "record": "snapshot reviewed guidance",
        "check": "detect drift without executing checks",
        "verify": "execute all declared project checks",
    }.items():
        operation = commands.add_parser(command, help=help_text)
        operation.add_argument("project", nargs="?", default=".")
    init = commands.add_parser(
        "init", help="install portable guidance and create an unreviewed record draft"
    )
    init.add_argument("project", nargs="?", default=".")
    init.add_argument(
        "--agent",
        choices=[agent.value for agent in Agent],
        action="append",
        default=[],
        help="prepare native project discovery for this host; repeat for multiple hosts",
    )
    diagnose = commands.add_parser(
        "doctor",
        help="check local guidance links, skills, and host routes without executing project code",
    )
    diagnose.add_argument("project", nargs="?", default=".")
    diagnose.add_argument(
        "--path",
        action="append",
        default=[],
        help="relative guidance file to check; repeat to select multiple files",
    )
    diagnose.add_argument(
        "--agent",
        choices=[agent.value for agent in Agent],
        action="append",
        default=[],
        help="require native project discovery for this host",
    )
    skill = commands.add_parser(
        "skill", help="read bundled guidance or install it for agent discovery"
    )
    skill_commands = skill.add_subparsers(dest="skill_command", required=True)
    link = skill_commands.add_parser(
        "link",
        help="link an existing project skill into selected hosts while preserving its canonical folder",
    )
    link.add_argument("source", help="canonical skill directory inside the project")
    link.add_argument(
        "--agent",
        choices=[agent.value for agent in Agent],
        action="append",
        required=True,
    )
    link.add_argument("--project", default=".")
    skill_commands.add_parser(
        "show", help="print the skill and all references as Markdown"
    )
    install = skill_commands.add_parser(
        "install",
        help="copy guidance into an agent skill directory; preserve differing existing files",
    )
    install.add_argument(
        "--upgrade",
        action="store_true",
        help="update a managed skill only when its previous files are unchanged",
    )
    install.add_argument(
        "--agent", required=True, choices=[agent.value for agent in Agent]
    )
    install.add_argument(
        "--scope", required=True, choices=[scope.value for scope in Scope]
    )
    install.add_argument(
        "--project",
        default=None,
        help="existing project directory for project scope (default: current directory)",
    )
    args = parser.parse_args()
    try:
        if args.command == "init":
            report, code = (
                initialize(
                    Path(args.project).expanduser().resolve(),
                    tuple(Agent(value) for value in args.agent),
                ),
                0,
            )
        elif args.command == "doctor":
            root = Path(args.project).expanduser().resolve()
            paths, _ = project_paths(root)
            report = doctor(
                root, paths, args.path, tuple(Agent(value) for value in args.agent)
            )
            code = 0 if report["status"] == "passed" else 1
        elif args.command == "skill":
            if args.skill_command == "show":
                print(
                    "\n\n".join(
                        f"# File: {item.path}\n\n{item.content.decode('utf-8')}"
                        for item in skill_files()
                    )
                )
                return 0
            if args.skill_command == "link":
                report = link_skill(
                    Path(args.project).expanduser().resolve(),
                    args.source,
                    tuple(Agent(value) for value in args.agent),
                )
                print(json.dumps(report, indent=2))
                return 0
            scope = Scope(args.scope)
            if scope is Scope.USER and args.project is not None:
                raise InvalidBaseline("--project cannot be used with --scope user")
            report, code = (
                install_skill(
                    Agent(args.agent),
                    scope,
                    Path(args.project or "."),
                    upgrade=args.upgrade,
                ),
                0,
            )
        else:
            report, code = execute(
                args.command, Path(args.project).expanduser().resolve()
            )
    except (InvalidBaseline, OSError, ValueError) as error:
        report, code = {"status": "invalid", "error": str(error)}, 2
    print(json.dumps(report, indent=2))
    return code
