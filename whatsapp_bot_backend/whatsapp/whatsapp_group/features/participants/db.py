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


def _save_group_and_participants(cur, group_id: str, participants: list[str]) -> None:
    """
    Insert group info and participants into the DB.

    Logic kept identical to the original:
    - single INSERT into group_info
    - then a simple for-loop inserting each participant one-by-one
    - same SQL and parameter names
    """
    # Insert into group_info
    cur.execute(
        text("INSERT INTO group_info (group_id) VALUES (:gid)"),
        {"gid": group_id},
    )

    # Insert participants (one-by-one, same logic as before)
    for phone_number in participants:
        cur.execute(
            text(
                "INSERT INTO participants (phone_number, group_id) VALUES (:phone_number, :gid)"
            ),
            {"gid": group_id, "phone_number": phone_number},
        )

