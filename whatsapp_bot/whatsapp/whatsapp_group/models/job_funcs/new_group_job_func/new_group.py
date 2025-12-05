from whatsapp.whatsapp_group.core.send_stuff_to_group import send_medias_and_messages_to_group
from job_and_listener.job.models.base_job_func_model import BaseJobFunc
from whatsapp.whatsapp_group.models.job_funcs.new_group_job_func.handle_failed_adds import HandleFailedAddsJobFunc
    

class NewGroupJobFunc(BaseJobFunc):
    """
    Represents a scheduled job (inherits from BaseJobFunc) that:
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
        HandleFailedAddsJobFunc(self.cur, self.job_name).run(
            invite_msg_title=invite_msg_title,
            group_id=group_id
        )

        # Send the actual media and messages to the group
        send_medias_and_messages_to_group(media, messages, group_id)
