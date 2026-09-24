import pytest
from omg_delegate.config import Config
from omg_delegate.models import Volume
from omg_delegate.volumes import check_volumes
from support import guardrails
from support.git_repo import Repo


@pytest.fixture
def world(tmp_path):
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    socket = tmp_path / "docker.sock"
    socket.write_text("")
    work = tmp_path / "work"
    work.mkdir()
    config = Config.from_dict(guardrails.build(socket), home=home)
    return {
        "tmp": tmp_path,
        "home": home,
        "socket": socket,
        "work": work,
        "config": config,
    }


def check(world, *volumes):
    return check_volumes(list(volumes), world["config"])


def test_a_plain_directory_is_accepted(world):
    assert check(world, Volume(str(world["work"]), "rw")) is None


def test_a_single_file_may_be_a_read_only_volume(world):
    file = world["work"] / "secret-notes.txt"
    file.write_text("x")
    assert (
        check(world, Volume(str(world["work"]), "rw"), Volume(str(file), "ro")) is None
    )


@pytest.mark.parametrize("path", ["docs/notes", "./here", "~/notes"])
def test_a_relative_path_is_refused(world, path):
    assert "absolute" in check(world, Volume(path, "rw"))


def test_a_missing_path_is_refused(world):
    assert "does not exist" in check(world, Volume(str(world["tmp"] / "nope"), "rw"))


def test_the_home_directory_is_too_broad(world):
    assert "too broad" in check(world, Volume(str(world["home"]), "ro"))


def test_an_ancestor_of_the_home_directory_is_too_broad(world):
    assert "too broad" in check(world, Volume(str(world["home"].parent), "ro"))


def test_the_filesystem_root_is_too_broad(world):
    assert "too broad" in check(world, Volume("/", "ro"))


def test_a_credential_directory_is_forbidden(world):
    assert "forbidden" in check(world, Volume(str(world["home"] / ".ssh"), "ro"))


def test_a_child_of_a_forbidden_path_is_forbidden(world):
    child = world["home"] / ".ssh" / "keys"
    child.mkdir()
    assert "forbidden" in check(world, Volume(str(child), "ro"))


def test_the_container_runtime_socket_is_forbidden(world):
    assert "forbidden" in check(world, Volume(str(world["socket"]), "rw"))


def test_a_symlink_is_judged_by_where_it_points(world):
    link = world["work"] / "link"
    link.symlink_to(world["home"] / ".ssh")
    assert "forbidden" in check(world, Volume(str(link), "rw"))


def test_a_clone_of_a_git_repository_as_the_first_volume_is_accepted(world):
    repo = Repo(world["tmp"] / "repo")
    repo.write("a.txt", "a")
    repo.commit("a")
    assert check(world, Volume(str(repo.path), "clone")) is None


def test_a_clone_of_a_directory_that_is_not_a_repository_is_refused(world):
    assert "git repository" in check(world, Volume(str(world["work"]), "clone"))


def test_a_clone_is_only_allowed_as_the_first_volume(world):
    repo = Repo(world["tmp"] / "repo")
    repo.write("a.txt", "a")
    repo.commit("a")
    message = check(
        world, Volume(str(world["work"]), "rw"), Volume(str(repo.path), "clone")
    )
    assert "first volume" in message


def test_an_unknown_mode_is_refused(world):
    assert "mode" in check(world, Volume(str(world["work"]), "rwx"))
