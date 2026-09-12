"""Documentation boundary tests for public/product vs private/development material."""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUBLIC_ROOT_FILES=[ROOT/'README.md',ROOT/'AGENTS.md',ROOT/'MCP_PROVIDER_STANDARD.md']
PUBLIC_DOCS=[
    *PUBLIC_ROOT_FILES,
    *ROOT.glob('docs/**/*.md'),
    *ROOT.glob('domains/**/*.md'),
    *ROOT.glob('software/**/*.md'),
    *ROOT.glob('catalogs/**/*.md'),
]
CLASS_RE=re.compile(r'^> Documentation class: (PUBLIC_[A-Z_]+)$',re.MULTILINE)


class DocumentationBoundaryTests(unittest.TestCase):
    def test_public_architecture_is_canonical_and_self_describing(self):
        path=ROOT/'docs'/'ARCHITECTURE.md'
        self.assertTrue(path.is_file())
        text=path.read_text(encoding='utf-8')
        self.assertIn('> Documentation class: PUBLIC_ARCHITECTURE',text)
        self.assertIn('Semantic-first',text)
        self.assertIn('Engineering Asset Catalog',text)
        self.assertNotIn('_private/',text)

    def test_documentation_policy_defines_public_and_private_classes(self):
        text=(ROOT/'docs'/'DOCUMENTATION_POLICY.md').read_text(encoding='utf-8')
        for token in [
            'PUBLIC_ARCHITECTURE','PUBLIC_CONTRACT','PUBLIC_POLICY',
            'PUBLIC_DOMAIN','PUBLIC_SOFTWARE_GUIDE','PUBLIC_CONTRIBUTOR',
            'PRIVATE_DEV_PLAN','PRIVATE_DEV_AUDIT','PRIVATE_DEV_ADR',
            'PRIVATE_HANDOFF','PRIVATE_BACKLOG','PRIVATE_EVIDENCE',
        ]:
            self.assertIn(token,text)

    def test_every_public_markdown_declares_documentation_class(self):
        missing=[]
        for path in PUBLIC_DOCS:
            if not path.is_file():
                continue
            head='\n'.join(path.read_text(encoding='utf-8').splitlines()[:12])
            if not CLASS_RE.search(head):
                missing.append(str(path.relative_to(ROOT)))
        self.assertEqual([],missing)

    def test_public_docs_do_not_link_to_private_or_internal_dev_documents(self):
        bad=[]
        for path in PUBLIC_DOCS:
            if not path.is_file():
                continue
            text=path.read_text(encoding='utf-8')
            if '](_private/' in text or '](../_private/' in text or '](../../_private/' in text:
                bad.append(str(path.relative_to(ROOT)))
        self.assertEqual([],bad)

    def test_public_readme_is_product_entrypoint_not_worktree_status_report(self):
        text=(ROOT/'README.md').read_text(encoding='utf-8')
        self.assertNotIn('## Trạng thái',text)
        self.assertNotRegex(text,r'unit_tests|git diff --check|private_tracked')
        self.assertIn('docs/ARCHITECTURE.md',text)
        self.assertIn('docs/README.md',text)


if __name__=='__main__':
    unittest.main()
