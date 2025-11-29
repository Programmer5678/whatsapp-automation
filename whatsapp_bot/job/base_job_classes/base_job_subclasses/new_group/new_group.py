from send_stuff_to_group import send_stuff
from job.base_job_classes.base_job import BaseJob
from job.base_job_classes.base_job_subclasses.new_group.handle_failed_adds import HandleFailedAdds
    

class NewGroupJob(BaseJob):
    """
    Represents a scheduled job (inherits from BaseJob) that:
    1. Handles failed adds by retrying or notifying.
    2. Sends media and messages to a specified group.
    """

    def run(self, *, invite_msg_title: str, media, messages, group_id: str):
        """
        Executes the job.

        Steps:
        1. Handle failed group additions using the instance cursor and job name.
        2. Send messages and media to the target group.

        Args:
            invite_msg_title (str): Title/message for invites or notifications.
            media: Media content to send (images, files, etc.).
            messages: List of messages to send.
            group_id (str): Identifier for the target group.
        """
        # Retry or notify failed adds for this group
        HandleFailedAdds(self.cur, self.job_name).run(
            invite_msg_title=invite_msg_title,
            group_id=group_id
        )

        # Send the actual media and messages to the group
        send_stuff(media, messages, group_id)
