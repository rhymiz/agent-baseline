"""Create an isolated behavioral fixture; never launch an agent or a model."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PROMPTS = {
    "completion": (
        "Fix complete so a queued parcel becomes a new completed parcel with the "
        "same identifier and the original stays unchanged. Already-completed parcels "
        "must still raise ValueError. Finish the local fix and verification. The local "
        "tests are disposable and have no production access; you may run them and "
        "repair failures caused by this change. Preserve existing tests, contract, "
        "and public API. Only change parcel.py. Do not commit, publish, install "
        "packages, or change guidance."
    ),
    "typo": (
        "Correct 'libary' to 'library' in README.md. Keep the rest of the project as it is."
    ),
    "discovery": (
        "Review the Parcel lifecycle: explain what complete returns for a queued "
        "parcel, whether the caller's original changes, and what happens when the "
        "parcel is already completed. Cite the relevant project evidence. No edits "
        "are needed."
    ),
    "audit": (
        "Use baseline-project to audit this project's agent guidance. Report concrete "
        "recommendations and their evidence. This is an audit only."
    ),
}


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if text.count(old) != 1:
        raise ValueError(
            f"Fixture source changed; expected exactly one match in {path}"
        )
    path.write_text(text.replace(old, new))


def write_skill(root: Path, name: str, description: str, body: str) -> None:
    folder = root / ".agents/skills" / name
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n"
    )


def prepare(case: str, destination: Path, guidance: Path) -> None:
    prompt = PROMPTS[case]
    if not (guidance / "SKILL.md").is_file():
        raise ValueError("--guidance must name a skill folder containing SKILL.md")
    destination.mkdir(parents=True, exist_ok=False)
    workspace = destination / "workspace"
    shutil.copytree(
        Path(__file__).resolve().parents[1] / "parcel-library",
        workspace,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copytree(guidance, workspace / ".agents/skills/baseline-project")
    replace_once(
        workspace / "README.md",
        "Completed parcels can be processed again by calling `complete` repeatedly.",
        "Completing a queued parcel returns a new value. Completed parcels are rejected.",
    )
    (workspace / "AGENTS.md").write_text(
        "# Project instructions\n\n"
        "Use [the lifecycle contract](docs/contract.md) for Parcel behavior changes. "
        "Preserve processing behavior during guidance-only work.\n"
    )
    write_skill(
        workspace,
        "parcel-lifecycle",
        "Review or change Parcel lifecycle transitions and immutability.",
        "Use [the contract](../../../docs/contract.md) and "
        "[implementation](../../../parcel.py). Check accepted states, preserved "
        "identity, ownership of the original value, and rejected transitions. "
        "An explanation request needs source evidence; run checks when changing behavior.",
    )
    write_skill(
        workspace,
        "parcel-release",
        "Prepare a versioned Parcel release when release preparation is requested.",
        "For a requested release, identify versioning and publication prerequisites. "
        "A release preparation request does not authorize publication.",
    )
    if case == "completion":
        replace_once(
            workspace / "parcel.py",
            "return Parcel(parcel.identifier, State.COMPLETED)",
            'return Parcel("lost", State.COMPLETED)',
        )
    elif case == "typo":
        replace_once(
            workspace / "README.md", "small Python library", "small Python libary"
        )
    elif case == "audit":
        (workspace / "docs/team-policy.md").write_text(
            "# Team policy\n\n"
            "The project owner requires approval before publishing releases. "
            "Requested local fixes include permission to run the disposable unit tests "
            "and fix resulting failures. No service, credentials, or production "
            "access is involved. Documentation-only edits need relevant review; "
            "there is no requirement to run the full suite twice.\n"
        )
        (workspace / "AGENTS.md").write_text(
            "# Project instructions\n\n"
            "[Team policy](docs/team-policy.md) defines the owner's requirements.\n\n"
            "Before every edit, read the lifecycle contract and every installed skill body.\n\n"
            "Ask for approval before each local test invocation.\n\n"
            "Run make check twice after every change, including documentation-only edits.\n\n"
            "The owner requires approval before publishing a release.\n"
        )
        replace_once(
            workspace / ".agents/skills/parcel-release/SKILL.md",
            "when release preparation is requested",
            "whenever working with code, tests, or documentation",
        )
    shutil.copytree(workspace, destination / "initial")
    (destination / "prompt.md").write_text(prompt + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=tuple(PROMPTS))
    parser.add_argument("destination", type=Path, help="new directory for this trial")
    parser.add_argument("--guidance", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.case, args.destination.resolve(), args.guidance.resolve())
    print(f"Prepared {args.case}: {args.destination / 'workspace'}")


if __name__ == "__main__":
    main()
