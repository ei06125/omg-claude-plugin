import json

import pytest
import release
from support.git_repo import MANIFEST, MANIFEST_TEXT, Repo, make_released_repo


@pytest.fixture
def repo(tmp_path):
    return make_released_repo(tmp_path)


def next_of(repo):
    return release.next_version(repo.path)


class TestNextVersion:
    def test_accepting_a_spec_bumps_minor(self, repo):
        repo.write_spec("omg-search", "Accepted")
        repo.commit()
        assert next_of(repo) == ("0.2.0", "minor")

    def test_a_new_spec_added_as_accepted_bumps_minor(self, repo):
        repo.write_spec("omg-new", "Accepted")
        repo.commit()
        assert next_of(repo) == ("0.2.0", "minor")

    def test_a_new_spec_added_as_draft_is_not_a_release(self, repo):
        repo.write_spec("omg-new", "Draft, awaiting review")
        repo.commit()
        assert next_of(repo) is None

    def test_several_accepted_specs_bump_minor_once(self, repo):
        repo.write_spec("omg-search", "Accepted")
        repo.write_spec("omg-other", "Accepted")
        repo.commit()
        assert next_of(repo) == ("0.2.0", "minor")

    def test_editing_an_accepted_spec_without_changing_status_is_not_a_release(
        self, repo
    ):
        repo.write_spec("omg-hello", "Accepted", summary="Reworded summary.")
        repo.commit()
        assert next_of(repo) is None

    @pytest.mark.parametrize(
        "path",
        [
            ".claude/skills/hello/SKILL.md",
            ".claude/agents/ceo.md",
            ".claude-plugin/plugin.json",
            "sources/server/main.py",
            "configs/default.toml",
        ],
    )
    def test_a_change_to_shipped_content_bumps_patch(self, repo, path):
        repo.write(path, "changed\n")
        repo.commit()
        assert next_of(repo) == ("0.1.1", "patch")

    @pytest.mark.parametrize(
        "path",
        [
            "README.md",
            "tests/test_x.py",
            ".github/workflows/release.yml",
            "tools/helper.py",
            ".agents/Governance/rule.md",
            "documentation/Technical/ADR-9999.md",
        ],
    )
    def test_changes_users_never_receive_are_not_a_release(self, repo, path):
        repo.write(path, "changed\n")
        repo.commit()
        assert next_of(repo) is None

    def test_the_highest_bump_wins(self, repo):
        repo.write(".claude/skills/hello/SKILL.md", "fixed\n")
        repo.write_spec("omg-search", "Accepted")
        repo.commit()
        assert next_of(repo) == ("0.2.0", "minor")

    def test_a_breaking_marker_bumps_minor_below_one(self, repo):
        repo.write_spec("omg-hello", "Accepted", breaking=True)
        repo.commit()
        assert next_of(repo) == ("0.2.0", "minor")

    def test_a_breaking_marker_bumps_major_from_one(self, tmp_path):
        repo = make_released_repo(tmp_path, version="1.4.2")
        repo.write_spec("omg-hello", "Accepted", breaking=True)
        repo.commit()
        assert next_of(repo) == ("2.0.0", "major")

    def test_a_breaking_marker_already_at_the_tag_does_not_bump_again(self, tmp_path):
        repo = Repo(tmp_path / "work")
        repo.set_manifest_version("0.2.0")
        repo.write_spec("omg-hello", "Accepted", breaking=True)
        repo.commit("Initial")
        repo.tag("v0.2.0")
        repo.write_spec(
            "omg-hello", "Accepted", breaking=True, summary="Reworded summary."
        )
        repo.commit()
        assert next_of(repo) is None

    def test_nothing_changed_is_not_a_release(self, repo):
        assert next_of(repo) is None

    def test_it_measures_from_the_latest_tag_only(self, repo):
        repo.write_spec("omg-search", "Accepted")
        repo.commit()
        repo.set_manifest_version("0.2.0")
        repo.commit("release")
        repo.tag("v0.2.0")
        assert next_of(repo) is None


