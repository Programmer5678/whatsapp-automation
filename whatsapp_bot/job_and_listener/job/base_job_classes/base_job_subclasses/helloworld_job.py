from job_and_listener.job.base_job_classes.base_job import BaseJob

class HelloworldJob(BaseJob):


    def run(self):
        
        print(f"waiting in job {self.job_name} ...")
        import time
        time.sleep(60)
        print("done waiting")
        
        print("Writing Hello world to helloworld.txt")
        with open("helloworld.txt", "w") as f:
            f.write("Hello world")