"""Render stable and immutable versioned source formulas; never publish them."""
import argparse
import hashlib
from pathlib import Path
import re
import urllib.request


def render(repository, name, version, digest):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repository):
        raise ValueError("repository must be OWNER/REPO")
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", name):
        raise ValueError("name must be a lowercase, hyphen-separated formula name")
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version):
        raise ValueError("version must be X.Y.Z without a v prefix")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("sha256 must be 64 lowercase hex characters")
    template = (Path(__file__).resolve().parents[1] / "Formula/teiban-cli.rb.in").read_text()
    class_name = "".join(part.capitalize() for part in name.split("-"))
    source = template.replace("TeibanCli", class_name)
    for key, value in {"REPOSITORY": repository, "NAME": name, "VERSION": version, "SHA256": digest}.items():
        source = source.replace(f"@{key}@", value)
    # Homebrew encodes versioned names as FooAT012, not FooAT0_1_2.
    pinned = source.replace(f"class {class_name} < Formula", f"class {class_name}AT{version.replace('.', '')} < Formula")
    pinned = re.sub(r"^  head .*?$", "  keg_only :versioned_formula", pinned, flags=re.MULTILINE)
    return source, pinned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--sha256", help="render offline using a previously verified archive checksum")
    parser.add_argument("--output-dir", type=Path, default=Path("Formula"))
    args = parser.parse_args()
    # Validate untrusted parameters before using them in a URL or path.
    render(args.repository, args.name, args.version, args.sha256 or "0" * 64)
    digest = args.sha256
    if digest is None:
        url = f"https://github.com/{args.repository}/archive/refs/tags/v{args.version}.tar.gz"
        checksum = hashlib.sha256()
        with urllib.request.urlopen(url, timeout=60) as response:
            while chunk := response.read(1024 * 1024):
                checksum.update(chunk)
        digest = checksum.hexdigest()
    stable, pinned = render(args.repository, args.name, args.version, digest)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fixed_path = args.output_dir / f"{args.name}@{args.version}.rb"
    # Reruns may reproduce an existing formula; never replace a different pin.
    if fixed_path.exists() and fixed_path.read_text() != pinned:
        raise ValueError(f"refusing to overwrite immutable formula: {fixed_path}")
    fixed_path.write_text(pinned)
    (args.output_dir / f"{args.name}.rb").write_text(stable)
    print(f"Rendered {args.name} and {args.name}@{args.version} in {args.output_dir}")


if __name__ == "__main__":
    main()
