

# --- STEP 2: Send messages to group (accepts WhatsappGroupCreate) ---
from typing import List
from evo_request import evo_request
from classes import WhatsappGroupCreate


def send_messages_to_group(messages : List[str] , group_id: str) -> None:
    for msg in messages:
        evo_request(
            "message/sendText",
            {
                "number": group_id,   # group IDs work here
                "text": msg
            }
        )


def send_medias_to_group(medias, group_id: str) -> None:
    for m in medias:
        evo_request(
            "message/sendMedia",
            {
                "number": group_id,   # group IDs work here
                "mediatype": "image",
                "mimetype": "image/jpeg",
                "fileName": "image.jpeg",
                "caption": "",
                "media" : m
            }
        )


def send_stuff(media , messages, group_id):
    
    send_medias_to_group(media, group_id)
    send_messages_to_group(messages, group_id)
    

