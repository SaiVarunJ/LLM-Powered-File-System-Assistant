import os
import shutil
from fs_tools import read_file, list_files, write_file, search_in_file


def test_read_file_txt_success():
    path = os.path.join("resumes", "resume_john_doe_python_dev.pdf")
    r = read_file(path)
    assert r["success"] is True
    assert "Python" in r["content"]


def test_read_file_not_exist():
    r = read_file("resumes/nonexistent_file.txt")
    assert r["success"] is False
    assert "does not exist" in r["error"]


def test_list_files_and_filter():
    files = list_files("resumes")
    assert isinstance(files, list)
    names = [f["name"] for f in files]
    assert "resume_john_doe_python_dev.pdf" in names

    txt_files = list_files("resumes", ".txt")
    assert any(f["name"].endswith(".txt") for f in txt_files)


def test_write_file_and_cleanup():
    out_path = os.path.join("resumes", "tmp_test_write.txt")
    w = write_file(out_path, "hello world")
    assert w["success"] is True
    assert os.path.exists(w["path"]) is True
    # cleanup
    try:
        os.remove(w["path"])
    except Exception:
        pass


def test_search_in_file_case_insensitive():
    path = os.path.join("resumes", "resume_john_doe_python_dev.pdf")
    s = search_in_file(path, "python")
    assert s["success"] is True
    assert isinstance(s["matches"], list)
    assert len(s["matches"]) >= 1
    assert "Python" in s["matches"][0]["snippet"] or "python" in s["matches"][0]["snippet"]

