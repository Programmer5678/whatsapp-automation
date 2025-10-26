from setup import get_cursor
from sqlalchemy import text

def change_participants(cur, group_id, new_participants):
    
    # Delete all existing participants for the group
    cur.execute(
        text("DELETE FROM participants WHERE group_id = :gid"),
        {"gid": group_id}
    )

    # Insert new participants
    for phone_number in new_participants:
        cur.execute(
            text(
                "INSERT INTO participants (phone_number, group_id) VALUES (:phone, :gid)"
            ),
            {"phone": phone_number, "gid": group_id}
        )

        