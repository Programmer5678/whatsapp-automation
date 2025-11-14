def job_function_core( job_name : str,  invite_msg_title: str, media, messages, group_id: str, cur):
    
    participants = list(cur.execute(text("select phone_number from participants where group_id = :gid"), {"gid" : group_id} ).fetchall())
    
    
    



# inhernet JobContext
class JobbingAround:
    
    def __init__(self, job_name : str,  cur):
        
        self.cur = cur
        self.job_name = job_name
        

    def run( invite_msg_title: str, media, messages, group_id: str ):
        job_function_core( job_name,  invite_msg_title, media, messages, group_id, cur )