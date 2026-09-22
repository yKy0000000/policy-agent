"""Tests for the document-loading boundary only."""

from pathlib import Path
import tempfile
import unittest

from src.ingest import discover_policy_files, load_policy_documents


class IngestTests(unittest.TestCase):
    def test_loads_policy_text_and_metadata_without_chunking(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            policy_file = repository / "Policies" / "example" / "sample-policy.md"
            policy_file.parent.mkdir(parents=True)
            policy_file.write_text(
                "---\n"
                "title: Sample Policy\n"
                "versions:\n"
                "  fpt: '*'\n"
                "---\n"
                "Introductory policy text.\n\n"
                "## Requirements\n\n"
                "Follow the policy.\n",
                encoding="utf-8",
            )

            documents = load_policy_documents(repository)

            self.assertEqual(len(documents), 1)
            document = documents[0]
            self.assertEqual(document.title, "Sample Policy")
            self.assertEqual(document.source_path, "Policies/example/sample-policy.md")
            self.assertEqual(document.headings[0].text, "Requirements")
            self.assertNotIn("title: Sample Policy", document.text)
            self.assertIn("Introductory policy text.", document.text)
            self.assertEqual(
                document.source_url,
                "https://github.com/github/site-policy/blob/main/Policies/example/sample-policy.md",
            )

    def test_ignores_repository_level_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "README.md").write_text("# Repository README\n", encoding="utf-8")
            policies = repository / "Policies"
            policies.mkdir()
            (policies / "policy.md").write_text("# Policy\n", encoding="utf-8")

            discovered = discover_policy_files(repository)

            self.assertEqual([path.name for path in discovered], ["policy.md"])


if __name__ == "__main__":
    unittest.main()

