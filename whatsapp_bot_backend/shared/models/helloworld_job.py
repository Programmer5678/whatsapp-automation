from job_and_listener.job.models.base_job_func_model import BaseJobFunc

class HelloWorldJobFunc(BaseJobFunc):


    def run(self):
        
        print(f"waiting in job {self.job_name} ...")
        import time
        time.sleep(60)
        print("done waiting")
        
        print("Writing Hello world to helloworld.txt")
        with open("helloworld.txt", "w") as f:
            f.write("Hello world")