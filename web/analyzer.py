"""Module containing logic used by the web app for repository analysis."""

from threading import Thread
from fastlog import log
from psycopg2 import Error as PG_Error
from easy_postgres import Connection as pg_conn
from engine.preprocessing.repoinfo import RepoInfo
from engine.preprocessing.module_parser import get_modules_from_dir
from engine.nodes.nodeorigin import NodeOrigin
from engine.algorithms.algorithm_runner import run_single_repo, OXYGEN
from engine.errors.user_input import UserInputError
from .credentials import db_url
from .pg_error_handler import handle_pg_error


def analyze_repo(repo_info, repo_id, algorithm=OXYGEN):
    """Analyze the repo using the specified algorithm. Store results in db."""
    log.info(f"Analyzing repository: {repo_info}")

    try:
        conn = pg_conn(db_url)

        if repo_info.clone_or_pull():
            log.success(
                f"Repository has been successfully cloned: {repo_info}")

        else:
            log.warning(f"Unable to clone repository: {repo_info}")

            conn.run("""UPDATE repos SET status = (SELECT id FROM states WHERE name = 'err_clone') WHERE id = %s;""",
                     repo_id)

            return

        modules = get_modules_from_dir(repo_info.dir)

        if not modules:
            log.warning("Repository contains no Python module")
            return

        result = run_single_repo(modules, algorithm)

        # Insert repository analysis into database all at once
        with conn.transaction():
            commit_id = conn.one("""INSERT INTO commits (repo_id, hash) VALUES (%s, %s) RETURNING id;""",
                                 repo_id, repo_info.hash)

            for c in result.clones:
                cluster_id = conn.one("""INSERT INTO clusters (commit_id, "value", weight) VALUES (%s, %s, %s) RETURNING id;""",
                                      commit_id, c.value, c.match_weight)

                for o, s in c.origins.items():
                    conn.run("""INSERT INTO origins (cluster_id, file, line, col_offset, similarity) VALUES (%s, %s, %s, %s, %s);""",
                             cluster_id, o.file, o.line, o.col_offset, s)

        log.success(f"Repository has been successfully analyzed: {repo_info}")

        conn.run("""UPDATE repos SET status = (SELECT id FROM states WHERE name = 'done') WHERE id = %s;""",
                 repo_id)

    except PG_Error as ex:
        handle_pg_error(ex, conn, repo_id)

    finally:
        conn.close()


def find_repo_results(conn, repo_id):
    """Find existing detection results for this repository in the database."""
    commit_id = conn.one("""SELECT id FROM commits WHERE repo_id = %s ORDER BY analyzed_at DESC LIMIT 1;""",
                         repo_id)

    if commit_id is None:
        return "No commit has been analyzed yet for this repository"

    clusters = conn.all_dict("""SELECT id, "value", weight FROM clusters WHERE commit_id = %s;""",
                             commit_id)

    for c in clusters:
        c.origins = [(NodeOrigin(o.file, o.line, o.col_offset), o.similarity) for o in
                     conn.all_dict("""SELECT file, line, col_offset, similarity FROM origins WHERE cluster_id = %s;""",
                                   c.id)]

    return clusters


def get_repo_analysis(repo_path):
    """
    Get analysis of a repository given its path.

    Returns:
        list[(NodeOrigin, float)] -- Clones in repo (origin and similarity).
        string -- Message describing the state of repo analysis.

    """
    # Strip leading and trailing whitespace from the path and parse repo info.
    repo_info = RepoInfo.parse_repo_info(repo_path.strip())

    if not repo_info:
        raise UserInputError("Invalid Git repository path format")

    try:
        conn = pg_conn(db_url)

        repo_id = conn.one("""INSERT INTO repos ("url", "server", "user", "name", "dir", "status") """ +
                           """VALUES (%s, %s, %s, %s, %s, (SELECT id FROM states WHERE name = 'queue')) """ +
                           """ON CONFLICT DO NOTHING RETURNING id;""",
                           repo_info.url, repo_info.server, repo_info.user, repo_info.name, repo_info.dir)

        if repo_id is not None:
            Thread(target=analyze_repo, args=(repo_info, repo_id)).start()
            return None, "The repository has been added to the queue"

        repo = conn.one_dict("""SELECT repos.id, states.name AS "status_name", states.description AS "status_desc" """ +
                             """FROM repos JOIN states ON (repos.status = states.id) """ +
                             """WHERE repos.url = %s OR (repos.server = %s AND repos.user = %s AND repos.name = %s) OR repos.dir = %s;""",
                             repo_info.url, repo_info.server, repo_info.user, repo_info.name, repo_info.dir)

        # Theoretically, this should never happend, but it's better to check anyways.
        if repo is None:
            return None, "Database error"

        elif repo.status_name in {"queue", "err_clone", "err_analysis"}:
            return None, repo.status_desc

        elif repo.status_name == "done":
            return find_repo_results(conn, repo.id), None

        else:
            return None, "Unexpected repository status"

    except PG_Error as ex:
        handle_pg_error(ex, conn, repo_id)
        return None, "Database error"

    finally:
        conn.close()
