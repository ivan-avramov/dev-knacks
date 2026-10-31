"""Independent contracts for the dev-knacks marketplace conversion.

Run from the repository root:
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests

Only stdlib; no network, CLI installs, or execution of skill instructions.
Each test docstring identifies its role. Source fingerprints were frozen before
implementation; this suite has no runtime dependency on the source checkout.
CLI validation and isolated plugin installs remain separate acceptance checks.

Reference interpretation: README navigation may leave the skill folder but must
resolve inside this repository. Known references to runtime instruction files,
generated review output, and review-panel's runtime guide are explicitly scoped
below; they are not missing files to add to the packaged skill.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
VERSIONS = {
    "review-assistant": "0.1.0",
    "four-eyes": "0.7.0",
    "review-panel": "0.5.0",
    "vnote": "0.1.0",
}
SOURCE_URL = "https://github.com/ivan-avramov/dev-knacks"
CHECK_COMMAND = "python3 -m unittest discover -s tests"
CLAUDE_TEXT = (
    "# CLAUDE.md\n\n"
    "This file provides guidance to Claude Code (claude.ai/code) when working "
    "with code in this repository.\n\n@AGENTS.md\n"
)

SOURCE_DIGESTS = {'skills/review-assistant/SKILL.md': 'f751d65c32e2178547178b6e33ef087c26590c6f43c747df449443cda7bf77a2',
 'skills/review-assistant/references/benchmark-poc.md': 'ab0bd961365fa710b7580084b43d1bb05d7802e9a6e4bbda0e6ecfb6f7252d8a',
 'skills/review-assistant/references/design-doc.md': '701788832362dff5ff8a0f71b8e428650511ed89d70dec2ed187d30a2b7ecfc2',
 'skills/review-assistant/references/patent-disclosure.md': '41d18a72d0b5148af021018dab60fafa27fda073fb0899d5c0cc4ad14c398344',
 'skills/review-assistant/references/patent-portfolio.md': 'b692a86bf71a785f89835c1cfaa66aec6562fef37ab0eb37bc91200dd2a6bb4d',
 'skills/review-assistant/references/product-vendor.md': '93b9c9fcfb37d6990262646161cec223f954a72fdd77055f84d3651b79a45cfb',
 'skills/review-assistant/references/repo-code.md': '4ed493a6b40187ef5ca34badf844c38f1d8a245c0c184307b47786a114648dcf',
 'skills/four-eyes/SKILL.md': 'd541b135a1ec6621416bec09f08742ebd9a9a1720320b39eb1b5d5edcb9e36db',
 'skills/four-eyes/briefs.md': '7f2bf34ada58c7ed7c981106e14123545301e1459a90b581c670315c4ec0c82d',
 'skills/review-panel/SKILL.md': '7d70eddb446357a27c5b0de05ecda5a706686fc5501cc56324d9340033365c21',
 'skills/review-panel/panel.example.toml': 'fe96eb38f8aad12ae11506d5015f96be1c5596248901ea87a3e9b17a68d2e6b4',
 'skills/review-panel/runtimes.md': '3f63c9f40abf86f6136cf86514f2a349e67edc4821cf2d0edf79182ac2f507ed',
 'skills/vnote/SKILL.md': '473aaaf5f7da2437cf5b9d7800d24f34a523e2cfc7627a55560e503682c9e419'}

BODY_DIGESTS = {'skills/review-assistant/SKILL.md': '7c4ece004a995388062e9a7b9f9e1233bf4150e2d75e8d3246e947a8e49cd0a4',
 'skills/four-eyes/SKILL.md': 'f97394e65ec9bd38b502f35df49f4d724155ac63ef067f4de619701c2c158b03',
 'skills/review-panel/SKILL.md': 'd9d79df55ee4a7b93dfaf1c5070c53c3d27081770df9e0cfd90e7762a9bd597e',
 'skills/vnote/SKILL.md': 'f45d1d30d0b8f520aec8b76e9f762311654ea9ee4e0c29a7e76e9b567b3b763e'}

CROSS_REFERENCE_LINES = {}

EXTRA_DIGESTS = {'extras/four-eyes/CLAUDE.snippet.md': '48421f05d1073345bc21859ebabe9e718b5ad9110b778be27504517ba1c5f5da',
 'extras/four-eyes/AGENTS.snippet.md': '848cff9a111c33db8717f6bf9673a391c632d85a2d39cdbe8f6dc64eb73cb6da'}

MIT_NORMALIZED_DIGEST = '4e434e113bd4315d757584d4e9e2e87d16c28edf4f98a20e5a44147a9a86b9e5'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def split_frontmatter(data):
    """Keep byte boundaries, including final newlines, for source comparison."""
    lines = data.splitlines(keepends=True)
    if not lines or lines[0].rstrip(b"\r\n") != b"---":
        raise AssertionError("SKILL.md must begin with ---")
    end = next((i for i in range(1, len(lines))
                if lines[i].rstrip(b"\r\n") == b"---"), None)
    if end is None:
        raise AssertionError("Missing closing frontmatter delimiter")
    return lines[:end + 1], b"".join(lines[end + 1:])


def without_metadata(data):
    """Strip only the frontmatter metadata field and its indented children."""
    header, body = split_frontmatter(data)
    kept = []
    dropping = False
    for line in header:
        if re.match(rb"metadata\s*:", line):
            dropping = True
            continue
        if dropping and (not line.strip() or line[:1].isspace()):
            continue
        dropping = False
        kept.append(line)
    return b"".join(kept) + body


def scalar(value):
    value = value.strip()
    if value.startswith('"'):
        try:
            return json.loads(value)
        except ValueError as error:
            raise AssertionError("Unsupported quoted YAML scalar") from error
    if value.startswith("'"):
        if not value.endswith("'"):
            raise AssertionError("Unclosed YAML quote")
        return value[1:-1].replace("''", "'")
    if not value or value[0] in "&*![]{}":
        raise AssertionError("Expected a plain or quoted YAML scalar")
    return re.split(r"\s+#", value, maxsplit=1)[0]


def frontmatter(data):
    """Parse the small YAML interface, not keys found elsewhere in the body.

    Accept plain/quoted scalars, folded/literal blocks, indented continuation,
    and block or flow metadata. Reject duplicate keys and unsupported syntax.
    This deliberately is not a general YAML loader.
    """
    header, _ = split_frontmatter(data)
    fields = {}
    key = None
    for raw in header[1:-1]:
        line = raw.decode("utf-8").rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z][\w-]*):\s*(.*)", line)
        if match:
            key, value = match.groups()
            if key in fields:
                raise AssertionError("Duplicate frontmatter key: " + key)
            fields[key] = [value]
        elif key and line[:1].isspace():
            fields[key].append(line)
        else:
            raise AssertionError("Unsupported frontmatter line: " + line)
    result = {}
    for key, parts in fields.items():
        first, *rest = parts
        if key == "metadata":
            if first.startswith("{") and first.endswith("}") and not rest:
                # Split commas outside quotes (the specified values are strings).
                entries = re.split(r",(?=(?:[^\"']|\"[^\"]*\"|'[^']*')*$)", first[1:-1])
            elif not first:
                entries = rest
            else:
                raise AssertionError("metadata must be a mapping")
            metadata = {}
            for entry in entries:
                match = re.fullmatch(r"\s*([\w-]+):\s*(.+)", entry)
                if not match or match[1] in metadata:
                    raise AssertionError("Invalid or duplicate metadata field")
                metadata[match[1]] = scalar(match[2])
            result[key] = metadata
        elif first in (">", ">-", ">+", "|", "|-", "|+"):
            result[key] = ("\n" if first.startswith("|") else " ").join(
                line.strip() for line in rest)
        else:
            result[key] = scalar(" ".join([first] + [line.strip() for line in rest]))
    return result


def prose(text):
    return " ".join(re.sub(r"[*`_]", "", text).replace("’", "'").lower().split())


def sections(text):
    matches = list(re.finditer(r"(?m)^(#{1,6})\s+(.+)$", text))
    return [(m[2], text[m.end():next((n.start() for n in matches[i + 1:]
                                    if len(n[1]) <= len(m[1])), len(text))])
            for i, m in enumerate(matches)]


def tables(text):
    lines = text.splitlines()
    for i in range(1, len(lines)):
        separator = [s.strip() for s in lines[i].strip().strip("|").split("|")]
        if len(separator) < 2 or not all(re.fullmatch(r":?-{3,}:?", s) for s in separator):
            continue
        header = [s.strip() for s in lines[i - 1].strip().strip("|").split("|")]
        rows = []
        for line in lines[i + 1:]:
            if "|" not in line or not line.strip():
                break
            rows.append([s.strip() for s in line.strip().strip("|").split("|")])
        yield header, rows


def markdown_destinations(text):
    # Inline links and reference-style definitions; anchors are checked as files.
    pattern = r"\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)"
    for match in re.finditer(pattern, text):
        yield match[1].strip("<>")
    for match in re.finditer(r"(?m)^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", text):
        yield match[1].strip("<>")


def publication_violations(data):
    """Return categories only, without echoing private matches into test logs."""
    violations = []
    for label, token in (
        ("session marker", b"Claude" + b"-Session"),
        ("absolute macOS user path", b"/" + b"Users/"),
        ("worktree path", b"work" + b"trees/"),
    ):
        if token in data:
            violations.append(label)
    if re.search(re.escape(b"/" + b"home/") + rb"[^/\s]+/", data):
        violations.append("absolute Linux user path")
    email = rb"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)"
    # Escaped newlines in source string literals are separators, not the local
    # part of an email before a Markdown import such as @AGENTS.md.
    email_text = re.sub(rb"\\[nrt]", b" ", data)
    for match in re.finditer(email, email_text):
        address = match[0].lower()
        domain = match[1].lower()
        if domain == b"users.noreply.github.com":
            continue
        if address == b"noreply" + b"@" + b"github.com":
            continue
        violations.append("non-GitHub-noreply email address")
        break
    return violations


class CatalogContracts(unittest.TestCase):
    def read_bytes(self, relative):
        path = ROOT / relative
        self.assertTrue(path.is_file(), "Missing file: " + relative)
        self.assertTrue(path.resolve().is_relative_to(ROOT), "File escapes repository: " + relative)
        return path.read_bytes()

    def read(self, relative):
        return self.read_bytes(relative).decode("utf-8")

    def catalog(self):
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise AssertionError("Duplicate JSON key: " + key)
                result[key] = value
            return result
        return json.loads(self.read(".claude-plugin/marketplace.json"), object_pairs_hook=unique_object)

    def require_patterns(self, text, patterns):
        for label, pattern in patterns.items():
            with self.subTest(requirement=label):
                self.assertRegex(prose(text), pattern, label)

    def section(self, text, pattern):
        found = [body for title, body in sections(text) if re.search(pattern, prose(title))]
        self.assertTrue(found, "Missing section: " + pattern)
        return "\n".join(found)

    def test_required_layout(self):
        """Exercising new behaviour: a flat, independently installable catalog."""
        required = set(SOURCE_DIGESTS) | set(EXTRA_DIGESTS) | {
            ".claude-plugin/marketplace.json", "README.md", "LICENSE", "AGENTS.md",
            "CLAUDE.md", "tests/test_catalog.py", "tests/test_review_assistant.py",
        } | {"skills/" + name + "/README.md" for name in VERSIONS}
        for relative in sorted(required):
            with self.subTest(path=relative):
                self.read_bytes(relative)
        with self.subTest(flat_tests=True):
            self.assertFalse((ROOT / "tests/__init__.py").exists())
            self.assertFalse(any(p.is_dir() and p.name != "__pycache__"
                                 for p in (ROOT / "tests").iterdir()))

    def test_marketplace_identity(self):
        """Exercising new behaviour: marketplace identity and owner interface."""
        catalog = self.catalog()
        self.assertEqual(catalog.get("name"), "dev-knacks")
        self.assertEqual(catalog.get("owner"), {"name": "Ivan Avramov"})
        self.assertIsInstance(catalog.get("description"), str)
        self.assertTrue(catalog["description"].strip())

    def test_catalog_and_skill_folders_both_directions(self):
        """Reproducing a failure: a valid-looking entry points at missing files."""
        plugins = self.catalog().get("plugins")
        self.assertIsInstance(plugins, list)
        names = [plugin.get("name") for plugin in plugins]
        self.assertEqual(names, list(VERSIONS), "Order, duplicates, omissions, or extra entries")
        directory = ROOT / "skills"
        self.assertTrue(directory.is_dir(), "Missing skills directory")
        self.assertEqual({p.name for p in directory.iterdir() if p.is_dir()}, set(names))
        for plugin in plugins:
            with self.subTest(plugin=plugin["name"]):
                expected = "./skills/" + plugin["name"]
                self.assertEqual(plugin.get("skills"), [expected])
                self.assertTrue((ROOT / expected / "SKILL.md").is_file())
                self.assertTrue((ROOT / expected).resolve().is_relative_to(directory.resolve()))

    def test_plugin_entry_fields(self):
        """Exercising new behaviour: one plugin loads exactly its own skill."""
        for entry in self.catalog()["plugins"]:
            with self.subTest(plugin=entry.get("name")):
                self.assertIn(entry.get("name"), VERSIONS)
                self.assertEqual(entry.get("source"), "./")
                self.assertIs(entry.get("strict"), False)
                self.assertEqual(entry.get("skills"), ["./skills/" + entry["name"]])
                self.assertIsInstance(entry.get("description"), str)
                self.assertTrue(entry["description"].strip())
                self.assertEqual(len(entry["description"].splitlines()), 1)

    def test_pinned_versions(self):
        """Preserving an invariant: each existing skill keeps its release version."""
        actual = {entry["name"]: entry.get("version") for entry in self.catalog()["plugins"]}
        self.assertEqual(actual, VERSIONS)

    def test_dependency_is_declared_and_resolves(self):
        """Exercising new behaviour: four-eyes installs review-panel with it."""
        entries = {entry["name"]: entry for entry in self.catalog()["plugins"]}
        self.assertIn("four-eyes", entries)
        self.assertEqual(entries["four-eyes"].get("dependencies"), ["review-panel"])
        for name, entry in entries.items():
            dependencies = entry.get("dependencies", [])
            with self.subTest(plugin=name):
                self.assertIsInstance(dependencies, list)
                if name != "four-eyes":
                    self.assertEqual(dependencies, [])
                for dependency in dependencies:
                    self.assertIn(dependency, entries)
                    self.assertNotEqual(dependency, name)

    def test_frontmatter_interface(self):
        """Exercising new behaviour: each folder exposes the portable YAML contract."""
        for name, version in VERSIONS.items():
            with self.subTest(skill=name):
                fm = frontmatter(self.read_bytes("skills/" + name + "/SKILL.md"))
                self.assertEqual(set(fm), {"name", "description", "metadata"})
                self.assertEqual(fm["name"], name)
                self.assertIsInstance(fm["description"], str)
                self.assertTrue(fm["description"].strip())
                self.assertIsInstance(fm["metadata"], dict)
                self.assertEqual(fm["metadata"].get("source"), SOURCE_URL)
                self.assertEqual(fm["metadata"].get("version"), version)

    def test_frontmatter_versions_match_entries(self):
        """Exercising new behaviour: install and skill versions cannot drift apart."""
        for entry in self.catalog()["plugins"]:
            with self.subTest(skill=entry["name"]):
                fm = frontmatter(self.read_bytes("skills/" + entry["name"] + "/SKILL.md"))
                self.assertEqual(fm["metadata"]["version"], entry["version"])

    def test_source_content_is_preserved(self):
        """Preserving an invariant: only metadata and eligible cross-references change."""
        for relative, expected in SOURCE_DIGESTS.items():
            with self.subTest(path=relative):
                data = self.read_bytes(relative)
                if relative.endswith("/SKILL.md"):
                    data = without_metadata(data)
                if sha256(data) == expected:
                    continue
                lines = data.splitlines(keepends=True)
                # Only source lines that actually named an old repo/install path
                # may differ. A dev-knacks mention alone is not a blanket waiver.
                for index, old in CROSS_REFERENCE_LINES.get(relative, {}).items():
                    self.assertLess(index, len(lines), "Cross-reference line removed")
                    old = old.encode("utf-8")
                    if lines[index] != old:
                        self.assertIn(b"dev-knacks", lines[index], "Changed reference must name dev-knacks")
                        lines[index] = old
                self.assertEqual(sha256(b"".join(lines)), expected,
                                 "Source changed outside metadata or an eligible cross-reference")

    def test_skill_bodies_match_source_digests(self):
        """Preserving an invariant: metadata conversion does not rewrite behaviour."""
        for relative, expected in BODY_DIGESTS.items():
            with self.subTest(path=relative):
                _, body = split_frontmatter(self.read_bytes(relative))
                # These source bodies contain no old repo/install cross-references.
                self.assertEqual(sha256(body), expected)

    def test_support_file_inventory(self):
        """Preserving an invariant: all support files ship once with their skill."""
        for name in VERSIONS:
            with self.subTest(skill=name):
                folder = ROOT / "skills" / name
                actual = {p.relative_to(ROOT).as_posix() for p in folder.rglob("*") if p.is_file()}
                expected = {p for p in SOURCE_DIGESTS if p.startswith("skills/" + name + "/")}
                expected.add("skills/" + name + "/README.md")
                self.assertEqual(actual, expected)

    def test_extras_equal_sources(self):
        """Preserving an invariant: installation snippets are copied byte for byte."""
        for relative, expected in EXTRA_DIGESTS.items():
            with self.subTest(path=relative):
                self.assertEqual(sha256(self.read_bytes(relative)), expected)

    def test_markdown_references_resolve(self):
        """Preserving an invariant: packaged Markdown references remain usable."""
        contextual = {
            "skills/review-assistant/SKILL.md": {"review-tree.md"},
            "skills/four-eyes/SKILL.md": {"CLAUDE.md", "AGENTS.md"},
            "skills/review-panel/runtimes.md": {"CLAUDE.md", "AGENTS.md", "~/.codex/AGENTS.md"},
        }
        count = 0
        for name in VERSIONS:
            folder = ROOT / "skills" / name
            self.assertTrue(folder.is_dir(), "Missing skill folder: " + name)
            for path in folder.rglob("*"):
                if not path.is_file() or path.suffix not in {".md", ".toml"}:
                    continue
                relative = path.relative_to(ROOT).as_posix()
                text = self.read(relative)
                targets = list(markdown_destinations(text))
                if path.name != "README.md":
                    text = re.sub(r"https?://\S+", "", text)
                    text = re.sub(r"\[[^\]\n]*\]\([^)]*\)", "", text)
                    targets += re.findall(r"(?<![\w/])(?:~/|\.{1,2}/)*(?:[\w.-]+/)*[\w-]+\.md\b", text)
                for target in targets:
                    parsed = urlsplit(target)
                    if parsed.scheme or parsed.netloc or not parsed.path.endswith(".md"):
                        continue
                    target = unquote(parsed.path)
                    if target in contextual.get(relative, set()):
                        continue
                    if relative == "skills/four-eyes/briefs.md" and target == "runtimes.md":
                        self.read_bytes("skills/review-panel/runtimes.md")
                        continue
                    count += 1
                    with self.subTest(source=relative, target=target):
                        resolved = (path.parent / target).resolve()
                        boundary = ROOT if path.name == "README.md" else folder.resolve()
                        self.assertTrue(resolved.is_relative_to(boundary), "Reference escapes allowed folder")
                        self.assertTrue(resolved.is_file(), "Unresolved reference: " + target)
        self.assertGreaterEqual(count, 6, "Expected at least the six review-assistant routes")

    def test_root_readme_catalog(self):
        """Exercising new behaviour: humans can find purpose, version and requirements."""
        text = self.read("README.md")
        self.require_patterns(text, {"identity": r"dev-knacks", "purpose": r"marketplace|catalog|collection",
                                     "skills": r"skills?"})
        candidates = [(header, rows) for header, rows in tables(text)
                      if all(any(re.search(term, prose(cell)) for cell in header)
                             for term in (r"skill", r"purpose|description", r"version", r"requires|requirements|dependencies"))]
        self.assertEqual(len(candidates), 1, "Expected one catalog table")
        header, rows = candidates[0]
        columns = [next(i for i, cell in enumerate(header) if re.search(term, prose(cell)))
                   for term in (r"skill", r"purpose|description", r"version", r"requires|requirements|dependencies")]
        seen = []
        for row in rows:
            self.assertEqual(len(row), len(header))
            skill, purpose, version, requires = [row[i] for i in columns]
            matches = [name for name in VERSIONS if re.search(r"(?<![\w-])" + name + r"(?![\w-])", skill)]
            self.assertEqual(len(matches), 1, "Unrecognized catalog row: " + skill)
            name = matches[0]
            seen.append(name)
            self.assertTrue(prose(purpose))
            self.assertEqual(version.strip("` *"), VERSIONS[name])
            if name == "four-eyes":
                self.assertIn("review-panel", requires)
            if name == "vnote":
                self.assertRegex(prose(requires), r"basic memory")
        self.assertCountEqual(seen, VERSIONS)

    def test_root_readme_claude_install(self):
        """Exercising new behaviour: marketplace installation and invocation are documented."""
        text = self.read("README.md")
        self.assertIn("/plugin marketplace add ivan-avramov/dev-knacks", text)
        self.assertRegex(text, r"/plugin install (?:<skill>|review-assistant|four-eyes|review-panel|vnote)@dev-knacks")
        self.assertRegex(text, r"/(<skill>|review-assistant|four-eyes|review-panel|vnote):\1")
        self.require_patterns(text, {"agent": r"claude code",
            "automatic dependency": r"four-eyes.{0,180}(?:automatic\w*.{0,100}review-panel|review-panel.{0,100}automatic\w*)"})

    def test_root_readme_codex_cursor_install(self):
        """Exercising new behaviour: Codex and Cursor can select individual skills."""
        text = self.read("README.md")
        self.assertRegex(text, r"npx skills add ivan-avramov/dev-knacks --skill (?:<skill>|review-assistant|four-eyes|review-panel|vnote)")
        for agent in ("codex", "cursor"):
            with self.subTest(agent=agent):
                self.assertIn(agent, prose(text))
                self.assertRegex(text, r"-a\s+" + agent + r"\b")

    def test_root_readme_manual_copy(self):
        """Preserving an invariant: named skill folders still work by manual copy."""
        text = self.read("README.md")
        for value in ("~/.agents/skills/", "~/.cursor/skills/", "~/.claude/skills/"):
            with self.subTest(destination=value):
                self.assertIn(value, text)
        self.assertRegex(text, r"skills/(?:<skill>|review-assistant|four-eyes|review-panel|vnote)/")
        self.assertRegex(text, r"/(?:<skill>|review-assistant|four-eyes|review-panel|vnote)(?![\w:-])")
        self.require_patterns(text, {"copy": r"cop(?:y|ying)",
            "keep folder name": r"(?:keep|preserv|retain|unchanged).{0,60}(?:folder|directory).{0,30}name|(?:folder|directory).{0,30}name.{0,60}(?:keep|preserv|retain|unchanged|match)"})

    def test_root_readme_layout_check_and_license(self):
        """Exercising new behaviour: repository navigation and local checks are documented."""
        text = self.read("README.md")
        self.assertIn(CHECK_COMMAND, text)
        for value in ("skills/", "extras/four-eyes/", "tests/", ".claude-plugin/", "AGENTS.md", "CLAUDE.md"):
            with self.subTest(path=value):
                self.assertIn(value, text)
        self.assertRegex(prose(text), r"\bmit\b")
        self.assertIn("LICENSE", text)

    def test_per_skill_readmes_link_root_install(self):
        """Exercising new behaviour: each independently installed skill has human guidance."""
        for name in VERSIONS:
            with self.subTest(skill=name):
                relative = "skills/" + name + "/README.md"
                text = self.read(relative)
                self.assertIn(name, text)
                install = self.section(text, r"install|setup|set up")
                links = [urlsplit(link) for link in markdown_destinations(install)]
                self.assertTrue(any(link.scheme == "https" and link.netloc == "github.com"
                                    and link.path.rstrip("/") in {
                                        "/ivan-avramov/dev-knacks",
                                        "/ivan-avramov/dev-knacks/blob/main/README.md",
                                    }
                                    and not link.query
                                    for link in links), "Installation must link to the root README")

    def test_vnote_readme_requirements(self):
        """Exercising new behaviour: vnote declares its server and vault assumptions."""
        text = self.read("skills/vnote/README.md")
        self.require_patterns(text, {"server": r"basic memory.{0,60}mcp|mcp.{0,60}basic memory",
            "requirement": r"requir|need|depend", "purpose": r"note|vault",
            "schema": r"frontmatter|schema", "provenance": r"provenance|source", "relations": r"relation"})
        self.assertIn("Sources/<slug>/", text)

    def test_review_assistant_readme_rationale_and_walk(self):
        """Preserving an invariant: review-assistant keeps its rationale and walkthrough."""
        text = self.read("skills/review-assistant/README.md")
        rationale = self.section(text, r"why|rationale")
        walk = self.section(text, r"what.*review.*looks like|walkthrough|walk.through|review.*flow")
        self.require_patterns(rationale, {"problem map": r"problem map", "altitude": r"altitude|pass",
            "evidence": r"evidence|quote", "reviewer steering": r"reviewer|steer",
            "tree": r"tree", "record": r"record|origin", "safety": r"confidential|access control|inject"})
        self.require_patterns(walk, {"setup": r"type|checklist", "problem pass": r"pass 0",
            "structure pass": r"pass 1", "detail pass": r"pass 2", "verdict": r"verdict|holds",
            "record": r"tree|record", "output": r"writeup|write.up|report"})

    def test_four_eyes_readme_snippets_and_history(self):
        """Preserving an invariant: four-eyes retains setup snippets and locates history."""
        text = self.read("skills/four-eyes/README.md")
        for value in ("extras/four-eyes/", "CLAUDE.snippet.md", "AGENTS.snippet.md",
                      "~/.claude/CLAUDE.md", "~/.codex/AGENTS.md", "review-panel"):
            with self.subTest(detail=value):
                self.assertIn(value, text)
        self.assertRegex(prose(text), r"append|add|paste")
        history = self.section(text, r"history|earlier")
        self.assertIn("ivan-avramov/four-eyes", history)
        self.assertRegex(prose(history), r"archiv")

    def test_review_panel_readme_behavior_and_history(self):
        """Preserving an invariant: panel usage and prior history remain discoverable."""
        text = self.read("skills/review-panel/README.md")
        for value in ("opinion", "verify", "research", "panel.example.toml", "~/.config/review-panel/panel.toml"):
            with self.subTest(detail=value):
                self.assertIn(value, text)
        self.assertRegex(prose(text), r"driver|judg")
        if "ivan-avramov/review-panel" in text:
            self.assertRegex(prose(text), r"archiv")

    def test_agents_catalog_rules(self):
        """Exercising new behaviour: maintenance rules preserve catalog consistency."""
        text = self.read("AGENTS.md")
        self.assertIn(CHECK_COMMAND, text)
        for value in ("skills/", ".claude-plugin/", "tests/", "extras/", "README.md"):
            with self.subTest(layout=value):
                self.assertIn(value, text)
        self.require_patterns(text, {
            "identity": r"dev-knacks", "catalog purpose": r"marketplace|catalog|collection",
            "one folder": r"(?:one|each).{0,70}(?:folder|directory).{0,70}skill|skill.{0,70}(?:one|own).{0,30}(?:folder|directory)",
            "name relationship": r"(?:folder|directory).{0,130}frontmatter.{0,130}(?:entry|plugin)|frontmatter.{0,130}(?:folder|directory).{0,130}(?:entry|plugin)",
            "version relationship": r"(?:entry|plugin).{0,80}version.{0,80}metadata\.version|metadata\.version.{0,80}(?:entry|plugin).{0,80}version",
            "bump together": r"bump.{0,100}(?:both|together).{0,100}(?:any|every|change)|(?:any|every).{0,80}change.{0,100}bump.{0,100}(?:both|together)",
            "terse agent files": r"(?:agent.facing|skill\.md).{0,100}(?:terse|concise|directive)",
            "rationale location": r"rationale.{0,100}readme\.md",
            "generic tools": r"(?:no|never|do not|must not|don't).{0,80}agent.specific tool|agent.specific tool.{0,80}(?:forbid|prohibit)",
            "no specs or records": r"(?:no|never|do not|don't).{0,80}spec.{0,100}run record.{0,100}session link",
        })

    def test_agents_review_assistant_cross_file_contracts(self):
        """Preserving an invariant: routing, shared terms and reference links stay synchronized."""
        text = self.read("AGENTS.md")
        self.require_patterns(text, {
            "routing": r"routing table.{0,100}reference|reference.{0,100}routing table",
            "shared vocabulary": r"shared vocabulary.{0,100}skill\.md",
            "grading owner": r"grading.{0,160}product-vendor\.md|product-vendor\.md.{0,160}grading",
            "renumbering": r"(?:renumber|section.number|section.{0,40}cross.reference).{0,160}(?:update|keep)|update.{0,160}(?:renumber|section|cross.reference)",
            "operational owner": r"operational probes.{0,160}(?:§9|section 9)|(?:§9|section 9).{0,160}operational probes",
        })
        # These are the four named source->target edges, checked in either
        # direction within one rule, rather than requiring an arrow spelling.
        rules = [prose(s) for s in re.split(r"\n\s*\n|\n(?=\s*[-*] )", text)]
        for source, target in (("patent-portfolio.md", "product-vendor.md"),
                               ("repo-code.md", "design-doc.md"),
                               ("product-vendor.md", "repo-code.md"),
                               ("product-vendor.md", "patent-portfolio.md")):
            with self.subTest(source=source, target=target):
                self.assertTrue(any(source in rule and target in rule for rule in rules), "Missing cross-link rule")
        for filename in ("design-doc.md", "patent-disclosure.md"):
            with self.subTest(operational_pointer=filename):
                self.assertTrue(any(filename in rule and ("§9" in rule or "section 9" in rule)
                                    for rule in rules), "Missing operational-probe pointer rule")

    def test_claude_exact_import(self):
        """Preserving an invariant: the init header imports the single agent guide."""
        self.assertEqual(self.read_bytes("CLAUDE.md").rstrip(b"\n"), CLAUDE_TEXT.encode().rstrip(b"\n"))

    def test_f1_snippets_are_separately_fetched_repository_extras(self):
        """Reproducing a failure (F1): installed readers can fetch both external snippets."""
        text = self.read("skills/four-eyes/README.md")
        links = set(markdown_destinations(text))
        missing = []
        for filename in ("CLAUDE.snippet.md", "AGENTS.snippet.md"):
            expected = SOURCE_URL + "/blob/main/extras/four-eyes/" + filename
            if expected not in links:
                missing.append("absolute repository link to " + filename)
        normalized = prose(self.section(text, r"install|setup|snippet|extras"))
        requirements = {
            "snippets identified as repository extras": r"\brepo(?:sitory)?\b.{0,100}\bextras\b|\bextras\b.{0,100}\brepo(?:sitory)?\b",
            "separate retrieval": r"(?:fetch|download|retriev|obtain|copy).{0,100}separat|separat.{0,100}(?:fetch|download|retriev|obtain|copy)",
            "extras excluded from the installed skill folder": r"(?:not|aren't|isn't|outside|excluded|absent).{0,120}(?:install|skill folder|skill directory)|(?:install|skill folder|skill directory).{0,120}(?:not includ|not contain|not ship|doesn't|does not|without|exclude)",
        }
        missing += [label for label, pattern in requirements.items() if not re.search(pattern, normalized)]
        if missing:
            self.fail("F1 missing: " + "; ".join(missing))

    def test_f2_agent_tool_rule_exempts_runtime_recipes(self):
        """Reproducing a failure (F2): portable instructions do not forbid required CLI recipes."""
        text = prose(self.read("AGENTS.md"))
        requirements = {
            "tool prohibition scoped to skill instructions": r"(?:skill instructions?|skill prose|instructions?.{0,60}skill\.md).{0,150}(?:no|never|avoid|must not|don't|do not).{0,80}(?:agent.specific|tool)|(?:no|never|avoid|must not|don't|do not).{0,80}agent.specific.{0,150}(?:skill instructions?|skill prose|instructions?.{0,60}skill\.md)",
            "review-panel runtime guide named": r"(?:skills/review-panel/)?runtimes\.md",
            "four-eyes helper recipes named": r"(?:skills/four-eyes/)?briefs\.md",
            "runtime/dispatch exception": r"(?:runtime|dispatch|cli).{0,150}(?:recipe|exception|except)|(?:exception|except|recipe).{0,150}(?:runtime|dispatch|cli)",
            "recipes may name CLI tools and flags": r"(?:may|allow|use|name|keep|retain|preserve).{0,160}(?:cli|runtime).{0,120}(?:flags?.{0,80}tools?|tools?.{0,80}flags?)|(?:cli|runtime).{0,120}(?:flags?.{0,80}tools?|tools?.{0,80}flags?).{0,100}(?:allow|permit|exception)",
        }
        missing = [label for label, pattern in requirements.items() if not re.search(pattern, text)]
        if missing:
            self.fail("F2 missing: " + "; ".join(missing))

    def test_f3_agents_document_release_pins_and_new_skill_steps(self):
        """Reproducing a failure (F3): maintainers can update all pins and add a skill coherently."""
        raw = self.read("AGENTS.md")
        text = prose(raw)
        missing = ["test pin " + token for token in (
            "VERSIONS", "SOURCE_DIGESTS", "BODY_DIGESTS", "test_catalog.py", "test_review_assistant.py"
        ) if token not in raw]
        requirements = {
            "SHA-256 body and support-file pins": r"sha.?256.{0,180}(?:bod(?:y|ies)|skill).{0,120}support|(?:bod(?:y|ies)|skill).{0,120}support.{0,180}sha.?256",
            "review-assistant version and word ceilings": r"(?=.{0,300}testreviewassistant\.py)(?=.{0,300}\bversion)(?=.{0,300}(?:word|size).{0,40}(?:ceiling|limit|baseline))",
            "intentional changes update pins in the version-bump commit": r"(?=.{0,400}(?:updat|refresh|regenerat))(?=.{0,400}(?:same commit|commit together))(?=.{0,400}(?:version|bump))",
            "marketplace version location": r"(?:marketplace|entry|plugin).{0,80}version|version.{0,80}(?:marketplace|entry|plugin)",
            "frontmatter version location": r"metadata\.version",
            "root catalog row version location": r"(?:root|readme\.md).{0,100}catalog.{0,100}(?:row|version)",
            "skill README heading version location": r"readme.{0,100}(?:heading|title)|(?:heading|title).{0,100}readme",
            "skill body version location": r"skill\.md.{0,100}(?:body|report)|(?:body|report).{0,100}skill\.md",
        }
        missing += [label for label, pattern in requirements.items() if not re.search(pattern, text)]
        # Accept a heading, paragraph or list introducing the add-skill steps.
        start = re.search(r"(?:add(?:ing)?|new|introduc\w*)\s+(?:(?:a|another)\s+)?skill", text)
        steps = text[start.start():start.start() + 1800] if start else ""
        for label, pattern in {
            "skill folder": r"folder|directory|skills/",
            "frontmatter": r"frontmatter|metadata\.version",
            "marketplace entry": r"marketplace|plugin entry",
            "README catalog row": r"catalog.{0,80}row|row.{0,80}catalog",
            "per-skill README": r"(?:skill|folder).{0,100}readme|readme.{0,100}(?:skill|folder)",
            "test constants": r"test.{0,100}(?:constant|pin|digest|versions)|(?:constant|pin|digest|versions).{0,100}test",
        }.items():
            if not re.search(pattern, steps):
                missing.append("add-skill step: " + label)
        if missing:
            self.fail("F3 missing: " + "; ".join(missing))

    def test_f4_npx_project_default_and_global_option(self):
        """Reproducing a failure (F4): users can distinguish project and user-wide installs."""
        text = self.read("README.md")
        normalized = prose(text)
        commands = re.findall(r"npx\s+skills\s+add\s+ivan-avramov/dev-knacks[^\n`]*", text.replace("\\\n", " "))
        missing = []
        if not any("--skill" in command and not re.search(r"(?:^|\s)(?:-g|--global)(?:\s|$)", command)
                   for command in commands):
            missing.append("project-form npx skills add command")
        if not re.search(r"default.{0,130}(?:current|project)|(?:current|project).{0,130}default", normalized):
            missing.append("current-project default explained")
        if not re.search(r"(?<!\w)-g\b.{0,150}(?:user.wide|global|all projects)|(?:user.wide|global|all projects).{0,150}(?<!\w)-g\b", normalized):
            missing.append("-g documented for user-wide installation")
        if missing:
            self.fail("F4 missing: " + "; ".join(missing))

    def test_f5_four_eyes_snippet_names_plugin_skill(self):
        """Reproducing a failure (F5): the unchanged snippet is mapped to plugin skill names."""
        text = prose(self.read("skills/four-eyes/README.md"))
        missing = ["plugin skill name " + name for name in (
            "four-eyes:four-eyes", "review-panel:review-panel"
        ) if name not in text]
        if not re.search(r"claude code.{0,100}plugin|plugin.{0,100}claude code", text):
            missing.append("Claude Code plugin context")
        if not re.search(r"snippet.{0,200}(?:refer|mean|name|target|identif)|(?:refer|mean|name|target|identif).{0,200}snippet", text):
            missing.append("snippet's four-eyes reference explained")
        if missing:
            self.fail("F5 missing: " + "; ".join(missing))

    def test_f6_install_compatibility_symlink_and_precedence_pointer(self):
        """Reproducing a failure (F6): retained install options and precedence have usable guidance."""
        text = self.read("README.md")
        normalized = prose(text)
        missing = []
        cursor_contexts = [prose(paragraph) for paragraph in re.split(r"\n\s*\n", text)
                           if "cursor" in prose(paragraph) and "|" not in paragraph]
        cursor_contexts += [prose(" ".join(row)) for _, rows in tables(text) for row in rows
                            if "cursor" in prose(" ".join(row))]
        for directory in (".claude/skills", ".codex/skills"):
            if not any(directory in context for context in cursor_contexts):
                missing.append("Cursor also reads " + directory)
        skill = r"(?P<skill><skill>|review-assistant|four-eyes|review-panel|vnote)"
        link = re.search(r"ln\s+-s\s+[\"']?\$PWD/skills/" + skill
                         + r"[\"']?\s+~/.agents/skills/(?P=skill)/?", text)
        if not link:
            missing.append("symlink example from the repository's skill folder")
        elif not re.search(r"mkdir\s+-p\s+~/.agents/skills/?", text[:link.start()]):
            missing.append("mkdir -p precedes the symlink example")
        if not re.search(r"(?:symlink|symbolic|link).{0,250}git pull|git pull.{0,250}(?:symlink|symbolic|link)", normalized):
            missing.append("symlink tracks git pull explained")
        # Shared install details may live in the root guide instead of being
        # duplicated in all four READMEs, provided installed readers can reach it.
        for name in VERSIONS:
            readme = self.read("skills/" + name + "/README.md")
            install = self.section(readme, r"install|setup|set up")
            links = [urlsplit(url) for url in markdown_destinations(install)]
            if not any(url.scheme == "https" and url.netloc == "github.com"
                       and url.path.rstrip("/") in {
                           "/ivan-avramov/dev-knacks", "/ivan-avramov/dev-knacks/blob/main/README.md"
                       } for url in links):
                missing.append(name + " installation points to the shared root guide")
        panel = self.read("skills/review-panel/README.md")
        precedence = [paragraph for paragraph in re.split(r"\n\s*\n", panel)
                      if re.search(r"both levels|precedence|prefer|resolv", prose(paragraph))]
        linked = False
        for paragraph in precedence:
            for url in map(urlsplit, markdown_destinations(paragraph)):
                if (url.scheme == "https" and url.netloc == "github.com"
                        and url.path.rstrip("/") in {
                            "/ivan-avramov/dev-knacks", "/ivan-avramov/dev-knacks/blob/main/README.md"
                        }
                        and (url.fragment in {"install", "manual-copy"} or "table" in prose(paragraph))):
                    linked = True
        if not linked:
            missing.append("review-panel precedence paragraph links the root install table")
        if missing:
            self.fail("F6 missing: " + "; ".join(missing))

    def test_standard_mit_license(self):
        """Preserving an invariant: standard MIT terms, author and 2026 copyright."""
        actual = " ".join(self.read("LICENSE").split()).encode()
        self.assertEqual(sha256(actual), MIT_NORMALIZED_DIGEST)

    def test_no_docs_directory(self):
        """Exercising new behaviour: the catalog excludes old proposals and run records."""
        for path in ROOT.rglob("*"):
            if ".git" not in path.relative_to(ROOT).parts:
                with self.subTest(path=path.relative_to(ROOT).as_posix()):
                    self.assertNotEqual(path.name, "docs", "No docs directory or file in the catalog")

    def test_no_session_links_or_absolute_user_paths(self):
        """Exercising new behaviour: all publication files exclude private paths and emails."""
        files = []
        for directory, directories, names in os.walk(ROOT):
            directories[:] = [name for name in directories if name not in {".git", "__pycache__"}]
            files.extend(Path(directory) / name for name in names
                         if (Path(directory) / name).is_file())
        self.assertTrue(files, "No publication files were scanned")
        for path in sorted(files):
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(path=relative):
                violations = publication_violations(self.read_bytes(relative))
                self.assertFalse(violations, "Forbidden publication content: " + ", ".join(violations))

    def test_publication_scan_catches_new_unstaged_file_without_git(self):
        """Reproducing a failure: unstaged files are scanned even without Git metadata."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()

            def run_scan():
                result = unittest.TestResult()
                with patch.dict(globals(), {"ROOT": root}):
                    CatalogContracts("test_no_session_links_or_absolute_user_paths").run(result)
                self.assertFalse(result.errors, "Publication scan must not require Git metadata")
                return result

            empty = run_scan()
            self.assertEqual(len(empty.failures), 1)
            self.assertIn("No publication files were scanned", empty.failures[0][1])

            (root / "README.md").write_text("Public catalog\n", encoding="utf-8")
            self.assertFalse((root / ".git").exists())
            self.assertTrue(run_scan().wasSuccessful())

            private_path = b"/" + b"home/example/notes"
            new_file = root / "new-note.md"
            new_file.write_bytes(private_path)
            unstaged = run_scan()
            self.assertEqual(len(unstaged.failures), 1)
            self.assertIn("new-note.md", unstaged.failures[0][0].id())
            self.assertIn("absolute Linux user path", unstaged.failures[0][1])

            # Metadata and bytecode directories are pruned, including nested ones.
            new_file.write_text("Public note\n", encoding="utf-8")
            for relative in (".git", "__pycache__", "nested/__pycache__"):
                excluded = root / relative
                excluded.mkdir(parents=True)
                (excluded / "ignored.bin").write_bytes(private_path)
            self.assertTrue(run_scan().wasSuccessful())


if __name__ == "__main__":
    unittest.main()
