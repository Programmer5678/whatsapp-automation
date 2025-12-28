from job_and_listener.job.models.base_job_func_model import BaseJobFunc

class ErrorHelloWorldJobFunc(BaseJobFunc):


    def run(self):
        
        self.add_issue_to_job_sql({"info": "Issue 1"})
        self.add_issue_to_job_sql( {"info": "Issue 2"})
        
        raise Exception("Hello world exception from scheduled job")