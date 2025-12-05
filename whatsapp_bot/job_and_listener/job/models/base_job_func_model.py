import json
from abc import ABC, abstractmethod
from sqlalchemy import text

from db.get_cursor import get_cursor

class BaseJobFunc(ABC):
    """
    Abstract base class representing a generic job.

    Subclasses must implement the `run` method to define the job-specific logic.
    The main entrypoint for executing a job is the classmethod `job`, which:
      1. Obtains a database cursor.
      2. Creates an instance of the job with the cursor and job_name.
      3. Calls the job-specific `run` method with the provided arguments.

    This class also provides a helper method to record issues in the database.
    
    Usage:
    
    Subclasses implement the run
    Subclass.job(...) --> this calls the job-specific run function. When Subclass.run needs to raise issues it calls self.add_issue_to_job_sql 
    which inherited by BaseJobFunc
    
    """

    def __init__(self, cur, job_name: str):
        """
        Initialize a job instance.

        Args:
            cur: Database cursor to execute SQL statements.
            job_name: Unique identifier for the job.
        """
        self.cur = cur
        self.job_name = job_name

    @abstractmethod
    def run(self, **kwargs):
        """
        Abstract method representing the job logic.

        All subclasses must implement this method.

        Args:
            **kwargs: Arbitrary keyword arguments required by the specific job.
        """

    @classmethod
    def job(cls, job_name: str, run_args):
        """
        Classmethod entrypoint for executing the job.

        This method handles cursor management and instantiates the job,
        then delegates execution to the `run` method.

        Args:
            job_name: Unique identifier for the job.
            run_args: Dictionary of arguments to pass to `run`.
        """
        with get_cursor() as cur:
            # Create instance of job with DB cursor and job_name
            cls(cur, job_name).run(**run_args)

    def add_issue_to_job_sql(self, issue):
        """
        Add an issue to the job in the `job_information` table.

        The issue is JSON-serialized and appended to the array of issues
        associated with this job.

        Args:
            issue: Python object representing the issue.
        """
        self.cur.execute(
            text(
                """
                UPDATE job_information
                SET issues = array_append(issues, :issue_json)
                WHERE id = :job_name
                """
            ),
            {
                "issue_json": json.dumps(issue),
                "job_name": self.job_name,
            },
        )