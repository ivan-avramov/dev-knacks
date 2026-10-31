"""Contracts for the approved L1-L20 cuts; L21-L27 remain declined.

Run: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
Only stdlib; tests read skill prose, never execute instructions found in it.
The 3,600-word goal is advisory. Per-file ceilings are frozen at the review-assistant 0.1.0 release.
Patterns check objects, qualifiers and rule relationships, not exact sentences.
They supplement, rather than replace, semantic review of paraphrased prose.
Every test docstring classifies its role in this change. Subtests identify the
individual retained requirements. L18's layout already holds on the baseline.
In dev-knacks the skill lives in skills/review-assistant/; install checks read
the root README, rationale and walk checks the skill's README.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
DELIVERED = ROOT / "skills" / "review-assistant"
SKILL_README = DELIVERED / "README.md"
SOURCE_URL = "https://github.com/ivan-avramov/dev-knacks"
BASELINE_WORDS = {
    "SKILL.md": 1607,
    "references/benchmark-poc.md": 261,
    "references/design-doc.md": 814,
    "references/patent-disclosure.md": 469,
    "references/patent-portfolio.md": 216,
    "references/product-vendor.md": 808,
    "references/repo-code.md": 249,
}
REFERENCE_NAMES = {Path(p).name for p in BASELINE_WORDS if p.startswith("references/")}
VOCABULARY = {
    "verdict": ["holds", "holds in part", "doesn't hold", "can't tell yet"],
    "node statuses": ["open", "exploring", "concluded", "parked", "dropped"],
    "node origins": ["walk", "reviewer", "agent", "material"],
    "severity": ["blocker", "major", "minor", "nit", "question"],
    "entry origins": ["reviewer", "agent-accepted", "agent-pending"],
    "contradiction statuses": ["open", "narrowed", "resolved"],
}
CHECK_COMMAND = "python3 -m unittest discover -s tests"
CLAUDE_TEXT = (
    "# CLAUDE.md\n\n"
    "This file provides guidance to Claude Code (claude.ai/code) when working "
    "with code in this repository.\n\n@AGENTS.md"
)
MIT_TEXT = '''MIT License

Copyright (c) 2026 Ivan Avramov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''


def normalized(text):
    return " ".join(text.replace("’", "'").split())


def prose(text):
    return normalized(re.sub(r"[*`_]", "", text)).lower()


def has_terms(text, terms):
    return all(re.search(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", prose(text))
               for term in terms)


def scalar(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].replace("''", "'")
    return value


def frontmatter(text):
    """Parse the specified small YAML interface; fail closed on extra keys.

    Supports plain/quoted scalars, folded/literal description blocks, indented
    plain continuations, and block/flow metadata. This is not a general YAML
    parser: aliases, tags, and multiline quoted scalars need manual review.
    """
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError("SKILL.md must start with a YAML --- delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise AssertionError("Missing closing YAML --- delimiter") from None
    fields = {}
    key = None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z][\w-]*):\s*(.*)", line)
        if match:
            key, value = match.groups()
            if key in fields:
                raise AssertionError("Duplicate frontmatter key: " + key)
            fields[key] = [value]
        elif key and line[0].isspace():
            fields[key].append(line)
        else:
            raise AssertionError("Unsupported YAML line: " + line)
    result = {}
    for key, parts in fields.items():
        first, *rest = parts
        if key == "metadata":
            raw = normalized(" ".join(parts)).strip("{} ")
            # A URL scheme ("https://") is part of a value, not a key.
            entries = re.split(r",\s*|\s+(?=[\w-]+\s*:(?!//))", raw)
            metadata = {}
            for entry in entries:
                match = re.fullmatch(r"([\w-]+)\s*:\s*(.+)", entry)
                if not match or match[1] in metadata:
                    raise AssertionError("Invalid or duplicate metadata: " + raw)
                metadata[match[1]] = scalar(match[2])
            result[key] = metadata
        elif first in (">", ">-", ">+", "|", "|-", "|+"):
            separator = "\n" if first.startswith("|") else " "
            result[key] = separator.join(line.strip() for line in rest)
            if not first.endswith("-"):
                result[key] += "\n"
        else:
            result[key] = scalar(" ".join([first] + [x.strip() for x in rest]))
    return result, "\n".join(lines[end + 1:])


def headings(text):
    """ATX Markdown headings outside fenced code, with offsets into the text."""
    result = []
    offset = 0
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = None
        elif fence is None:
            match = re.match(r" {0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
            if match:
                result.append((len(match[1]), match[2], offset, offset + len(line)))
        offset += len(line)
    return result


def sections(text):
    hs = headings(text)
    return [(title, text[end:next((s for l, _, s, _ in hs[i + 1:] if l <= level), len(text))])
            for i, (level, title, _, end) in enumerate(hs)]


def table_rows(text):
    """Return cells only from Markdown tables with a separator row."""
    lines = text.splitlines()
    result = []
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        if i == 0 or "|" not in lines[i - 1]:
            continue
        for row in lines[i + 1:]:
            if "|" not in row or not row.strip():
                break
            result.append([c.strip() for c in row.strip().strip("|").split("|")])
    return result


class SkillContracts(unittest.TestCase):
    def read(self, path):
        self.assertTrue(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
        return path.read_text(encoding="utf-8")

    @property
    def skill_dir(self):
        return DELIVERED

    def skill(self):
        return self.read(self.skill_dir / "SKILL.md")

    def skill_files(self):
        return [self.skill_dir / "SKILL.md"] + sorted((self.skill_dir / "references").glob("*.md"))

    def require_patterns(self, text, patterns):
        for label, pattern in patterns.items():
            with self.subTest(requirement=label):
                self.assertRegex(prose(text), pattern, label)

    def section_text(self, text, topic):
        matches = [body for title, body in sections(text) if re.search(topic, prose(title))]
        self.assertTrue(matches, f"Missing section matching {topic}")
        return prose(" ".join(matches))

    def reference_section(self, filename, topic):
        return self.section_text(self.read(self.skill_dir / "references" / filename), topic)

    def require_rule(self, text, *alternatives):
        self.assertTrue(any(re.search(pattern, prose(text)) for pattern in alternatives),
                        "Missing rule; accepted patterns: " + " OR ".join(alternatives))

    def test_layout(self):
        """Preserving an invariant: the skill sits in skills/ beside the release files."""
        for name in ("LICENSE", "README.md", "AGENTS.md", "CLAUDE.md", "tests/test_review_assistant.py",
                     "skills/review-assistant/SKILL.md", "skills/review-assistant/README.md"):
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).is_file(), name)
        with self.subTest(path="skills/review-assistant/references"):
            self.assertEqual({p.name for p in (DELIVERED / "references").glob("*")}, REFERENCE_NAMES)
        for name in ("SKILL.md", "references", "review-assistant"):
            with self.subTest(removed=name):
                self.assertFalse((ROOT / name).exists(), "No copy outside skills/: " + name)

    def test_mit_license(self):
        """Preserving an invariant: standard MIT grant, holder, and year."""
        self.assertEqual(normalized(self.read(ROOT / "LICENSE")), normalized(MIT_TEXT))

    def test_frontmatter_schema(self):
        """Preserving an invariant: exact metadata interface and version."""
        fm, _ = frontmatter(self.skill())
        self.assertEqual(set(fm), {"name", "description", "metadata"})
        self.assertEqual(fm["metadata"], {"source": SOURCE_URL, "version": "0.1.0"})

    def test_frontmatter_name_and_folder(self):
        """Preserving an invariant: Cursor-compatible name and install folder."""
        fm, _ = frontmatter(self.skill())
        self.assertEqual(fm.get("name"), "review-assistant")
        self.assertRegex(fm["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertEqual(self.skill_dir.name, fm["name"])

    def test_description_scope(self):
        """Preserving an invariant: description advertises all review types."""
        fm, _ = frontmatter(self.skill())
        desc = fm.get("description", "")
        self.assertGreater(len(desc), 0)
        self.assertLessEqual(len(desc), 1024)
        self.require_patterns(desc, {
            "design docs": r"design doc", "specs": r"\bspec", "RFCs": r"\brfcs?\b",
            "architecture proposals": r"architecture proposals?", "disclosures": r"patent disclosures?",
            "portfolios": r"portfolios?", "products": r"products?", "companies": r"compan(?:y|ies)",
            "vendors": r"vendors?", "repositories": r"\brepo(?:s|sitories|sitory)?\b",
            "benchmarks": r"benchmarks?", "POCs": r"\bpocs?\b",
        })

    def test_description_triggers_and_exclusions(self):
        """Preserving an invariant: explicit and implicit triggers, exclusions."""
        desc = frontmatter(self.skill())[0].get("description", "")
        self.require_patterns(desc, {
            "let's review": r"let's review", "help review/evaluate/assess": r"help me.*review.*evaluate.*assess",
            "walk-through": r"walk me through.*doc.*patent.*product", "what's real": r"what's real here",
            "implicit material trigger": r"(?:bring|material|examine).*without.*nam",
            "unattended exclusion": r"(?:not for|exclud|don't use|do not use).*unattended.*review-panel",
            "PR exclusion": r"(?:not for|exclud|don't use|do not use).*line.by.line pr",
        })

    def test_routing_table_bijection(self):
        """Preserving an invariant: section 1 routes each reference exactly once."""
        section = next((body for title, body in sections(self.skill()) if re.match(r"1\.\s", title)), None)
        self.assertIsNotNone(section, "Missing numbered route/setup section")
        rows = table_rows(section)
        routes = []
        material_patterns = {
            "design-doc.md": r"design|spec|rfc|architecture",
            "product-vendor.md": r"product|company|vendor",
            "patent-disclosure.md": r"disclosure|invention|filing",
            "patent-portfolio.md": r"patent|portfolio",
            "repo-code.md": r"repo|codebase|source",
            "benchmark-poc.md": r"benchmark|poc|bake.off",
        }
        for row in rows:
            links = re.findall(r"references/([\w-]+\.md)", " ".join(row))
            if links:
                self.assertTrue(prose(row[0]), "Routing row needs a material type")
                for link in links:
                    with self.subTest(route=link):
                        self.assertIn(link, material_patterns)
                        self.assertRegex(prose(row[0]), material_patterns[link])
                routes.extend(links)
        self.assertEqual(set(routes), REFERENCE_NAMES)
        self.assertEqual(len(routes), len(set(routes)), "Duplicate routing entries")
        self.assertEqual(set(routes), {p.name for p in (self.skill_dir / "references").glob("*.md")})

    def test_markdown_file_references_resolve(self):
        """Preserving an invariant: local skill and sibling Markdown links resolve."""
        count = 0
        for path in self.skill_files():
            text = self.read(path)
            # Include bare filenames, code spans and link destinations. Runtime
            # review-tree.md is an output, explicitly created by the protocol.
            for match in re.finditer(r"(?<![\w/])(?:\.{1,2}/)*(?:[\w-]+/)*[\w-]+\.md\b", text):
                target = match[0]
                if target == "review-tree.md":
                    continue
                if re.search(r"https?://\S*$", text[:match.start()]):
                    continue
                count += 1
                with self.subTest(source=path.name, target=target):
                    self.assertTrue((path.parent / target).is_file(), f"Unresolved {path.name}: {target}")
        self.assertGreaterEqual(count, 6, "Expected the six routing references")

    def test_numbered_sections_and_cross_references(self):
        """Preserving an invariant: all ten protocol sections and reference targets."""
        body = frontmatter(self.skill())[1]
        numbered = [int(m[1]) for level, title, _, _ in headings(body)
                    if level == 2 and (m := re.match(r"(\d+)\.\s+\S", title))]
        self.assertEqual(numbered, list(range(1, 11)))
        titles = {int(m[1]): prose(title) for level, title, _, _ in headings(body)
                  if level == 2 and (m := re.match(r"(\d+)\.\s+\S", title))}
        # Decimal anchors such as §7.9 are examples of source-material anchors,
        # not references to this skill. Expand integer ranges such as §2–3.
        pattern = r"(?:\bsections?\s+|§\s*)(\d+)(?![\d.]\d)(?:\s*[–-]\s*(\d+))?"
        for match in re.finditer(pattern, body, re.I):
            first = int(match[1])
            last = int(match[2] or first)
            with self.subTest(reference=match[0]):
                self.assertLessEqual(first, last)
                for number in range(first, last + 1):
                    self.assertIn(number, numbered)
                # Classify the nearest named subject preceding a pointer in its
                # paragraph, then check both destination number and heading topic.
                # Decimal source anchors are excluded by the reference regex.
                context = prose(body[max(body.rfind("\n\n", 0, match.start()), 0):match.start()])
                subjects = list(re.finditer(
                    r"tree|breadcrumb|also consider|evaluat\w*|anchor\w*|record", context))
                self.assertTrue(subjects, f"Unclassified reference context: {context}")
                subject = subjects[-1][0]
                if subject in ("tree", "breadcrumb"):
                    allowed, topic = {6}, r"tree|exploration"
                elif subject == "also consider" or subject.startswith("evaluat"):
                    allowed, topic = {5}, r"evaluat|reviewer.*points|adding"
                else:
                    allowed, topic = {4, 7}, r"record|turn|anchor"
                self.assertIn(first, allowed, f"{subject} points to unrelated section {first}")
                self.assertRegex(titles[first], topic)

    def test_design_problem_solution_coverage(self):
        """Preserving an invariant: cover each mapped problem, beyond goals/components."""
        text = self.reference_section("design-doc.md", r"pass 1")
        self.require_rule(text,
                          r"each problem.{0,80}(?:address|solv|solution)",
                          r"(?:map|trace|link).{0,30}(?:every|all) problem.{0,80}(?:solution|component|address)")

    def test_design_duplicate_tools_hedged(self):
        """Preserving an invariant: duplicate tools suggest rather than prove prototypes."""
        text = self.reference_section("design-doc.md", r"pass 1")
        self.require_rule(text,
                          r"tools.{0,90}(?:usually|may|might|can|could|often|suggest).{0,50}(?:merged|assembled) prototypes",
                          r"(?:merged|assembled) prototypes.{0,60}(?:possible|likely|suspect).{0,60}tools")

    def test_patent_independent_descriptions_sought(self):
        """Preserving an invariant: actively seek independent mechanism descriptions."""
        text = self.reference_section("patent-portfolio.md", r"across.*portfolio")
        self.require_rule(text,
                          r"(?:check for|seek|find|search for|look for).{0,30}independent descriptions?.{0,50}mechanism",
                          r"independent descriptions?.{0,50}mechanism.{0,40}(?:seek|search|check)")

    def test_vendor_mature_product_evidence(self):
        """Preserving an invariant: unpitched mature product tests shipping/support ability."""
        text = self.reference_section("product-vendor.md", r"context")
        self.require_rule(text,
                          r"mature product.{0,65}(?:absent|missing|not|outside).{0,25}(?:deck|pitch).{0,100}ship.{0,25}support",
                          r"(?:deck|pitch).{0,50}mature product.{0,100}(?:ship|deliver).{0,30}support")

    def test_design_goal_completion_criterion(self):
        """Preserving an invariant: each goal needs a way to establish completion."""
        text = self.reference_section("design-doc.md", r"pass 0")
        self.require_rule(text,
                          r"each goal.{0,100}(?:way|test|criterion|measure).{0,45}(?:met|achiev|complet|success)",
                          r"(?:success|completion|acceptance) (?:test|criteria|criterion).{0,40}(?:each|every) goal")

    def test_design_credential_inventory(self):
        """Preserving an invariant (L8): credential inventory may be a noun probe."""
        text = self.reference_section("design-doc.md", r"probes")
        self.require_rule(text,
                          r"which credentials exist|credential inventory",
                          r"(?:list|enumerate|inventory|identify).{0,30}(?:all |existing )?credentials",
                          r"credentials?.{0,20}(?:which exist|inventory|existing)")

    def test_benchmark_baseline_identity(self):
        """Preserving an invariant (L8): baseline identity may be a noun probe."""
        text = self.reference_section("benchmark-poc.md", r"pass 1")
        self.require_rule(text,
                          r"baseline.{0,25}(?:what is it|identify|name|describe|establish)",
                          r"(?:identify|name|describe|establish).{0,25}(?:the )?baseline",
                          r"baseline.{0,25}(?:identity|what it is)")

    def test_thread_pulling_priority(self):
        """Preserving an invariant: questions and thread-pulling precede advancement."""
        text = self.section_text(self.skill(), r"^4\.")
        self.require_rule(text,
                          r"questions.{0,30}thread[- ]pulling.{0,30}(?:first|priority|precede)",
                          r"(?:prioriti[sz]e|first).{0,30}questions.{0,30}(?:threads|thread[- ]pulling)")

    def test_summary_trust_without_source(self):
        """Preserving an invariant: summaries must stand without reopening the source."""
        text = self.section_text(self.skill(), r"^4\.")
        self.require_rule(text,
                          r"trust.{0,25}(?:summary|summaries)?.{0,30}without (?:opening|reading|consulting|reopening).{0,20}source",
                          r"(?:summary|summaries).{0,60}(?:self[- ]contained|stand alone)")

    def test_agreement_main_failure(self):
        """Preserving an invariant: false agreement remains the primary failure mode."""
        text = self.section_text(self.skill(), r"^5\.")
        self.require_rule(text,
                          r"agree\w*.{0,40}(?:doesn't hold|does not hold|unsupported|invalid).{0,30}(?:main|primary|principal) failure",
                          r"(?:main|primary|principal) failure.{0,80}(?:false agreement|agree\w*.*(?:unsupported|invalid|doesn't hold))")

    def test_writeup_strengths_heading(self):
        """Preserving an invariant (L10): keep strengths heading; drop its hint."""
        self.assertRegex(self.section_text(self.skill(), r"^8\."), r"what is strong")

    def test_description_whenever(self):
        """Preserving an invariant: description preserves the whenever trigger scope."""
        text = frontmatter(self.skill())[0]["description"]
        self.require_rule(text, r"\bwhenever\b", r"\bevery time\b", r"\bany time\b")

    def test_section_number_anchor_example(self):
        """Preserving an invariant: anchor formats include a concrete section number."""
        text = self.section_text(self.skill(), r"^(?:4|7)\.")
        self.require_rule(text,
                          r"(?:§\d+(?:\.\d+)*\s*:|§\d+(?:\.\d+)+|section \d+(?:\.\d+)*\s*:)"
                          r".{0,100}(?:p\.\s*\d+|page \d+|slide|claim)")

    def test_guidance_reordering(self):
        """Preserving an invariant: maintain section references after reordering too."""
        text = self.read(ROOT / "AGENTS.md")
        self.require_rule(text, r"renumber\w*.{0,30}reorder\w*.{0,80}updat",
                          r"updat.{0,80}renumber\w*.{0,30}reorder\w*")

    def test_readme_symlink_parent_directory(self):
        """Preserving an invariant: the documented copy or symlink works with no skills directory."""
        text = self.section_text(self.read(ROOT / "README.md"), r"install|setup|set up")
        # Require directory creation earlier in the example, for the same
        # destination parent. No shell execution is needed for this contract.
        self.require_rule(text,
                          r"mkdir\s+-p\s+(?P<parent>[^\s`;&]+).{0,100}(?:ln\s+-s|cp\s+-r)\s+\S+\s+(?P=parent)/review-assistant")

    def test_known_rationale_removed(self):
        """Preserving an invariant: move known explanations out of agent-facing skill files."""
        phrases = ("inverts the conclusion", "reward plausible answers",
                   "undermines even a defensive filing", "enable inline comments",
                   "per-suite tune is a different system", "beats one on defects")
        for path in self.skill_files():
            text = prose(self.read(path))
            for phrase in phrases:
                with self.subTest(file=path.name, explanation=phrase):
                    self.assertFalse(phrase in text, f"Move explanation to README: {phrase}")

    def test_r1_benchmark_tiering_without_winner_exception(self):
        """Preserving an invariant: tier results without a winner-selection exception."""
        texts = {"benchmark": self.reference_section("benchmark-poc.md", r"pass 1"),
                 "README": prose(self.read(SKILL_README))}
        for source, text in texts.items():
            self.require_rule(text, r"(?:group|report|present).{0,35}tiers",
                              r"tiers.{0,25}(?:instead of|rather than|over) winners")
            self.require_rule(text, r"rather than (?:declar|select|choos)\w*.{0,15}winner",
                              r"(?:don't|do not|never|no) (?:(?:declare|declaring|select|choose) )?(?:a )?winner",
                              r"tiers.{0,25}(?:instead of|rather than|over) winners")
            # Reject conditional tiering as well as conditional permission to
            # choose a winner. Mere mention of a detectable difference is legal.
            exceptions = (
                r"tiers.{0,35}(?:unless|except|only if)",
                r"(?:winner.{0,55}(?:unless|except|only if|otherwise))",
                r"(?:if|when|once|unless).{0,80}(?:exceed|threshold|significan).{0,70}winner",
                r"\b(?:may|can)\s+(?:declare|select|choose).{0,15}winner",
            )
            self.assertFalse(any(re.search(p, text) for p in exceptions),
                             f"{source}: winner-selection or conditional-tiering exception")

    def test_r2_design_security_and_current_correctness(self):
        """Preserving an invariant: retain trust reasons, identity modes, and current truth."""
        text = self.reference_section("design-doc.md", r"probes")
        checks = {
            "trust and why": (r"component.{0,35}trust.{0,30}(?:why|reason|justif)",
                              r"(?:reason|justif).{0,40}(?:component|trust)"),
            "signed and delegated identity": (r"carried.{0,30}signed.{0,25}delegated.{0,25}asserted",
                                              r"(?:signed|delegated).{0,30}(?:signed|delegated).{0,50}asserted"),
            "claims true today": (r"claims about other systems.{0,40}(?:true today|currently true|current accuracy)",
                                   r"(?:verify|check).{0,50}(?:current|today).{0,40}(?:claims|other systems)"),
        }
        for label, patterns in checks.items():
            self.require_rule(text, *patterns)

    def test_r3_design_anchor_fields_and_redraw_label(self):
        """Preserving an invariant: preserve design anchor fields and redraw provenance."""
        record = self.reference_section("design-doc.md", r"record notes")
        reading = self.reference_section("design-doc.md", r"reading")
        self.require_rule(record, r"(?:section number|section id|numbered section).{0,30}title.{0,25}page",
                          r"page.{0,35}(?:section number|section id).{0,25}title")
        self.require_rule(reading, r"redraw.{0,35}label\w*.{0,25}redraw",
                          r"(?:label|mark|identify).{0,35}redraw.{0,25}(?:as|a) redraw")

    def test_r4_reference_links_and_guidance_claims(self):
        """Preserving an invariant: restore reference links and truthful explicit guidance."""
        expected = {
            ("product-vendor.md", "repo-code.md"),
            ("product-vendor.md", "patent-portfolio.md"),
            ("repo-code.md", "design-doc.md"),
        }
        for source, target in sorted(expected):
            path = self.skill_dir / "references" / source
            topic = r"sources" if source == "product-vendor.md" else r"cross.check"
            text = self.reference_section(source, topic)
            self.assertIn(target, text, f"Missing reference link: {source} -> {target}")
            self.assertTrue((path.parent / target).is_file(), f"Unresolved link: {target}")
            if target == "design-doc.md":
                self.require_rule(text, r"design-doc\.md.{0,35}correctness",
                                  r"correctness.{0,35}design-doc\.md")
        text = self.read(ROOT / "AGENTS.md")
        # Accept arrow lists, colon lists, and prose "links to" declarations.
        # A source can name several destinations before the next source marker.
        claims = set()
        for block in re.split(r"\n\s*\n|\n(?=\s*[-*]\s)", text):
            block = prose(block)
            markers = list(re.finditer(
                r"([\w-]+\.md)\s*(?:→|->|:|(?:cross-)?links? to)", block))
            for i, marker in enumerate(markers):
                source = marker[1]
                if source not in REFERENCE_NAMES:
                    continue
                end = markers[i + 1].start() if i + 1 < len(markers) else len(block)
                for target in re.findall(r"[\w-]+\.md\b", block[marker.end():end]):
                    claims.add((source, target))
        self.assertTrue(expected <= claims,
                        f"Guidance omits explicit cross-links: {sorted(expected - claims)}")
        for source, target in sorted(claims):
            source_path = self.skill_dir / "references" / source
            self.assertIn(target, self.read(source_path), "Guidance claims a nonexistent link")
            self.assertTrue((source_path.parent / target).is_file(), "Guidance target does not resolve")

    def test_r5_also_consider_relevance_without_source_quota(self):
        """Preserving an invariant: select relevant sources without a one-per-source quota."""
        text = self.section_text(self.skill(), r"^5\.")
        self.require_rule(text, r"whichever sources.{0,45}(?:bear|relevan)",
                          r"(?:choose|select|draw|use).{0,50}sources.{0,50}(?:relevan|bear)")
        self.require_rule(text, r"(?:rather than|not|never|avoid|don't|do not).{0,20}one (?:from|per).{0,15}(?:each|source)",
                          r"(?:no|without|avoid).{0,25}(?:source quota|quota per source)")
        text = prose(self.read(SKILL_README))
        self.assertFalse(re.search(r"varied sources.{0,35}one-note", text),
                         "README still advocates source variety as the selection rule")
        self.require_rule(text, r"sources?.{0,55}(?:relevan|bear on|matter|applicab)",
                          r"relevan.{0,55}sources?",
                          r"(?:decision impact|materiality).{0,50}(?:over|rather than|not).{0,20}(?:variety|coverage|quota)")

    def test_r6_vendor_wording_example_and_contradiction_rank(self):
        """Preserving an invariant: separate wording, mark examples, and rank contradictions."""
        text = self.reference_section("product-vendor.md", r"claims and findings")
        self.require_rule(text, r"(?:keep|separate|distinguish).{0,35}internal.{0,45}external",
                          r"internal.{0,35}external.{0,35}(?:separate|distinct)")
        if "fake" in text or "unsubstantiated" in text:
            self.require_rule(text, r"(?:e\.g\.|for example|such as|\().{0,70}(?:fake|unsubstantiated)")
        text = prose(self.read(self.skill_dir / "references/product-vendor.md"))
        self.require_rule(text, r"(?:contradict\w*|inconsisten\w*).{0,180}(?:strongest|highest[- ]value|most compelling|most important)",
                          r"(?:prioriti[sz]e|rank|treat).{0,80}(?:contradict\w*|inconsisten\w*).{0,100}(?:strong|high|top)")

    def round2_probe_items(self, filename, topic):
        text = self.read(self.skill_dir / "references" / filename)
        bodies = [body for title, body in sections(text) if re.search(topic, prose(title))]
        self.assertTrue(bodies, f"Missing probe section: {filename}: {topic}")
        # L8 permits noun lists under a shared imperative lead. Carry that lead
        # into each item's actionability check; content is checked separately.
        items = []
        for body in bodies:
            parts = re.split(r"(?m)^\s*[-*]\s+", body)
            lead = prose(parts[0])
            shared = lead + " " if re.search(r"\b(?:probe|check|assess|inspect|verify):", lead) else ""
            items.extend(shared + prose(item) for item in parts[1:])
        return items

    def round2_require_probe(self, item):
        # Questions may follow a bold label. Imperatives may begin the item or
        # follow its label; accept several equivalent review verbs.
        imperative = (r"(?:^|[.:;]\s+)(?:probe|check|ask|verify|assess|determine|establish|confirm|"
                      r"evaluate|map|list|name|identify|inspect|ensure|consider|test|look|"
                      r"flag|trace|compare|examine|find|offer|see)\b")
        self.assertTrue("?" in item or re.search(imperative, item),
                        f"Probe is stated as a fact, not a question or instruction: {item}")

    def test_r7_design_pass_probes_are_actionable(self):
        """Preserving an invariant: L5/L8 retain actionable surviving pass-zero/one probes."""
        for item in self.round2_probe_items("design-doc.md", r"^pass [01]\b"):
            self.round2_require_probe(item)

    def test_r7_vendor_charter_fit_is_a_probe(self):
        """Preserving an invariant: assess charter fit instead of asserting that it holds."""
        items = [s for s in self.round2_probe_items("product-vendor.md", r"pass 0") if "charter" in s]
        self.assertTrue(items, "Missing charter-fit probe")
        for item in items:
            # The separate preference about scope-based arguments must not mask
            # a factual assertion in the charter-fit clause itself.
            self.round2_require_probe(re.split(r"\bprefer\b", item, maxsplit=1)[0])

    def test_r7_benchmark_configuration_is_a_probe(self):
        """Preserving an invariant: L8 allows an imperative lead; configuration stays frozen across suites."""
        items = [s for s in self.round2_probe_items("benchmark-poc.md", r"^pass 1\b")
                 if re.search(r"configuration|system under test", s) and "suites" in s]
        self.assertTrue(items, "Missing system-configuration probe")
        for item in items:
            self.round2_require_probe(re.split(r"\btreat\b", item, maxsplit=1)[0])
            self.require_rule(item, r"(?:frozen|fixed|constant|unchanged).{0,30}(?:across|between).{0,20}suites")

    def test_r7_patent_problem_reality_is_a_probe(self):
        """Preserving an invariant: assess problem reality/significance separately from cited pain."""
        text = self.reference_section("patent-disclosure.md", r"pass 0")
        self.require_rule(text, r"(?:is|whether|assess|check|evaluate|determine).{0,35}(?:the )?problem.{0,35}(?:real|genuine).{0,25}significant",
                          r"(?:assess|check|evaluate).{0,50}(?:reality|significance).{0,30}problem")
        self.require_rule(text, r"(?:name|identify|state).{0,35}pain.{0,40}authors.{0,20}cite")
        self.require_rule(text, r"whether.{0,25}disclosure.{0,25}(?:shows|demonstrates|supports)")

    def test_r7_description_even_without_skill_name(self):
        """Preserving an invariant: make unnamed-skill triggering explicitly inclusive."""
        text = frontmatter(self.skill())[0]["description"]
        self.require_rule(text, r"even without nam\w*.{0,20}skill",
                          r"whether or not.{0,25}(?:skill.{0,15}named|nam\w*.{0,15}skill)")

    def test_r8_additional_rationale_removed_and_probes_retained(self):
        """Preserving an invariant (L7/L15): relocated blast radius and terse patent status."""
        # L7 moves bulk blast radius to section 9; L15 permits a terse status
        # field. Keep both meanings, and the earlier rationale removals.
        cases = {
            "design-doc.md": (r"often the (?:review's )?real agenda", r"blast radius (?:is )?invisible"),
            "patent-portfolio.md": (r"[\"']?patented[\"']? in marketing often means pending",),
            "patent-disclosure.md": (r"may add scope.{0,40}unexamined risk",),
        }
        for filename, explanations in cases.items():
            text = prose(self.read(self.skill_dir / "references" / filename))
            for pattern in explanations:
                self.assertFalse(re.search(pattern, text), f"Move explanation to README: {pattern}")
        design = prose(self.read(self.skill_dir / "references/design-doc.md"))
        self.require_rule(design, r"open decisions.{0,60}(?:seed|start|plan).{0,20}walk",
                          r"(?:seed|start|plan).{0,25}walk.{0,40}open decisions")
        self.require_rule(design + " " + self.section_text(self.skill(), r"^9\."), r"(?:assess|check|evaluate|examine).{0,35}(?:bulk|aggregate).{0,20}blast radius",
                          r"(?:bulk|aggregate) blast radius.{0,20}(?:assess|check|evaluat)",
                          r"(?:probe|check).{0,500}bulk blast radius")
        portfolio = self.reference_section("patent-portfolio.md", r"per patent")
        self.require_rule(portfolio, r"(?:separate|distinguish).{0,30}issued.{0,35}pending",
                          r"issued (?:vs\.?|versus).{0,15}pending")
        self.require_rule(portfolio, r"(?:treat|check|verify|consider).{0,50}(?:marketing|patented).{0,70}(?:possibly|may|could|potentially).{0,25}pending",
                          r"(?:check|verify).{0,60}(?:patented|marketing).{0,50}(?:actually|still) pending",
                          r"marketing.{0,20}patented.{0,30}possibly pending")
        disclosure = self.reference_section("patent-disclosure.md", r"inventive step")
        self.require_rule(disclosure, r"(?:assess|check|evaluate|examine).{0,60}(?:variant|embodiment).{0,40}scope.{0,25}risk",
                          r"(?:variant|embodiment).{0,40}(?:assess|evaluate|check).{0,25}scope.{0,25}risk")

    def test_shared_vocabulary(self):
        """Preserving an invariant: complete named vocabulary in the protocol."""
        text = prose(frontmatter(self.skill())[1])
        # Require each vocabulary family together in a section, so unrelated
        # incidental mentions scattered across the document do not suffice.
        bodies = [prose(title + " " + body) for title, body in sections(self.skill())]
        for family, terms in VOCABULARY.items():
            with self.subTest(family=family):
                self.assertTrue(any(has_terms(b, terms) for b in bodies), family)
        for prefix in "PQTFC":
            with self.subTest(id_sequence=prefix):
                self.assertRegex(frontmatter(self.skill())[1], rf"\b{prefix}\d+\b")
        for tag in (r"\[doc\s+§x\s*/\s*p\.y\]", r"\[inferred:\s*from\s+(?:\.\.\.|…)\]",
                    r"\[knowledge\]", r"\[web:\s*source\]"):
            with self.subTest(basis_tag=tag):
                self.assertRegex(text, tag)

    def test_definition_ownership(self):
        """Preserving an invariant: references consume shared definitions, not copies."""
        grade_sets = [
            ["independent", "co-marketing", "vendor-sourced", "logo only"],
            ["observed", "vendor-doc", "vendor-claim", "independent"],
            [f"m{i}" for i in range(6)],
        ]
        for path in self.skill_files():
            text = self.read(path)
            # Full enumerations in a paragraph/list block are observable copies;
            # isolated uses of a term remain legal. Paraphrased redefinitions
            # and whether an enumeration is explanatory require manual review.
            blocks = re.split(r"\n\s*\n", text)
            if path.name != "SKILL.md":
                for family, terms in VOCABULARY.items():
                    with self.subTest(path=path.name, vocabulary=family):
                        self.assertFalse(any(has_terms(block, terms) for block in blocks),
                                         "Shared vocabulary enumeration belongs in SKILL.md")
            if path.name != "product-vendor.md":
                for terms in grade_sets:
                    with self.subTest(path=path.name, scale=terms):
                        self.assertFalse(any(has_terms(block, terms) for block in blocks),
                                         "Grading scale belongs in product-vendor.md")

    def test_grading_scales(self):
        """Preserving an invariant: product/vendor owns all three grading scales."""
        path = self.skill_dir / "references/product-vendor.md"
        grading = [body for title, body in sections(self.read(path)) if re.search(r"\bgrading\b", title, re.I)]
        self.assertEqual(len(grading), 1, "One Grading section must define the scales")
        text = prose(grading[0])
        for grade in ("independent", "co-marketing", "vendor-sourced", "logo only",
                      "observed", "vendor-doc", "vendor-claim"):
            with self.subTest(grade=grade):
                self.assertRegex(text, r"\b" + re.escape(grade) + r"\b")
        for level, meaning in {0: r"assert|claim", 1: r"announc", 2: r"demo", 3: r"young|beta|six|6",
                               4: r"shipping", 5: r"proven|corroborat"}.items():
            with self.subTest(maturity=level):
                self.assertRegex(text, rf"\bm{level}\b(?:(?!\bm[0-5]\b).){{0,160}}(?:{meaning})")
        portfolio = self.read(self.skill_dir / "references/patent-portfolio.md")
        self.assertIn("product-vendor.md", portfolio)

    def test_portable_capabilities(self):
        """Preserving an invariant: replace host-specific tool and skill calls."""
        for path in self.skill_files():
            text = self.read(path)
            for pattern in (r"\b(?:TodoWrite|AskUserQuestion|Task)\b", r"\bpdf-reading\b",
                            r"(?<![\w:/])/[a-z][\w-]*(?![\w/-])\b"):
                with self.subTest(path=path.name, forbidden=pattern):
                    match = re.search(pattern, text)
                    self.assertIsNone(match, f"{path.name}: nonportable token {match[0] if match else ''}")

    def test_claude_import(self):
        """Preserving an invariant: exact /init header and canonical guidance import."""
        self.assertTrue(self.read(ROOT / "CLAUDE.md") in (CLAUDE_TEXT, CLAUDE_TEXT + "\n"),
                        "CLAUDE.md must contain only the /init header, blank line, and @AGENTS.md")

    def test_agents_guidance(self):
        """Preserving an invariant: portable canonical development contracts."""
        text = self.read(ROOT / "AGENTS.md")
        self.assertIn(CHECK_COMMAND, text)
        self.assertIn("review-assistant/SKILL.md", text)
        self.assertIn("review-assistant/references/", text)
        self.require_patterns(text, {
            "interactive protocol": r"interactive|reviewer.driven", "on-demand references": r"on.demand|as needed",
            "description trigger": r"description.*trigger|trigger.*description",
            "automated exclusion": r"review-panel", "PR exclusion": r"line.by.line pr",
            "routing contract": r"routing|route", "bijection": r"vice versa|both ways|bijection|exactly|every.*each",
            "shared definitions": r"(?:vocabulary|definitions).*once|never redefine",
            "grading owner": r"product-vendor\.md", "cross-reference maintenance": r"renumber|reorder|section.*refer|cross.reference",
            "directive style": r"terse.*directive|directive.*terse",
            "human rationale": r"rationale.*readme\.md|readme\.md.*rationale",
            "reference passes": r"pass", "reference context": r"context", "record notes": r"record",
        })
        for name in ("P", "Q", "T", "F", "C"):
            with self.subTest(sequence=name):
                self.assertRegex(text, rf"\b{name}(?:\d+)?\b")
        for term in ("basis", "verdict", "status", "origin", "severit"):
            with self.subTest(contract=term):
                self.assertIn(term, prose(text))

    def test_readme_sections_and_walk(self):
        """Preserving an invariant: skill README has overview, rationale, walk, install."""
        text = self.read(SKILL_README)
        parts = sections(text)
        self.assertGreaterEqual(len(parts), 4, "Use Markdown sections for the requested human guide")
        titles = " ".join(prose(title) for title, _ in parts)
        self.require_patterns(titles, {
            "overview": r"what|overview|about|review assistant|review-assistant",
            "rationale": r"why|rationale", "walk": r"review|walk|workflow",
            "install": r"install|setup|set up",
        })
        self.assertRegex(text, r"(?m)^\s*1[.)]\s+\S")
        self.assertRegex(text, r"(?m)^\s*2[.)]\s+\S")
        self.assertIn("review-assistant", text)

    def test_root_readme_layout_check_and_license(self):
        """Preserving an invariant: root README has install, layout, check command, license."""
        text = self.read(ROOT / "README.md")
        titles = " ".join(prose(title) for title, _ in sections(text))
        self.require_patterns(titles, {
            "install": r"install|setup|set up", "layout": r"layout|repository|structure",
            "license": r"licen[cs]e",
        })
        self.assertIn(CHECK_COMMAND, text)
        self.assertIn("skills/review-assistant/", text)
        self.assertRegex(text, r"\bMIT\b")
        self.assertRegex(text, r"\[[^\]]+\]\((?:\./)?LICENSE(?:\s+\"[^\"]*\")?\)")

    def test_readme_rationale_topics(self):
        """Preserving an invariant: explanations moved to the human guide."""
        text = self.read(SKILL_README)
        self.require_patterns(text, {
            "problem map first": r"pass 0|problem map", "one piece per turn": r"one.*(?:piece|turn)|piece.*turn",
            "evaluate rather than record": r"evaluat", "basis tags": r"basis|provenance",
            "genuine positives": r"positive|strength|strong", "detailed material": r"detail|appendi|known.issues",
        })

    def test_readme_installation_matrix(self):
        """Preserving an invariant: install and invoke on all three hosts."""
        text = self.read(ROOT / "README.md")
        # Paths may be in headings/paragraphs, tables, or shell examples; require
        # each host's documented scope in its own section or table row.
        contexts = [title + " " + body for title, body in sections(text) if not re.search(r"\binstall\b", title, re.I)]
        contexts += [" ".join(row) for row in table_rows(text)]
        # The catalog README documents every skill, so invocations may use the
        # <skill> placeholder instead of the review-assistant name.
        hosts = {
            "Claude Code": (".claude", "/<skill>"),
            "Codex": (".agents", "$<skill>"),
            "Cursor": (".cursor", "/<skill>"),
        }
        for host, (directory, invocation) in hosts.items():
            with self.subTest(agent=host):
                allowed = [directory] if host != "Cursor" else [".cursor", ".agents", ".claude", ".codex"]
                matching = [c for c in contexts if host.lower() in prose(c)]
                self.assertTrue(matching, "Missing host section/table row: " + host)
                combined = "\n".join(matching)
                self.assertTrue(any(f"~/{d}/skills/" in combined for d in allowed), "Missing user-wide path")
                self.assertTrue(any(re.search(r"(?<![\w~/])(?:<repo>/|\./)?" + re.escape(d) + r"/skills/", combined)
                                    for d in allowed), "Missing per-repository path")
                self.assertTrue(invocation in combined
                                or invocation.replace("<skill>", "review-assistant") in combined,
                                "Missing invocation: " + invocation)
        self.require_patterns(text, {
            "copy or symlink": r"copy|symlink|symbolic|cp\s|ln -s",
            "keep folder name": r"(?:keep|preserve|retain|must|don't rename|do not rename).*review-assistant|review-assistant.*(?:folder name|directory name)",
        })

    def test_size_report_and_loose_ceiling(self):
        """Preserving an invariant: report the trim goal; guard baseline size and description."""
        # The dev-knacks metadata.source line is catalog metadata, not skill
        # prose; it is excluded so the frozen baseline ceilings still apply.
        source_line = re.compile(r"(?m)^\s+source:\s*" + re.escape(SOURCE_URL) + r"\s*$")
        counts = {str(path.relative_to(self.skill_dir)): len(source_line.sub("", self.read(path), count=1).split())
                  for path in self.skill_files()}
        self.assertEqual(set(counts), set(BASELINE_WORDS), "Count the complete seven-file skill")
        total = sum(counts.values())
        print("\nSkill size (whitespace-delimited words; baseline frozen at the review-assistant 0.1.0 release = 4,424):", flush=True)
        for name in sorted(counts):
            ratio = counts[name] / BASELINE_WORDS[name]
            print(f"  {name}: {counts[name]}/{BASELINE_WORDS[name]} ({ratio:.1%})", flush=True)
        status = "met" if total <= 3600 else "exceeded (advisory)"
        print(f"  TOTAL: {total}/4424 ({total / 4424:.1%}); goal 3600 {status}; guard: no file above baseline", flush=True)
        for name, count in counts.items():
            with self.subTest(file=name):
                self.assertLessEqual(count, BASELINE_WORDS[name], "Skill file grew beyond baseline")
        self.assertLessEqual(len(frontmatter(self.skill())[0]["description"]), 1024)


    def ref(self, name):
        return self.read(self.skill_dir / "references" / (name + ".md"))

    def raw_section(self, text, topic):
        matches = [body for title, body in sections(text) if re.search(topic, prose(title))]
        self.assertTrue(matches, f"Missing section: {topic}")
        return "\n".join(matches)

    def absent(self, text, patterns):
        for label, pattern in patterns.items():
            with self.subTest(removed=label):
                self.assertNotRegex(prose(text), pattern, label)

    def test_cut_l01_per_type_examples(self):
        """Reproducing a failure (L1/F3): remove covered-type examples; retain strategy."""
        self.absent(self.section_text(self.skill(), r"^[23]\."), {
            "Pass 0 examples": r"(?:design doc|product/company|patent):",
            "Pass 1 examples": r"(?:design|product|patent):",
        })

    def test_cut_l02_single_rule_owners(self):
        """Reproducing a failure (L2): one full rule at each canonical owner."""
        turn = self.section_text(self.skill(), r"^4\.")
        self.require_patterns(turn, {"evaluation pointer": r"(?:section\s*|§)5",
                                     "tree pointer": r"(?:section\s*|§)6"})
        self.absent(turn, {"repeated item limit": r"(?:three|3).{0,20}also consider",
                           "repeated breadcrumb format": r"nearby open:|▸"})
        owners = {
            5: r"also consider.{0,60}(?:three|3)",
            6: r"breadcrumb.{0,90}(?:nearby open|▸)",
            8: r"constructive.{0,20}(?:not|never).{0,10}falsely positive",
            9: r"(?:vendor.{0,15}author|author.{0,15}vendor).{0,50}attribut",
        }
        for owner, pattern in owners.items():
            with self.subTest(owner=owner):
                self.assertRegex(self.section_text(self.skill(), rf"^{owner}\."), pattern)
                count = sum(len(re.findall(pattern, prose(body)))
                            for title, body in sections(self.skill()) if re.match(r"\d+\.", title))
                count += sum(len(re.findall(pattern, prose(self.ref(Path(n).stem)))) for n in REFERENCE_NAMES)
                self.assertEqual(count, 1, "Rule must have one full definition")

    def test_cut_l03_vendor_evidence_repeats(self):
        """Reproducing a failure (L3): remove general evidence rules from vendor reference."""
        self.absent(self.ref("product-vendor"), {
            "generic date rule": r"date everything|date (?:all|every) (?:facts?|material|sources?)",
            "version drift rule": r"(?:check|verify|track).{0,20}version drift",
            "absence principle": r"absence of evidence (?:is|as) (?:a )?finding",
        })

    def test_cut_l04_design_reading_record_repeats(self):
        """Reproducing a failure (L4/F6): remove generic repeats, allow unique anchor spans."""
        self.absent(self.reference_section("design-doc.md", r"reading|record notes"), {
            "paraphrase instruction": r"paraphrase|quote only decisive",
            "show figures repeat": r"show.{0,20}(?:doc|material).{0,15}own figures",
            "exact-word anchor repeat": r"anchor.{0,20}(?:each|every) entry.{0,20}exact words",
        })

    def test_cut_l05_pass_zero_repeats(self):
        """Reproducing a failure (L5): remove who-hurts/why-now repetitions."""
        self.absent(self.reference_section("design-doc.md", r"pass 0"), {
            "why now": r"why now",
            "generic problem probe": r"who hurts|what happens today|problem concrete",
        })

    def test_cut_l06_source_and_counsel_repeats(self):
        """Reproducing a failure (L6): source fetch and counsel have shared owners."""
        self.absent(self.ref("repo-code"), {"fetch repeat": r"fetch.{0,20}(?:actual )?source|rely on memory"})
        for name in ("patent-disclosure", "patent-portfolio"):
            self.absent(self.ref(name), {name + " counsel": r"counsel|not legal advice|specialist"})
        self.assertRegex(self.section_text(self.skill(), r"^1\."), r"actual source.{0,30}not readme or memory")

    def operational_patterns(self):
        return {
            "timing modes": r"\bsync(?:hronous)?\b.{0,20}\basync(?:hronous)?\b",
            "critical path": r"critical.path",
            "end-to-end budget": r"end.to.end.{0,20}(?:time )?budget",
            "cost model shifted elsewhere": r"cost model.{0,50}(?:shift|elsewhere)",
            "per-item bulk phenomenon": r"per.item.{0,50}(?:phenomenon|bulk).{0,30}bulk|per.item.{0,50}bulk phenomenon",
            "bulk blast radius": r"bulk blast radius",
            "feedback learning versus static": r"static thresholds.{0,65}(?:learn|outcomes)|(?:learn|outcomes).{0,65}static thresholds",
            "misclassification": r"misclassif",
            "silent heuristics": r"heuristics?.{0,25}(?:fail silently|silent)|silent.{0,25}heuristics?",
            "auditability and explainability": r"audit\w*.{0,30}explain\w*.{0,45}(?:ai|agent)|(?:ai|agent).{0,45}audit\w*.{0,30}explain",
            "model/prompt stability": r"(?:stabil\w*|stable).{0,40}model.{0,20}prompt.{0,15}changes",
            "untrusted input": r"untrusted input",
            "human loop": r"humans?.{0,15}(?:in the loop|in.loop)",
            "completed-task cost": r"cost per completed task",
        }

    def test_cut_l07_shared_operational_probes(self):
        """Exercising new behaviour (L7): shared operational list and two pointers."""
        shared = self.section_text(self.skill(), r"^9\.")
        self.assertRegex(shared, r"operational probes\s*\(all types\)")
        self.assertEqual(len(re.findall(r"operational probes\s*\(all types\)", shared)), 1)
        self.require_patterns(shared, self.operational_patterns())
        for name in ("design-doc", "patent-disclosure"):
            text = self.ref(name)
            pointer_lines = [line for line in text.splitlines()
                             if re.search(r"(?:§\s*9|section\s+9)", line, re.I)]
            self.assertTrue(pointer_lines, name + " needs a section 9 pointer")
            for line in pointer_lines:
                self.assertRegex(prose(line), r"operational probes")
            # A shared-list mention is legal; copying its actual probes is not.
            self.absent(text, {"copied " + k: v for k, v in self.operational_patterns().items()})
        self.assertRegex(prose(self.ref("patent-disclosure")), r"probes.{0,15}usually expose thin disclosures.{0,100}(?:§\s*9|section\s+9)")
        self.absent(self.reference_section("design-doc.md", r"probes"), {
            "aggregate lens": r"aggregate behavior:",
            "AI lens": r"ai and agent behavior:",
            "scale cost": r"cost model.{0,15}scale",
            "outcome feedback": r"outcomes feed back|never learn",
            "agent audit": r"agent decision.{0,25}audit",
        })

    def test_cut_l08_imperative_noun_list_support(self):
        """Exercising new behaviour (L8): terse lists have an imperative lead."""
        for name, topic in (("design-doc", r"probes"), ("repo-code", r"health signals"),
                            ("benchmark-poc", r"pass 1")):
            text = self.raw_section(self.ref(name), topic)
            self.assertRegex(prose(text), r"(?:probe|check|assess|inspect|verify):")
            for item in self.round2_probe_items(name + ".md", topic):
                self.round2_require_probe(item)

    def test_cut_l09_shorter_step_lists(self):
        """Reproducing a failure (L9): turn/evaluation lists lose wording."""
        # Panel: section 1.3 need not shrink. Its semantics are checked by
        # test_keep_skill_setup_and_problem_checkpoint.
        for number, baseline in ((4, 165), (5, 266)):
            self.assertLess(len(self.raw_section(self.skill(), rf"^{number}\.").split()), baseline)

    def test_cut_l10_writeup_outline_one_line(self):
        """Reproducing a failure (L10): eight headings in order, no outline hints."""
        text = self.raw_section(self.skill(), r"^8\.")
        names = ("context", "problem map and bar", "bottom line", "what is strong",
                 "conclusions", "suggestions", "open questions", "second pass and out of scope")
        lines = [prose(line) for line in text.splitlines() if all(n in prose(line) for n in names)]
        self.assertEqual(len(lines), 1, "Eight headings must share one line")
        line = lines[0]
        self.assertEqual([line.index(n) for n in names], sorted(line.index(n) for n in names))
        # Closure instructions may precede the outline on the same line.
        remainder = line[line.index(names[0]):line.index(names[-1]) + len(names[-1])]
        # F7 restores the positive-content rule alongside the strengths heading.
        remainder = re.sub(r"(?:include|state|identify) (?:genuine|real|evidenced) (?:positives|strengths)", "", remainder)
        for name in names:
            remainder = remainder.replace(name, "", 1)
        # 'by theme' is part of the existing conclusions heading; not a hint.
        remainder = remainder.replace("by theme", "")
        remainder = re.sub(r"^outline\s*:", "", remainder)
        self.assertNotRegex(remainder, r"[a-z]", "Outline still contains per-heading hints")

    def test_cut_l11_phase_notes_removed(self):
        """Reproducing a failure (L11): remove other per-phase notes."""
        self.absent(self.reference_section("product-vendor.md", r"planning"), {
            "tour note": r"product,? not the tour",
        })

    def test_cut_l12_workspace_one_line(self):
        """Reproducing a failure (L12): one workspace line without contents inventory."""
        text = self.raw_section(self.ref("product-vendor"), r"workspace")
        self.assertEqual(len([s for s in text.splitlines() if s.strip()]), 1)
        self.absent(text, {"folder inventory": r"frozen claims baseline|contradictions ledger|draft vendor questions|sources index|evaluation plan"})

    def test_cut_l13_filing_two_lines(self):
        """Reproducing a failure (L13): two filing-lens lines without defensive values."""
        text = self.raw_section(self.ref("patent-disclosure"), r"filing lens")
        self.assertEqual(len([s for s in text.splitlines() if s.strip()]), 2)
        self.absent(text, {"defensive value list": r"freedom to operate|cross.licensing|litigation deterrence|portfolio.{0,10}weight"})

    def test_cut_l14_rubric_field_list_removed(self):
        """Reproducing a failure (L14): remove rubric fields, keep evaluation probes."""
        self.absent(self.reference_section("patent-disclosure.md", r"evaluation questions"), {
            "field enumeration": r"product significance|competitor likelihood|workaround difficulty|standards adoption",
        })

    def test_cut_l15_bibliographic_fields_collapsed(self):
        """Reproducing a failure (L15): replace bibliographic enumeration."""
        text = self.reference_section("patent-portfolio.md", r"per patent")
        self.assertRegex(text, r"bibliographic (?:data|details|information).{0,20}status")
        self.absent(text, {"enumerated dates": r"priority.{0,15}filing.{0,15}grant.{0,15}expiry",
                           "enumerated identity": r"number,? title,? assignee"})

    def test_cut_l16_coverage_dimensions_only(self):
        """Reproducing a failure (L16): coverage dimensions have no sub-item lists."""
        text = self.reference_section("design-doc.md", r"coverage check")
        self.absent(text, {"observability sub-items": r"metrics|logs|traces|alerting",
                           "evolution sub-items": r"upgrades|versioning|deprecation|operable by someone else"})

    def test_cut_l17_readability_exception(self):
        """Reproducing a failure (L17): remove two probes except five-minute test."""
        text = self.reference_section("design-doc.md", r"probes")
        self.assertRegex(text, r"senior reader.{0,30}(?:five|5).minutes.{0,35}built.{0,15}risky.{0,15}asked")
        self.absent(text, {"maintainability lens": r"maintainability|who operates|decisions superseded|schema and interface versioning",
                           "summary readability": r"summary alone.{0,30}(?:shape|system)"})

    def test_cut_l18_fields_one_line_each(self):
        """Preserving an invariant (L18): node and entry fields already occupy one line."""
        for number, label, fields in (
            (6, "node", ("id", "title", "status", "origin", "record entry")),
            (7, "entry", ("conclusion", "severity", "anchors", "evidence", "change", "internal", "external", "tree node")),
        ):
            lines = [prose(s) for s in self.raw_section(self.skill(), rf"^{number}\.").splitlines()
                     if re.match(rf"(?:- )?{label}:", prose(s))]
            self.assertEqual(len(lines), 1)
            for field in fields:
                self.assertIn(field, lines[0])

    def test_cut_l19_evidence_boundaries_shorter(self):
        """Reproducing a failure (L19): boundaries tighten while retaining rules."""
        # Section 9 gains L7's list, so a total-size comparison there is invalid.
        # Its semantic rules and deduplication have their own tests.
        self.assertLess(len(self.raw_section(self.skill(), r"^10\.").split()), 72)

    def test_cut_l20_architecture_signals_shorter(self):
        """Reproducing a failure (L20): architecture signal list tightens."""
        text = self.raw_section(self.ref("product-vendor"), r"pass 1")
        signal = re.search(r"(?im)^.*architecture signals[^\n]*", text)
        self.assertIsNotNone(signal)
        self.assertLess(len(signal[0].split()), 32)

    def test_keep_design_reading_and_pass_zero(self):
        """Preserving an invariant (L4/L5): design-specific reading and goals."""
        self.require_patterns(self.reference_section("design-doc.md", r"reading"), {
            "core before lens": r"core path first.{0,100}(?:then|before).{0,30}lens",
            "faithful redraw provenance": r"faithful redraw.{0,30}as a redraw|label.{0,30}faithful redraw",
            "end of pass 1 sketch with feedback and provenance": r"pass 1.{0,20}end.{0,40}(?:architecture )?sketch.{0,60}(?:agreed )?feedback.{0,40}(?:yours|your own)",
        })
        self.require_patterns(self.reference_section("design-doc.md", r"record notes"), {
            "anchor components": r"section number.{0,20}title.{0,20}page",
            "single finding": r"one finding per entry|each entry.{0,15}one finding",
        })
        self.require_patterns(self.reference_section("design-doc.md", r"pass 0"), {
            "goal follows problem": r"each goal.{0,30}follow.{0,25}problem",
            "goal completion": r"(?:each|goal).{0,100}(?:way|measure|test).{0,35}(?:met|achiev|complet)",
            "returning non-goals": r"non.goals.{0,30}(?:come back|return|reappear)",
            "not building and buying": r"not building.{0,25}buy|buy.{0,25}not build",
        })

    def test_declined_l21_design_coverage_dimensions(self):
        """Preserving an invariant (L21/L16): coverage policy and every dimension."""
        text = self.reference_section("design-doc.md", r"coverage check")
        self.require_patterns(text, {
            "covered and N/A with reason and missed": r"covered.{0,25}not applicable.{0,35}reason.{0,20}missed",
            "missing relevant dimensions become nodes": r"missing.{0,60}ship commitment.{0,30}tree nodes",
            "demo versus production obligation": r"demo.{0,30}little.{0,50}production.{0,15}most",
        })
        self.assertRegex(prose(self.ref("design-doc")), r"coverage check.{0,35}one turn.{0,20}early.{0,15}pass 1")
        for dimension in (
            "functional", "problem", "goals", "non-goals", "architecture", "components", "workflows",
            "decisions", "alternatives", "interfaces", "contracts", "data model", "storage", "retention",
            "schema evolution", "phases", "non-functional", "identity", "access", "tenancy", "isolation",
            "security", "compliance", "ai", "agent behavior", "scale", "performance", "capacity", "cost",
            "availability", "failure modes", "business continuity", "observability", "incident handling",
            "testing", "ci/cd", "rollout", "migration", "rollback", "maintainability", "evolution",
            "dependencies", "risks", "open questions",
        ):
            with self.subTest(dimension=dimension):
                self.assertTrue(has_terms(text, [dimension]), dimension)
        self.assertRegex(text, r"ai.{0,30}agent behavior.{0,25}(?:when |if )?applicable")

    def test_declined_l22_design_lens_objects_and_qualifiers(self):
        """Preserving an invariant (L22/L8): every unmoved lens object and qualifier."""
        text = self.reference_section("design-doc.md", r"probes")
        self.require_patterns(text, {
            "lens and commitment select probes": r"lens.{0,20}ship commitment.{0,25}(?:call for|require)|(?:probe|check).{0,40}lens.{0,20}ship commitment",
            "identity reaches each system": r"identity.{0,30}(?:each system|propagat)",
            "carried signed delegated or intermediary asserted": r"(?:carried|signed).{0,30}delegated.{0,30}asserted.{0,30}intermediary",
            "trust and reason": r"component.{0,20}trust.{0,20}why",
            "enforcement plus bug and bypass": r"enforc.{0,70}bug.{0,35}(?:client|bypass).{0,20}bypass|enforc.{0,70}bug.{0,35}bypass",
            "every entry path": r"(?:every|all) entry path.{0,30}agent.{0,15}direct.{0,15}batch.{0,20}interactive",
            "credentials existence": r"(?:which credentials exist|credentials.{0,15}which exist|credential inventory)",
            "credentials breadth lifetime minter": r"credentials?.{0,55}(?:broad|breadth).{0,25}(?:long.lived|lifetime).{0,25}(?:who|can).{0,15}mint",
            "multi-user principals removal or containment": r"principals.{0,25}many users.{0,35}remov.{0,20}contain",
            "derived data examples": r"derived data.{0,20}results.{0,15}copies.{0,15}caches.{0,15}indices",
            "derived destination reader source protection": r"derived data.{0,90}(?:land|destination).{0,25}(?:read|reader).{0,45}source.{0,20}protection",
            "errors metadata timing disclosure": r"errors.{0,15}metadata.{0,15}timing.{0,20}(?:reveal|leak)|(?:leak|reveal|disclos)\w*.{0,20}errors.{0,15}metadata.{0,15}timing",
            "knowingly open": r"knowingly.{0,15}(?:left )?open",
            "3am failure": r"(?:break|fail).{0,20}3 a\.?m\.?",
            "numbers and retry recovery examples": r"numbers.{0,25}(?:add up|inconsisten).{0,30}timeouts.{0,15}retry budgets.{0,20}recovery time.{0,15}target",
            "fills or saturates first": r"(?:fills|fills up).{0,25}saturates.{0,15}first",
            "customer upgrades and maintenance": r"upgrades.{0,20}maintenance windows.{0,30}customers",
            "workflows step by step": r"workflows.{0,20}step.by.step",
            "doc matches code if any": r"doc.{0,15}(?:match|vs\.?|versus|against).{0,15}code.{0,20}(?:if any|where present|if available)",
            "other systems true today": r"claims.{0,20}other systems.{0,20}(?:true today|currently true)",
            "current docs not memory": r"current docs.{0,15}not memory",
            "inconsistent facts": r"same fact.{0,30}(?:differently|different).{0,20}(?:two places|places)",
            "names and crossrefs": r"drifting names.{0,20}wrong cross.references",
            "missing declared interfaces": r"interfaces.{0,25}prose.{0,20}absent.{0,30}interface list",
            "offer contradiction pass with both quotes": r"offer.{0,25}contradiction.check pass.{0,35}(?:pair|both).{0,20}(?:both )?quotes",
            "five-minute test": r"senior reader.{0,30}(?:five|5).minutes.{0,35}built.{0,15}risky.{0,15}asked",
        })

    def test_keep_operational_meanings_before_or_after_move(self):
        """Preserving an invariant (L7): operational objects survive relocation."""
        # This invariant passes before migration; test_cut_l07 separately
        # enforces the final owner, absence of copies, and actionable pointers.
        text = (self.section_text(self.skill(), r"^9\.") + " " +
                self.reference_section("design-doc.md", r"probes") + " " +
                prose(self.ref("patent-disclosure")))
        self.require_patterns(text, self.operational_patterns())

    def test_keep_repo_health_objects_and_qualifiers(self):
        """Preserving an invariant (L8): repo health probes retain scope and qualifiers."""
        self.require_patterns(self.reference_section("repo-code.md", r"health signals"), {
            "recent activity authors bus factor": r"activity.{0,25}(?:30|thirty) days.{0,25}author concentration.{0,15}bus factor",
            "PR CI": r"ci.{0,15}(?:pull requests|prs)",
            "test scope beyond unit": r"test suite.{0,30}(?:covers|coverage).{0,45}quality.{0,15}behavior.{0,30}beyond unit",
            "repo versus roadmap": r"integrations.{0,20}backends.{0,25}repo.{0,25}roadmap",
            "external builds": r"builds?.{0,20}outside.{0,15}company",
            "license upstream fork": r"license.{0,15}undisclosed upstreams.{0,15}forks",
            "actual versus described interfaces": r"interfaces.{0,25}(?:actually )?exposed.{0,20}endpoints.{0,15}apis.{0,20}described",
        })

    def test_keep_benchmark_validity_objects_and_qualifiers(self):
        """Preserving an invariant (L8): benchmark probes retain objects and qualifiers."""
        self.require_patterns(self.reference_section("benchmark-poc.md", r"pass 1"), {
            "baseline identity": r"baseline.{0,25}(?:what is it|identity|identify|what it is)",
            "strawman examples": r"straw man.{0,25}untuned competitor.{0,20}old version.{0,20}wrong configuration",
            "data authorship and overlap": r"data.{0,20}(?:who wrote|author).{0,25}tuning.{0,20}held.out.{0,25}overlap",
            "frozen learning": r"(?:learning|tuning).{0,25}frozen.{0,20}evaluation",
            "leakage examples": r"leakage.{0,120}version history.{0,20}cached sources.{0,25}shared index.{0,30}test material",
            "excluded run kinds": r"excluded runs.{0,30}timeouts.{0,15}failures.{0,15}retries.{0,30}headline",
            "judging who": r"judging.{0,20}(?:who|judge identity)",
            "checkable preferred": r"prefer checkable pass/fail.{0,25}(?:over|rather than).{0,15}model judge",
            "human only uncheckable": r"expert human.{0,20}only.{0,30}nothing checkable",
            "ablation vendor contribution example": r"ablation.{0,50}vendor.{0,20}contribution.{0,30}bootstrap.only.{0,25}human tuning",
            "human tooling AI inferred labels": r"label each step.{0,15}human.{0,15}tooling.{0,15}ai.{0,20}(?:mark )?inferred",
            "hidden time-to-value tuning": r"time.to.value.{0,30}(?:hidden|hiding|conceal\w*) human tuning",
            "variance repeated and detectable": r"variance.{0,30}repeat runs.{0,35}minimum detectable difference",
            "tiers over winners": r"tiers.{0,35}rather than.{0,20}winner",
            "configuration frozen across suites": r"configuration.{0,45}frozen across suites",
            "harness constants": r"harness sensitivity.{0,30}(?:held constant|constants)",
        })

    def test_keep_vendor_examples_and_architecture(self):
        """Preserving an invariant (L3/L20): examples, hedges, dates, architecture signals."""
        self.require_patterns(self.ref("product-vendor"), {
            "17x attributed": r"(?:vendor claims|states).{0,30}17x",
            "blind spots": r"blind spots.{0,30}non.english markets.{0,20}login.walled sources.{0,20}customers under nda",
            "close negative-flipping gaps": r"close gaps.{0,30}flip a negative.{0,35}settled",
            "dating examples": r"feature first shipped.{0,35}demo environment.{0,15}created",
            "self-contradiction ranking": r"contradict\w*.{0,150}(?:among|one of).{0,20}strongest findings",
            "contradiction examples": r"customer counts.{0,15}sizes.{0,15}ga dates.{0,35}faq.{0,15}deck",
            "duplicate dependency tools": r"duplicate tools.{0,25}(?:dependency )?stack",
            "own pipeline versus compose specialists": r"own\w*.{0,20}pipeline.{0,20}end.to.end.{0,25}compos\w*.{0,15}specialists|end.to.end.{0,20}pipeline.{0,15}ownership.{0,25}compos\w*.{0,15}specialists",
            "critical licenses": r"licenses.{0,20}critical path",
            "deployment versus pitch with examples": r"deployment.{0,25}(?:reality|pitch).{0,30}hosted.{0,15}in.environment.{0,15}air.gapped",
        })

    def test_keep_vendor_workspace(self):
        """Preserving an invariant (L12): subject folders, provenance, update discipline."""
        self.require_patterns(self.reference_section("product-vendor.md", r"workspace"), {
            "one subject folder": r"folder per subject|per.subject folder",
            "raw digest derived separated": r"raw.{0,30}sources.{0,25}digests.{0,45}derived.{0,30}(?:apart|separate)|separat\w*.{0,30}raw.{0,30}digests.{0,30}derived",
            "never cite derived": r"never cit(?:e|ing).{0,15}derived|(?:do not|don't) cite.{0,15}derived",
            "new material versus record": r"new material.{0,25}(?:check|compare).{0,25}record|(?:check|compare).{0,15}new material.{0,25}record",
            "flag not overwrite": r"flag changes.{0,25}(?:don't|never|not|do not) overwrite",
        })

    def test_declined_l23_grading_definitions_complete(self):
        """Preserving an invariant (L23): evidence classes and full maturity meanings."""
        text = self.reference_section("product-vendor.md", r"grading")
        self.require_patterns(text, {
            "customer independent examples": r"independent.{0,20}trade press.{0,15}analyst.{0,20}named customer employee on record",
            "co-marketing partner": r"co.marketing.{0,15}partner page",
            "vendor-sourced examples": r"vendor.sourced.{0,15}(?:their )?site.{0,15}deck.{0,15}wire release",
            "logo only": r"logo only",
            "deployment distinctions": r"keep distinct.{0,25}named customer in production.{0,15}trial.{0,15}poc.{0,15}logo.{0,15}unattributed.{0,25}fortune 500 retailer",
            "observed used measured": r"observed.{0,15}(?:we )?used.{0,15}measured",
            "documented examples": r"vendor.doc.{0,20}docs.{0,15}changelog.{0,15}audit logs",
            "claimed marketing only": r"vendor.claim.{0,15}deck.{0,15}marketing only",
            "capability independent": r"capability evidence.{0,180}independent",
            "M5 corroborated shipping": r"m5\b.{0,40}shipping.{0,35}independently corroborated use",
            "M4 shipping": r"m4\b.{0,15}shipping",
            "M3 youth churn beta": r"m3\b.{0,40}under about (?:six|6) months.{0,20}rapid churn.{0,25}(?:labelled|labeled) beta",
            "M2 vendor demo only": r"m2\b.{0,20}demo.only.{0,30}only.{0,20}vendor.built environment",
            "M1 sold no artifact": r"m1\b.{0,20}announced.{0,15}named.{0,15}sold.{0,15}no working artifact",
            "M0 claim only": r"m0\b.{0,15}asserted.{0,15}claim only",
            "matrix fields": r"per.product.{0,15}per.feature matrix.{0,25}what it actually is.{0,15}phase.{0,15}evidence strength.{0,15}note.{0,30}move the rating",
            "update each phase": r"update after each phase",
        })

    def test_declined_l25_vendor_claims_baseline(self):
        """Preserving an invariant (L25): attributed frozen claims and separate findings."""
        self.require_patterns(self.reference_section("product-vendor.md", r"claims and findings"), {
            "baseline sources": r"claims baseline.{0,60}deck.{0,15}site.{0,15}white papers.{0,15}calls",
            "attribution and quotations": r"attributed.{0,15}quoted",
            "freeze when findings start and label": r"freeze.{0,20}findings start.{0,20}mark frozen",
            "findings cite baseline": r"findings.{0,20}separate record.{0,20}baseline",
            "contradictions source both and vendor questions": r"contradictions.{0,20}c ids.{0,20}both sides sourced.{0,40}vendor question list",
            "transcripts versus docs outside sources": r"transcripts.{0,30}each rep.{0,30}claim.{0,20}docs.{0,20}outside sources",
            "reps same call finding": r"reps contradicting.{0,25}one call.{0,20}(?:own|a) finding",
            "internal external wording": r"internal wording.{0,20}(?:separate from )?external.{0,25}fake.{0,20}unsubstantiated",
        })

    def test_declined_l25_vendor_phase_plan(self):
        """Preserving an invariant (L11/L25): phase trigger, order, gates and caveat."""
        text = self.reference_section("product-vendor.md", r"planning")
        self.require_patterns(text, {
            "conditional continuation": r"if the review continues",
            "cheap falsifiable first": r"cheapest.{0,20}most falsifiable first",
            "attended late": r"vendor.attended.{0,15}(?:work )?late",
            "phase order": r"0.{0,10}desk.{0,25}1.{0,15}hands.on.{0,70}2.{0,150}3.{0,15}vendor.attended.{0,30}4.{0,15}references.{0,70}5.{0,20}(?:bounded )?pilot",
            "central unscriptable test": r"one test central to our interest.{0,15}slide can't fake.{0,30}past their script",
            "per-phase gates": r"each phase.{0,15}cost.{0,25}done.{0,25}pass.{0,25}kill",
            "remote browser not performance": r"remote or isolated browser.{0,30}(?:not|aren't) performance numbers.{0,25}(?:write|record)",
        })

    def test_keep_patent_portfolio(self):
        """Preserving an invariant (L6/L15): status caveat and patent-specific fields."""
        self.require_patterns(self.ref("patent-portfolio"), {
            "algorithmic status caveat": r"google patents.{0,15}legal status.{0,20}algorithmic.{0,20}not a legal conclusion",
        })
        self.require_patterns(self.reference_section("patent-portfolio.md", r"per patent"), {
            "issued versus pending": r"issued.{0,30}pending",
            "marketing patented may be pending": r"marketing.{0,20}patented.{0,30}(?:possibly|may be) pending",
            "claim 1 plain language": r"claim 1.{0,15}plain language",
            "coverage versus sold": r"(?:actually )?covers.{0,45}(?:sold|sell)",
            "examiner prior art": r"examiner.cited prior art",
            "chain of title": r"chain of title",
            "inventor concentration": r"inventor concentration",
            "family members": r"family.{0,20}continuations.{0,20}foreign filings",
        })

    def test_keep_patent_disclosure_filing(self):
        """Preserving an invariant (L13): filing alternatives, enablement and priority."""
        self.require_patterns(self.reference_section("patent-disclosure.md", r"filing lens"), {
            "offensive": r"offensive.{0,20}(?:needs )?broad.{0,20}defensible claims.{0,20}enforceability.{0,20}detectability",
            "defensive tolerances and enablement": r"defensive.{0,200}(?:narrower|narrow).{0,25}(?:more )?obvious claims.{0,30}still needs enablement",
            "publication cost and purpose": r"defensive publication.{0,20}cheaper.{0,35}(?:only prior art|prior.art.only)",
            "competitive timing hedge": r"if competitive movement is likely.{0,25}file early",
            "priority continuation when mature": r"priority date.{0,30}continuation.{0,30}implementation matures",
        })

    def test_declined_l26_patent_evaluation_questions(self):
        """Preserving an invariant (L14/L26): all evaluation questions and examples."""
        self.require_patterns(self.reference_section("patent-disclosure.md", r"evaluation questions"), {
            "meaning and direction before score": r"before scoring.{0,30}confirm.{0,30}measures.{0,35}direction.{0,15}good for us",
            "we detect competitor infringement": r"detectability.{0,20}(?:can )?we.{0,20}detect.{0,15}competitor.{0,15}infring",
            "easy detection favors filing": r"easy detection.{0,15}favors filing",
            "substance versus filler": r"each answer.{0,20}substantive.{0,15}filler",
            "filler example and judgment": r"might become a best practice someday.{0,25}(?:informs nothing|filler)",
            "impact assumes unshown feasibility": r"business.impact.{0,30}(?:often )?assume.{0,20}feasibility.{0,35}(?:hasn't|not|unshown)",
            "authors self-undercut": r"authors.{0,20}own answers.{0,25}undercut.{0,15}filing",
            "workaround obviousness example": r"many workarounds exist.{0,35}obviousness concern",
        })

    def test_keep_four_cross_links(self):
        """Preserving an invariant: four cross-links remain advisory and resolve."""
        for source, topic, target, target_topic in (
            ("product-vendor", "sources", "repo-code.md", None),
            ("product-vendor", "sources", "patent-portfolio.md", None),
            ("repo-code", "cross.check", "design-doc.md", "correctness"),
            ("patent-portfolio", "across.*portfolio", "product-vendor.md", "grading"),
        ):
            text = self.reference_section(source + ".md", topic)
            self.assertIn(target, text)
            if target_topic:
                self.assertRegex(text, re.escape(target) + r".{0,30}" + target_topic)
            self.assertTrue((self.skill_dir / "references" / target).is_file())
            self.assertNotRegex(text, r"(?:must|required to|always) (?:read|load).{0,30}" + re.escape(target))

    def test_keep_skill_setup_and_problem_checkpoint(self):
        """Preserving an invariant (L1/L9): setup scope and confirmed problem bar."""
        self.require_patterns(self.section_text(self.skill(), r"^1\."), {
            "mixed types load relevant references": r"mixed material.{0,100}read each relevant",
            "anchors": r"(?:extract|text).{0,35}page/slide anchors",
            "render when figures tables matter": r"render pages.{0,25}figures.{0,15}tables matter",
            "skim structure": r"skim structure first.{0,25}headings.{0,15}pages.{0,15}own summary.{0,20}reading guide.{0,20}open decisions",
            "incremental reading search as needed": r"(?:don't|do not) read all up front.{0,30}read each part.{0,30}presented.{0,20}search.{0,30}question",
            "prose questions only missing info": r"ask in prose.{0,35}q001.{0,35}only.{0,30}(?:can't infer|cannot infer|unknown)",
            "decision and examples": r"decision.{0,25}file/hold.{0,15}launch/hold ga.{0,15}adopt/pass.{0,15}approve/rework",
            "reviewer role lens scope": r"reviewer.{0,15}role.{0,15}lens.{0,15}scope.{0,10}in/out",
            "commitment and examples": r"commitment.{0,15}demo.{0,15}preview.{0,15}production.{0,15}priority date.{0,15}contract",
            "writeup readers": r"writeup readers|writeup audience",
            "start planned walk": r"start.{0,25}exploration tree.{0,30}planned walk.{0,25}top.level nodes",
        })
        self.require_patterns(self.section_text(self.skill(), r"^2\."), {
            "before judging plain problems": r"before judging.{0,30}(?:plain|plainly).{0,100}problems.{0,35}claims to solve",
            "remove labels": r"minus.{0,20}labels|(?:remove|strip).{0,20}labels",
            "problem context": r"for whom.{0,15}why now.{0,15}proposed answer",
            "one turn quote each problem": r"one turn.{0,25}each problem.{0,30}short quote",
            "vague problems": r"(?:say|flag|name).{0,30}(?:vague|vagueness).{0,25}problem",
            "derive bar": r"derive the bar.{0,15}what a good answer must do",
            "reviewer confirms both": r"reviewer confirms or corrects both",
            "confirmed reference rest review": r"confirmed.{0,30}reference.{0,30}rest of the review",
            "record changes explicitly": r"record later changes explicitly",
        })

    def test_declined_l27_skill_altitude(self):
        """Preserving an invariant (L27/L1): section 3 rules and timeout example."""
        self.require_patterns(self.section_text(self.skill(), r"^3\."), {
            "pass zero problems": r"pass 0.{0,15}problems.{0,25}subject tries to solve",
            "pass one solution shape": r"pass 1.{0,15}structure.{0,25}solution's shape.{0,15}address",
            "pass two details": r"pass 2.{0,15}detail.{0,15}contracts.{0,15}fields.{0,15}limits.{0,15}wording",
            "default current altitude": r"default.{0,25}current pass.{0,15}altitude",
            "detail only higher impact": r"(?:raise|bring).{0,20}(?:lower )?detail only.{0,35}changes.{0,15}higher conclusion",
            "one line impact tree rest": r"impact in one line.{0,25}tree the rest.{0,15}pass 2",
            "every reviewer point placed": r"(?:place|put).{0,15}every reviewer point.{0,20}altitude",
            "name bigger issue": r"name.{0,15}bigger issue.{0,25}detail",
            "timeout example": r"30.second timeout.{0,55}workflow is synchronous",
            "offer low impact node": r"offer.{0,15}pass.2 node.{0,25}low.level points.{0,25}no higher impact",
            "mostly detail generated docs": r"mostly.detail material.{0,25}generated docs.{0,60}detail implies.{0,25}current altitude",
        })

    def test_declined_l27_skill_turn_shape(self):
        """Preserving an invariant (L27/L2/L9): section 4 turn and presentation rules."""
        self.require_patterns(self.section_text(self.skill(), r"^4\."), {
            "one scoped piece and examples": r"one scope.limited piece per turn.{0,20}section.{0,15}component.{0,15}product.{0,15}claim cluster",
            "paragraph and voice limits": r"3[–-]4 short paragraphs.{0,15}~?200 words in voice",
            "own summary decisive exact quotes": r"own.words summary.{0,20}short exact quotes.{0,20}decisive|summari[sz]e.{0,20}own words.{0,25}quote.{0,20}decisive.{0,20}short.{0,15}exact",
            "decisive examples": r"numbers.{0,15}conditions.{0,15}commitments.{0,15}hedges.{0,15}phrases.{0,30}argument turns on",
            "anchored examples": r"each anchored.{0,100}slide 13.{0,25}claim 1.{0,25}path/file.py:120.{0,25}transcript speaker.{0,15}timestamp",
            "exact words when requested": r"quote at length when (?:asked|requested)|(?:on request|when asked).{0,30}quote at length",
            "P labels one sequence": r"label paragraphs.{0,20}substance p1.{0,15}p2.{0,25}one sequence per session",
            "own assessment and basis": r"(?:your take|assess).{0,15}strong.{0,15}weak.{0,15}missing.{0,20}what it rests on",
            "stop after breadcrumb reviewer controls advance": r"end.{0,20}breadcrumb.{0,25}(?:then )?stop.{0,20}advance only.{0,25}reviewer says",
            "redirect wins any time": r"reviewer.{0,15}redirect wins at any point",
            "tables restricted with comparison example": r"tables only.{0,20}comparisons.{0,25}material says.{0,15}reviewer says.{0,15}evidence.{0,20}matrices",
            "material figures own sketch provenance": r"show.{0,20}material's own figures.{0,25}label own sketches as yours",
            "number title acronyms": r"sections by number and title.{0,25}acronyms on first use",
        })

    def test_keep_skill_evaluation(self):
        """Preserving an invariant (L2/L9): evaluation, challenge and suggestion rules."""
        self.require_patterns(self.section_text(self.skill(), r"^5\."), {
            "evaluate not merely record": r"evaluate each reviewer point.{0,20}(?:don't|do not) just record",
            "restate": r"restate in one line",
            "altitude bigger issue": r"altitude.{0,25}bigger issue",
            "own terms hidden assumptions": r"own terms.{0,25}hidden assumptions",
            "for against quotes anchors": r"material for/against.{0,20}quoted.{0,15}anchored",
            "elsewhere search first miss phrasing": r"elsewhere.{0,25}search first.{0,35}i found no",
            "outside evidence changes verdict": r"outside evidence.{0,30}knowledge.{0,15}web.{0,35}change the verdict",
            "partial verdict which part": r"holds in part.{0,15}which part",
            "unknown verdict settlement": r"can't tell yet.{0,15}what would settle",
            "recommend disposition": r"recommend.{0,25}record(?: as (?:a )?conclusion)?.{0,25}explore.{0,15}thread.{0,15}park.{0,15}drop",
            "manufactured disagreement": r"manufactured disagreement.{0,15}(?:the other|other failure)",
            "challenge concessions survivors withdrawals": r"challenged.{0,25}test.{0,15}honestly.{0,25}concede explicitly.{0,25}holds.{0,25}exactly what survives.{0,25}explicitly withdraw.{0,30}new context",
            "three unraised ranked decision impact": r"also consider.{0,25}(?:up to )?(?:three|3) unraised items per turn.{0,30}ranked\s+(?:by|according to)\s+(?:how much (?:they|each item|an item) (?:could|can|would) change the decision|(?:their |potential |expected )?decision impact|(?:their |potential |expected )?(?:effect|impact) on the decision)",
            "sources including contradiction reference knowledge web": r"material elsewhere.{0,35}self.contradiction.{0,30}reference.{0,20}standard coverage.{0,20}knowledge.{0,15}prior art.{0,20}web search",
            "web examples": r"current product facts.{0,20}competitors.{0,20}vendor claims.{0,20}published results",
            "basis why matters": r"each.{0,15}basis tag.{0,25}why it matters",
            "offer not pursue agent nodes": r"offer.{0,15}(?:don't|do not) pursue.{0,25}agent.origin nodes.{0,25}unless.{0,20}reviewer",
            "no imported preferences": r"better.{0,25}problem map and bar.{0,25}not.{0,25}preferences.{0,20}technologies.{0,15}standards.{0,15}architectures",
            "alternatives tradeoffs not doctrine": r"alternatives.{0,15}trade.off.{0,15}not doctrine",
            "no inference as quote": r"never pass inference off as.{0,20}material's words",
        })

    def test_keep_skill_tree_record_writeup(self):
        """Preserving an invariant (L10/L18): tree, record and writeup rules/fields."""
        self.require_patterns(self.section_text(self.skill(), r"^6\."), {
            "tree storage fallback": r"todo or task tool.{0,25}else.{0,20}review-tree.md.{0,35}files persist.{0,15}else.{0,20}conversation",
            "source of truth": r"source of truth",
            "hierarchical ids": r"t1.{0,10}t1\.2.{0,10}t1\.2\.1",
            "concluded record link": r"if concluded.{0,20}record entry id|record entry id.{0,20}(?:if|when) concluded",
            "thread child": r"thread.{0,25}child under the current node",
            "conclusion confirm record return": r"thread concludes.{0,25}one.line conclusion.{0,25}confirm with reviewer.{0,15}record.{0,25}way back.{0,20}parent.{0,20}nearest open siblings",
            "breadcrumb every turn": r"end (?:every|each) turn.{0,20}breadcrumb|breadcrumb.{0,25}(?:at the )?end of (?:every|each) turn",
            "tree on request checkpoints": r"compact full tree on request.{0,25}checkpoints.{0,20}pass end.{0,20}before writeup",
            "no silent deletion dropped reason": r"never delete.{0,20}silently.{0,25}dropped nodes.{0,20}reason",
        })
        self.require_patterns(self.section_text(self.skill(), r"^7\."), {
            "one running record beside tree": r"one consolidated record.{0,25}as you go.{0,20}beside the tree",
            "reviewer meaning": r"reviewer.{0,15}stated or agreed by reviewer",
            "accepted pending meanings": r"agent.accepted.{0,15}yours.{0,15}accepted.{0,20}agent.pending.{0,15}yours.{0,15}not yet engaged",
            "contradiction definition and discipline": r"contradictions.{0,25}c1.{0,25}material or its sources disagreeing with themselves.{0,25}source both sides.{0,20}(?:don't|do not) editorialize",
            "parked tree items": r"parked items.{0,15}parked tree nodes",
            "blocker meaning": r"blocker.{0,15}decision can't proceed until addressed",
            "anchor fields": r"anchors.{0,15}exact words.{0,15}section.{0,15}page or line",
            "evidence grades conditional": r"evidence with basis tags[,;]? and grades.{0,25}reference defines",
            "change evidence": r"what would change it",
            "separate wording where different": r"internal and external wording.{0,20}separately where they differ",
            "same-turn agreement and acknowledgment": r"record in the same turn as the agreement.{0,20}say in one line what you recorded",
            "weakened record correction no overwrite": r"new evidence weakens.{0,25}entry.{0,20}record a correction.{0,20}never quietly overwrite",
        })
        self.require_patterns(self.section_text(self.skill(), r"^8\."), {
            "close materiality": r"offer to close.{0,35}remaining open nodes can't change the decision.{0,25}name any.{0,20}still could",
            "writeup on closure or request format": r"then.{0,15}or on request.{0,25}one channel.neutral.{0,15}shareable writeup.{0,35}document format",
            "only approved origins pending first": r"only reviewer and agent.accepted entries.{0,20}list agent.pending.{0,30}reviewer to accept or drop first",
            "claims bounded evidence": r"bound every claim to its evidence|bound claims to evidence",
            "external audience wording": r"external wording.{0,25}audiences outside the review",
            "tone ask if unknown": r"match tone.{0,20}readers.{0,20}ask if unknown",
            "constructive author default": r"default.{0,20}authors asked.{0,25}constructive.{0,15}not falsely positive",
            "neutral title example": r"neutral title.{0,25}evaluation:.{0,15}subject",
        })

    def test_declined_l24_skill_evidence_rules(self):
        """Preserving an invariant (L19/L24): every section 9 evidence rule survives."""
        self.require_patterns(self.section_text(self.skill(), r"^9\."), {
            "prefer detail and examples": r"prefer detail(?:ed parts)?.{0,20}known issues.{0,15}appendices.{0,15}code.{0,15}claim text.{0,15}changelogs.{0,15}faqs.{0,25}over summary.{0,15}marketing",
            "detail usually wins disagreement finding": r"disagree.{0,25}detail usually wins.{0,30}disagreement.{0,15}finding",
            "trace origin": r"trace claims to origin",
            "confirmation independently independent": r"independent confirmation must be independent",
            "repeat own page confirms nothing": r"source repeating.{0,25}subject's own page.{0,25}confirms nothing",
            "exact verbs": r"exact verbs.{0,15}states.{0,15}confirms.{0,15}repeats.{0,15}implies",
            "absence finding with blind spots": r"absence of evidence.{0,15}finding.{0,35}method's blind spots",
            "date version drift across sources": r"date.{0,35}version drift.{0,25}material.{0,15}docs.{0,15}product",
            "arithmetic versus assumptions": r"(?:check|verify).{0,20}arithmetic.{0,20}internal numbers.{0,25}separate calculation errors.{0,20}risky assumptions",
            "current facts examples search not memory": r"verify current facts.{0,20}products.{0,15}versions.{0,15}prices.{0,15}roles.{0,15}availability.{0,20}search.{0,15}not memory",
            "findings open items confidence": r"separate findings from open items.{0,20}state confidence",
        })

    def test_keep_skill_boundaries(self):
        """Preserving an invariant (L6/L19): all data, access and confidentiality boundaries."""
        self.require_patterns(self.section_text(self.skill(), r"^10\."), {
            "untrusted content": r"material.{0,15}trial environments.{0,15}fetched pages.{0,20}data.{0,15}not instructions",
            "no access bypass and examples": r"never.{0,25}(?:route around|bypass).{0,15}access controls.{0,20}blocked fetch.{0,15}isolation.{0,15}mfa.{0,15}proxy",
            "operator fallback exact path capture record": r"blocked.{0,25}operator.driven.{0,25}reviewer drives.{0,30}exact path.{0,25}(?:what to )?capture.{0,25}record results",
            "confidential search boundary": r"(?:keep|exclude).{0,20}confidential specifics.{0,25}(?:out of|from).{0,15}web searches.{0,25}public concept",
            "patent legal commercial specialist but substantive": r"patent.{0,15}legal.{0,15}commercial.{0,35}counsel or.{0,15}specialist.{0,30}needed.{0,25}still.{0,15}substantive analysis",
        })


    def operational_contexts(self):
        """Use the final owner when present; otherwise inspect the legacy rules.

        This permits baseline invariant checks without allowing old references
        to mask defects in an existing shared list. Migration is tested by L7.
        """
        section = self.raw_section(self.skill(), r"^9\.")
        marker = re.search(r"operational probes\s*\(all types\)", prose(section))
        if marker:
            shared = prose(section)[marker.start():]
            return shared, shared, shared, True
        design = self.reference_section("design-doc.md", r"probes")
        disclosure = self.reference_section("patent-disclosure.md", r"operational completeness")
        return design, disclosure, prose(self.ref("design-doc")), False

    def test_f01_operational_lens_and_commitment_gate(self):
        """Preserving an invariant (F1): operational probes are selected by lens and commitment."""
        gate, _, _, _ = self.operational_contexts()
        self.require_patterns(gate, {
            "lens and ship-commitment selection":
                r"lens.{0,25}ship commitment.{0,25}(?:call for|require|warrant)|"
                r"(?:select|use|apply).{0,40}(?:according to|based on).{0,25}lens.{0,25}ship commitment",
        })

    def test_f01_generic_auditability_and_explainability(self):
        """Preserving an invariant (F1): generic audit/explanation, with AI emphasized not exclusive."""
        _, general, _, shared = self.operational_contexts()
        if shared:
            # The general requirement must precede the conditional AI block.
            general = re.split(r"ai and agent (?:components|systems)", general, maxsplit=1)[0]
        self.require_patterns(general, {
            "generic audit and explanation especially AI":
                r"audit\w*.{0,30}explain\w*.{0,35}(?:especially|particularly|including).{0,20}ai(?:.driven)?",
        })

    def test_f01_conditional_ai_probe_scope(self):
        """Preserving an invariant (F1): AI probes apply conditionally and retain all five objects."""
        _, _, context, shared = self.operational_contexts()
        if shared:
            # Require an explicit conditional block, not a condition elsewhere
            # in the file that does not scope these probes.
            marker = re.search(
                r"ai and agent (?:components|systems).{0,30}(?:when|where|if) (?:present|applicable)|"
                r"(?:when|where|if) (?:present|applicable).{0,30}ai and agent (?:components|systems)", context)
            self.assertIsNotNone(marker, "F1: missing conditional AI/agent block in SKILL section 9")
            context = context[marker.end():]
        else:
            self.require_patterns(context, {
                "legacy applicability qualifier": r"ai and agent behavior.{0,20}when applicable",
            })
            context = self.reference_section("design-doc.md", r"probes")
        self.require_patterns(context, {
            "agent audit": r"(?:each|every) agent decision.{0,35}audit|audit\w*.{0,35}(?:each|every) agent decision",
            "model/prompt stability": r"(?:stabil\w*|stable).{0,40}model.{0,20}prompt.{0,15}changes",
            "untrusted input": r"untrusted input",
            "humans in loop": r"humans?.{0,15}in the loop",
            "cost per completed task": r"cost per completed task",
        })

    def test_f01_each_agent_decision_auditable_afterward(self):
        """Preserving an invariant (F1): every agent decision supports retrospective audit."""
        _, _, context, shared = self.operational_contexts()
        if not shared:
            context = self.reference_section("design-doc.md", r"probes")
        self.require_patterns(context, {
            "per-decision retrospective audit":
                r"(?:each|every) agent decision.{0,35}audit\w*.{0,25}(?:afterward|afterwards|after the fact|retrospect\w*)|"
                r"(?:retrospect\w*|after.the.fact).{0,20}audit\w*.{0,35}(?:each|every) agent decision",
        })

    def test_f02_every_turn_breadcrumb_owned_by_section_six(self):
        """Preserving an invariant (F2): section 6 owns the every-turn rule and example."""
        self.require_patterns(self.section_text(self.skill(), r"^6\."), {
            "each-turn breadcrumb":
                r"end (?:every|each) turn.{0,20}breadcrumb|breadcrumb.{0,25}(?:at the )?end of (?:every|each) turn",
            "example": r"breadcrumb.{0,90}▸\s*t2\.1.{0,70}nearby open",
        })

    def test_f03_strategy_problem_and_bet(self):
        """Preserving an invariant (F3): strategy has no reference, so retain both altitude examples."""
        self.require_patterns(self.section_text(self.skill(), r"^2\."), {
            "strategy problem and bet": r"strategy.{0,25}market problem.{0,25}(?:the )?bet",
        })
        self.require_patterns(self.section_text(self.skill(), r"^3\."), {
            "strategy bet logic": r"strategy.{0,25}logic of (?:the )?bet|strategy.{0,25}bet.{0,20}logic",
        })

    def test_f03_design_problem_constraints(self):
        """Preserving an invariant (F3): design constraints survive the move to reference Pass 0."""
        # The baseline has the concept in section 2; L1 separately removes
        # that covered-type example, forcing the reference to preserve it.
        reference = self.reference_section("design-doc.md", r"pass 0")
        legacy = self.section_text(self.skill(), r"^2\.")
        self.assertTrue(
            bool(re.search(r"(?:problem|design).{0,50}constraints|constraints.{0,50}(?:problem|design)", reference))
            or bool(re.search(r"design doc:.{0,25}problems.{0,15}constraints", legacy)),
            "F3: design Pass 0 must retain the problem's operating constraints")

    def test_f03_product_boundary_addresses_problem(self):
        """Preserving an invariant (F3): product boundary belongs in the solution/problem check."""
        reference = self.reference_section("product-vendor.md", r"pass 1")
        legacy = self.section_text(self.skill(), r"^3\.")
        self.assertTrue(
            bool(re.search(r"boundar(?:y|ies).{0,50}(?:address|solve|meet|fit).{0,25}problem|"
                           r"problem.{0,40}(?:address|solv|met).{0,35}boundar(?:y|ies)", reference))
            or bool(re.search(r"solution's shape address.{0,90}product: boundaries", legacy)),
            "F3: product Pass 1 must test whether its boundary addresses the problem")

    def test_f04_phase_scope_and_bounded_pilot(self):
        """Preserving an invariant (F4): commercial phase is conditional and own-data pilot bounded."""
        self.require_patterns(self.reference_section("product-vendor.md", r"planning"), {
            "commercial only in scope": r"4.{0,15}references.{0,15}commercial.{0,30}(?:only if in scope|only when in scope|if within scope)",
            "bounded own-data pilot": r"5.{0,20}bounded pilot.{0,20}(?:our )?own data|5.{0,20}pilot.{0,20}(?:our )?own data.{0,20}bounded",
        })

    def test_f05_vendor_attribution_and_repo_test_coverage(self):
        """Preserving an invariant (F5): explicit number attribution and full health-probe meaning."""
        self.require_patterns(self.reference_section("product-vendor.md", r"claims and findings"), {
            "explicit vendor-number attribution":
                r"(?:attribute|label|identify|mark|treat).{0,25}vendor numbers.{0,20}(?:as )?vendor claims|"
                r"vendor numbers.{0,30}(?:attributed|labelled|labeled|identified|marked|treated).{0,20}(?:as )?vendor claims",
            "17x example and no facts": r"states 17x.{0,25}never fact",
        })
        self.require_patterns(self.reference_section("repo-code.md", r"health signals"), {
            "coverage and evaluations beyond units":
                r"test suite.{0,20}(?:what it covers|coverage).{0,20}especially.{0,15}quality or behavior evaluation beyond unit tests",
        })

    def test_f06_record_span_preserved_repeat_removed(self):
        """Reproducing a failure (F6): retain unique anchor spans while completing L4."""
        text = self.reference_section("design-doc.md", r"record notes")
        self.require_patterns(text, {
            "span examples": r"few words.{0,15}sentence.{0,20}heading.{0,25}whole.section point",
            "anchor location": r"section number.{0,15}title.{0,15}page",
            "one finding per entry": r"one finding per entry|each entry.{0,20}one finding",
        })
        self.absent(text, {
            "generic exact-word instruction": r"anchor.{0,20}(?:each|every) entry.{0,20}exact words",
        })

    def test_f07_genuine_positives_with_strengths_heading(self):
        """Preserving an invariant (F7): positive findings are a rule, not a removable hint."""
        self.require_patterns(self.section_text(self.skill(), r"^8\."), {
            "include genuine positives":
                r"what is strong.{0,60}(?:include|state|identify).{0,15}(?:genuine|real|evidenced) (?:positives|strengths)|"
                r"(?:include|state|identify).{0,15}(?:genuine|real|evidenced) (?:positives|strengths).{0,60}what is strong",
        })

    def test_f08_generated_doc_rationale_general_placement(self):
        """Exercising new behaviour (F8): paraphrase rationale moves to general quotes/anchors."""
        readme = self.read(SKILL_README)
        bullets =[prose(b) for b in re.split(r"(?m)^\s*[-*]\s+", readme)[1:]]
        design = [b for b in bullets if b.startswith("design docs.")]
        quotes = [b for b in bullets if re.match(r"quotes (?:and|&) anchors\.", b)]
        self.assertEqual(len(design), 1, "Expected one Design docs rationale bullet")
        self.assertEqual(len(quotes), 1, "Expected one general quotes/anchors rationale bullet")
        self.absent(design[0], {"misplaced paraphrase rationale": r"generated docs.{0,80}paraphras|paraphras.{0,40}decisive bits"})
        self.require_patterns(quotes[0], {
            "general generated-doc rationale": r"generated docs.{0,30}repeat.{0,50}paraphras\w*.{0,40}(?:quotes?|quoting).{0,20}only decisive bits",
        })


    def test_disclosure_applies_full_operational_list(self):
        """Exercising new behaviour: disclosure applies the full shared list without a selection gate."""
        text = self.reference_section("patent-disclosure.md", r"operational completeness")
        self.require_rule(text,
                          r"\b(?:apply|use|run|check).{0,20}\b(?:all|every|full|complete|entire)\b.{0,35}skill\s*(?:§\s*|section\s+)9\b.{0,30}operational probes",
                          r"\b(?:apply|use|run|check).{0,20}\b(?:all|every|full|complete|entire)\b.{0,20}operational probes.{0,35}skill\s*(?:§\s*|section\s+)9\b")
        self.assertNotRegex(text, r"\b(?:if|when|unless|except|optional|optionally)\b|\b(?:as|where) (?:applicable|needed)\b|\blens\b|ship.commitment",
                            "Disclosure must apply the full list without the lens/ship-commitment selection gate")


if __name__ == "__main__":
    unittest.main()
