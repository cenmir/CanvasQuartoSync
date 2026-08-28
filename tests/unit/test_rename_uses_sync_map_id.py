"""Renaming must update the existing Canvas object, not create a second one.

The sync map exists so the tool knows which Canvas object belongs to which file.
It was only consulted when the file had *not* changed, so any edit fell through
to matching by title. If the title had changed too, the search found nothing and
a new object was created, leaving the original orphaned in the module.

That is the one case where the map is indispensable, and it was the one case
where it was ignored.
"""

import io
from unittest.mock import MagicMock, patch

import pytest

from handlers.assignment_handler import AssignmentHandler
from handlers.page_handler import PageHandler
from handlers.content_utils import save_sync_map


CANVAS_ID = 4242


def _write(tmp_path, name, title, canvas_type, mtime):
    """A content file whose recorded mtime is deliberately stale."""
    d = tmp_path / "01_Module"
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text(
        '---\ntitle: "%s"\ncanvas:\n  type: %s\n  published: false\n---\n\nBody.\n'
        % (title, canvas_type),
        encoding="utf-8",
    )
    rel = "01_Module/" + name
    # mtime differs from the file on disk, i.e. the file has been edited.
    save_sync_map(str(tmp_path), {rel: {"id": CANVAS_ID, "mtime": mtime}})
    return str(p)


def _course():
    course = MagicMock()
    course.id = 74
    course.time_zone = "Europe/Stockholm"   # a Mock here is not a loadable zone
    # Title search finds nothing, because the title has just changed. This is
    # what makes the old behaviour create a duplicate.
    course.get_assignments.return_value = []
    course.get_pages.return_value = []
    return course


@patch("handlers.assignment_handler.store_canvas_hash")
@patch("handlers.assignment_handler.save_mapped_id")
@patch("handlers.assignment_handler.process_content", side_effect=lambda c, *a, **k: c)
@patch.object(AssignmentHandler, "render_quarto_document", return_value="<p>Body</p>")
def test_renamed_assignment_updates_instead_of_creating(_render, _proc, _save, _hash, tmp_path):
    path = _write(tmp_path, "01_Lab.qmd", "Lab 4 - Torsion", "assignment", mtime=1.0)

    course = _course()
    existing = MagicMock()
    existing.id = CANVAS_ID
    existing.name = "Lab 4 - Physical torsion lab"   # the old title
    existing.description = "<p>Body.</p>"            # drift check reads this
    course.get_assignment.return_value = existing

    AssignmentHandler().sync(path, course, module=None, content_root=str(tmp_path))

    course.get_assignment.assert_called_once_with(CANVAS_ID)
    assert not course.create_assignment.called, (
        "renaming created a second assignment and orphaned the original"
    )
    assert existing.edit.called, "the existing assignment was never updated"


@patch("handlers.page_handler.store_canvas_hash")
@patch("handlers.page_handler.save_mapped_id")
@patch("handlers.page_handler.process_content", side_effect=lambda c, *a, **k: c)
@patch.object(PageHandler, "render_quarto_document", return_value="<p>Body</p>")
def test_renamed_page_updates_instead_of_creating(_render, _proc, _save, _hash, tmp_path):
    path = _write(tmp_path, "01_Page.qmd", "Section forces", "page", mtime=1.0)

    course = _course()
    existing = MagicMock()
    existing.page_id = CANVAS_ID
    existing.title = "Internal forces"               # the old title
    existing.body = "<p>Body.</p>"                   # drift check reads this
    course.get_page.return_value = existing

    PageHandler().sync(path, course, module=None, content_root=str(tmp_path))

    course.get_page.assert_called_once_with(CANVAS_ID)
    assert not course.create_page.called, (
        "renaming created a second page and orphaned the original"
    )
    assert existing.edit.called, "the existing page was never updated"


@patch("handlers.assignment_handler.store_canvas_hash")
@patch("handlers.assignment_handler.save_mapped_id")
@patch("handlers.assignment_handler.process_content", side_effect=lambda c, *a, **k: c)
@patch.object(AssignmentHandler, "render_quarto_document", return_value="<p>Body</p>")
def test_falls_back_to_title_search_when_the_id_is_gone(_render, _proc, _save, _hash, tmp_path):
    """Deleting the Canvas object by hand must still be recoverable.

    The title search is the fallback, and it has to keep working. It just must
    not be the path taken while a usable id exists.
    """
    path = _write(tmp_path, "01_Lab.qmd", "Lab 4", "assignment", mtime=1.0)

    course = _course()
    course.get_assignment.side_effect = Exception("404 Not Found")

    AssignmentHandler().sync(path, course, module=None, content_root=str(tmp_path))

    assert course.create_assignment.called, (
        "with the Canvas object gone, the sync should recreate it"
    )