class TestLatestTag:
    def test_it_picks_the_highest_version_and_ignores_other_tags(self, repo):
        for name in ("v0.10.0", "v0.2.0", "v1", "vx", "latest", "v0.1.0-rc.1"):
            repo.tag(name)
        assert release.latest_tag(repo.path) == "v0.10.0"

    def test_it_returns_none_without_a_release_tag(self, tmp_path):
        repo = make_released_repo(tmp_path, tagged=False)
        assert release.latest_tag(repo.path) is None


class TestParsing:
    @pytest.mark.parametrize(
        ("status_line", "expected"),
        [
            ("Accepted", "accepted"),
            ("In development, awaiting owner acceptance", "in development"),
            ("Draft, awaiting owner review", "draft"),
            ("accepted", "accepted"),
            ("Something else", None),
        ],
    )
    def test_spec_status(self, status_line, expected):
        assert (
            release.spec_status(f"# Spec\n\n- **Status:** {status_line}\n") == expected
        )

    def test_a_spec_without_a_status_has_none(self):
        assert release.spec_status("# Spec\n\nNo header here.\n") is None

    def test_breaking_marker(self):
        assert release.is_breaking("# S\n\n- **Breaking:** yes\n")
        assert not release.is_breaking("# S\n\n- **Breaking:** no\n")
        assert not release.is_breaking("# S\n\nBreaking: yes but not in the header\n")

    @pytest.mark.parametrize("text", ["0.1", "v0.1.0", "1.2.3.4", "a.b.c", ""])
    def test_parse_version_rejects_anything_but_x_y_z(self, text):
        with pytest.raises(ValueError):
            release.parse_version(text)

    def test_parse_version(self):
        assert release.parse_version("1.20.3") == (1, 20, 3)

    @pytest.mark.parametrize(
        ("kind", "expected"),
        [("major", "2.0.0"), ("minor", "1.3.0"), ("patch", "1.2.4")],
    )
    def test_bump(self, kind, expected):
        assert release.bump("1.2.3", kind) == expected


class TestBumpManifest:
    def test_only_the_version_line_changes(self):
        before = MANIFEST_TEXT % "0.1.0"
        after = release.bump_manifest_text(before, "0.2.0")
        assert after == MANIFEST_TEXT % "0.2.0"
        assert json.loads(after)["keywords"] == json.loads(before)["keywords"]

    def test_other_fields_named_version_are_left_alone(self):
        text = '{\n  "version": "0.1.0",\n  "meta": {\n    "version": "9.9.9"\n  }\n}\n'
        after = release.bump_manifest_text(text, "0.2.0")
        assert json.loads(after) == {"version": "0.2.0", "meta": {"version": "9.9.9"}}

    def test_a_manifest_without_a_version_is_an_error(self):
        with pytest.raises(release.ReleaseError):
            release.bump_manifest_text('{"name": "omg"}\n', "0.2.0")


class TestVerifyTag:
    def test_an_annotated_tag_on_main_matching_the_manifest_passes(self, tmp_path):
        repo = make_released_repo(tmp_path)
        release.verify_tag(repo.path, "v0.1.0", main_ref="main")

    def test_a_tag_on_a_side_branch_is_rejected(self, tmp_path):
        repo = make_released_repo(tmp_path)
        repo.git("switch", "-q", "-c", "side")
        repo.set_manifest_version("0.2.0")
        repo.commit("side release")
        repo.tag("v0.2.0")
        repo.git("switch", "-q", "main")
        with pytest.raises(release.ReleaseError, match="main"):
            release.verify_tag(repo.path, "v0.2.0", main_ref="main")

    def test_a_missing_manifest_at_the_tag_is_rejected(self, tmp_path):
        repo = Repo(tmp_path / "work")
        repo.write("README.md", "x\n")
        repo.commit("Initial")
        repo.tag("v0.1.0")
        with pytest.raises(release.ReleaseError, match=MANIFEST):
            release.verify_tag(repo.path, "v0.1.0", main_ref="main")
