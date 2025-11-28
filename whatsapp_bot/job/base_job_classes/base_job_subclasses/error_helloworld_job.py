from base_job_classes.base_job import BaseJob


class ErrorHelloworldJob(BaseJob):


    def run(self):
        
        self.add_issue_to_job_sql({"info": "Issue 1"})
        self.add_issue_to_job_sql( {"info": "Issue 2"})
        
        raise Exception("Hello world exception from scheduled job")