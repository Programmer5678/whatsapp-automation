from sqlalchemy import text


# def insert_participants_to_sql(cur, participants):
#     """
#     Inserts a list of participants into the mass_messages table.
#     Skips any duplicates based on the primary key 'id'.

#     Args:
#         cur: Active DB cursor
#         participants: List of participant objects with 'id' and 'phone_number' attributes
#     """
#     insert_sql = text("""
#         INSERT INTO mass_messages (recipient_id, recipient_phone_number, success)
#         VALUES (:recipient_id, :recipient_phone_number, :success)
#     """)

#     for part in participants:
#         cur.execute(
#             insert_sql,
#             {
#                 "id": part.id,
#                 "phone_number": part.phone_number,
#                 "success": None
#             }
#         )