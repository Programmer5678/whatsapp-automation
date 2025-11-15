from base_job_classes.base_job import BaseJob


class HelloworldJob(BaseJob):
    """
    Represents a scheduled job (inherits from BaseJob) that:
    1. Handles failed adds by retrying or notifying.
    2. Sends media and messages to a specified group.
    """

    def run(self):
        
        print(f"waiting in job {self.job_name} ...")
        import time
        time.sleep(10)
        print("done waiting")
        
        print("Writing Hello world to helloworld.txt")
        with open("helloworld.txt", "w") as f:
            f.write("Hello world")