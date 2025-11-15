from base_job_classes.base_job import BaseJob


class ErrorHelloworldJob(BaseJob):
    """
    Represents a scheduled job (inherits from BaseJob) that:
    1. Handles failed adds by retrying or notifying.
    2. Sends media and messages to a specified group.
    """

    def run(self):
        
        self.add_issue_to_job_sql({"info": "Issue 1"})
        self.add_issue_to_job_sql( {"info": "Issue 2"})
        
        raise Exception("Hello world exception from scheduled job")