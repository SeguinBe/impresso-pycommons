"""Code for parsing impresso's canonical directory structures."""

import os
import logging
from datetime import date
from collections import namedtuple

logger = logging.getLogger(__name__)

# a simple data structure to represent input directories
# a `Document.zip` file is expected to be found in `IssueDir.path`
IssueDir = namedtuple(
    "IssueDirectory", [
        'journal',
        'date',
        'edition',
        'path'
    ]
)


def canonical_path(dir, name=None, extension=None, path_type="file"):
    """Create a canonical dir/file path from an `IssueDir` object.

    :param dir: an object representing a newspaper issue
    :type dir: `IssueDir`
    :param name: the file name (used only if path_type=='file')
    :type name: string
    :param extension: the file extension (used only if path_type=='file')
    :type extension: string
    :param path_type: type of path to build ('dir' | 'file')
    :type path_type: string
    :rtype: string
    """
    sep = "-" if path_type == "file" else "/"
    extension = extension if extension is not None else ""
    if path_type == "file":
        return "{}{}".format(
            sep.join(
                [
                    dir.journal,
                    str(dir.date.year),
                    str(dir.date.month).zfill(2),
                    str(dir.date.day).zfill(2),
                    dir.edition,
                    name
                ]
            ),
            extension)
    else:
        return sep.join(
            [
                dir.journal,
                str(dir.date.year),
                str(dir.date.month).zfill(2),
                str(dir.date.day).zfill(2),
                dir.edition
            ]
        )


def detect_issues(base_dir):
    """Parse a directory structure and detect newspaper issues to be imported.

    NB: invalid directories are skipped, and a warning message is logged.

    :param base_dir: the root of the directory structure
    :rtype: list of `IssueDir` instances
    """
    detected_issues = []
    known_journals = ["GDL", "EVT", "JDG", "LNQ"]  # TODO: anything to add?
    dir_path, dirs, files = next(os.walk(base_dir))

    # workaround to deal with journal-level folders like: 01_GDL, 02_GDL
    journal_dirs = [d for d in dirs if d.split("_")[-1] in known_journals]

    for journal in journal_dirs:
        journal_path = os.path.join(base_dir, journal)
        journal = journal.split("_")[-1] if "_" in journal else journal
        dir_path, year_dirs, files = next(os.walk(journal_path))
        # year_dirs = [d for d in dirs if len(d) == 4]

        for year in year_dirs:
            year_path = os.path.join(journal_path, year)
            dir_path, month_dirs, files = next(os.walk(year_path))

            for month in month_dirs:
                month_path = os.path.join(year_path, month)
                dir_path, day_dirs, files = next(os.walk(month_path))

                for day in day_dirs:
                    day_path = os.path.join(month_path, day)
                    # concerning `edition="a"`: for now, no cases of newspapers
                    # published more than once a day in Olive format (but it
                    # may come later on)
                    try:
                        detected_issue = IssueDir(
                            journal,
                            date(int(year), int(month), int(day)),
                            'a',
                            day_path
                        )
                        logger.debug("Found an issue: {}".format(
                            str(detected_issue))
                        )
                        detected_issues.append(detected_issue)
                    except ValueError:
                        logger.warning(
                            "Path {} is not a valid issue directory".format(
                                day_path
                            )
                        )

    return detected_issues