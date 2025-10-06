from evolution_framework import  WhatsappGroupCreate, create_group_and_invite

raf0_date = "DATE"

group_messages = [ "joe" ]

group_name = f"RAF0 {raf0_date}"
group_participants = [ "972532237008" ]
group_invite_msg_title = f"בבקשה להצטרף לקבוצה של הרף 0 שיתקיים ב {raf0_date}"

group_messages = [ """דגשים חשובים:
- הגעה עצאית לכניסה לקריית ההדרכה בשעה 13:30, לא תתאפשר כניסה לפניי ולא יתקבלו איחורים.
- שימו לב שהמיון הוא דו יומי ויש להביא ציוד לינה.
- נדרש להגיע עם חוגרים מקודדים
""" , 

"""
אנחנו יודעים שהדרך לבה״ד היא ארוכה… בואו נצעד אותה יחד! 💪🏻 בה״ד 1 ומדור הגפ״ה גאים להציג: אפליקציית מקראות ישראל הרישמית! שנועדה לפשט את הלמידה לקראת הקליטה לבה״ד 1. השימוש הינו חופשי ומומלץ להעברה ושיתוף עם כלל הצוערים שעתידים להיקלט לבה״ד. שיהיה המון בהצלחה! מדור גפ״ה בה״ד 1 🫶🏼 https://step-to-bhd1.web.app/home
""" ,

"""מצרפים את אפליקציית המקראות של בה"ד 1 לשימושכם"""

]

media = "https://raw.githubusercontent.com/Programmer5678/uploads/main/raf0.jpeg"

raf0_group = WhatsappGroupCreate(name=group_name,
                                   participants=group_participants,
                                   messages=group_messages,
                                   invite_msg_title=group_invite_msg_title,
                                   media=[media])

raf0_group_id = create_group_and_invite(raf0_group)
print(f"{group_name} group ID: {raf0_group_id }")