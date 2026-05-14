import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_app_metadata.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_app_metadata", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_app(root, name, compose, appfile=None):
    app_dir = root / "Apps" / name
    app_dir.mkdir(parents=True)
    (app_dir / "docker-compose.yml").write_text(textwrap.dedent(compose).lstrip(), encoding="utf-8")
    if appfile is not None:
        (app_dir / "appfile.json").write_text(textwrap.dedent(appfile).lstrip(), encoding="utf-8")


class ValidateAppMetadataTests(unittest.TestCase):
    def test_valid_compose_and_appfile_has_no_issues(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_app(
                root,
                "GoodApp",
                """
                name: goodapp
                services:
                  goodapp:
                    image: ghcr.io/example/goodapp:1.2.3
                    environment:
                      FOO: bar
                    ports:
                      - target: 8080
                        published: "18080"
                        protocol: tcp
                    volumes:
                      - type: bind
                        source: /DATA/AppData/$AppID/config
                        target: /config
                    x-casaos:
                      envs:
                        - container: FOO
                          description:
                            en_US: Foo setting
                      ports:
                        - container: "8080"
                          description:
                            en_US: Web UI
                      volumes:
                        - container: /config
                          description:
                            en_US: Config
                x-casaos:
                  main: goodapp
                  version: "1.2.3"
                  updateAt: "2026-05-01"
                  releaseNotes:
                    en_US: Initial release.
                  website: "https://example.com"
                  repo: "https://github.com/example/goodapp"
                  support: "https://support.example.com"
                  docs: "https://docs.example.com"
                """,
                """
                {
                  "container": {
                    "image": "ghcr.io/example/goodapp:1.2.3"
                  }
                }
                """,
            )

            result = validator.validate_repo(root)

        self.assertEqual([], result.issues)
        self.assertEqual(1, result.summary["apps"])
        self.assertEqual("ok", result.traces[0]["status"])

    def test_detects_required_field_version_and_appfile_image_problems(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_app(
                root,
                "BadApp",
                """
                name: badapp
                services:
                  badapp:
                    image: example/badapp:2.0.0
                x-casaos:
                  main: badapp
                  version: "1.0.0"
                  updateAt: "2026/05/01"
                  releaseNotes: ""
                  website: "not-a-url"
                  repo: ""
                  docs: ""
                """,
                """
                {
                  "container": {
                    "image": "example/badapp:1.0.0"
                  },
                  "latest_update_date": "1777593600"
                }
                """,
            )

            result = validator.validate_repo(root)

        categories = {issue.category for issue in result.issues}
        self.assertIn("required_field_missing", categories)
        self.assertIn("version_image_mismatch", categories)
        self.assertIn("updateAt_format", categories)
        self.assertNotIn("releaseNotes_empty", categories)
        self.assertIn("url_format", categories)
        self.assertIn("appfile_image_tag_mismatch", categories)

    def test_linuxserver_registry_alias_matches_appfile_image(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_app(
                root,
                "Jackett",
                """
                name: jackett
                services:
                  jackett:
                    image: linuxserver/jackett:0.24.1841
                x-casaos:
                  main: jackett
                  version: "0.24.1841"
                  updateAt: "2026-05-11"
                  releaseNotes:
                    en_US: Release.
                  website: "https://example.com"
                  repo: "https://github.com/linuxserver/docker-jackett"
                  support: ""
                  docs: ""
                """,
                """
                {
                  "container": {
                    "image": "lscr.io/linuxserver/jackett:0.24.1841"
                  }
                }
                """,
            )

            result = validator.validate_repo(root)

        self.assertNotIn("appfile_image_repository_mismatch", {issue.category for issue in result.issues})
        self.assertNotIn("appfile_image_tag_mismatch", {issue.category for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
