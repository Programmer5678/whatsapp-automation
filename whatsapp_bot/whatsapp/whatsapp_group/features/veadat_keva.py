
from whatsapp.whatsapp_group.core.schedule_create_group.core import create_group_and_invite
from whatsapp.whatsapp_group.models.whatsapp_group_create import WhatsappGroupCreate


veadat_keva_date = "DATE"
veadat_keva_time = "TIME"

group_name = f"ועדת קבע {veadat_keva_date}"
group_participants = [ "972532237008" ]
group_invite_msg_title = f"בבקשה להצטרף לקבוצה של ועדת הקבע שתתקיים ב {veadat_keva_date}"

group_messages = [ f"""
                  שלום לכולם, 
לקראת הקקצ יתקיימו ראיונות בראשות רען מפקדים . הראיונות בויסי(יישלח אליכם לינק סמוך לשעת הראיון). בבקשה - כולם למלא את הטופס הבא שמטרתו לוודא מאיזה יוזר אתם מתחברים.. 
{veadat_keva_date} שעה {veadat_keva_time} מתחילים
                  """]


veadat_keva_group = WhatsappGroupCreate(name=group_name,
                                   participants=group_participants,
                                   messages=group_messages,
                                   invite_msg_title=group_invite_msg_title,
                                   media=[])

veadat_keva_group_id = create_group_and_invite(veadat_keva_group)
print(f"{group_name} group ID: {veadat_keva_group_id }")