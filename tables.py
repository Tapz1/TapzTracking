from project_lib import *


class ResultTable(Table):
    time_id = Col('time_id', show=False)
    user_id = Col('user_id', show=False)
    Date = Col('Date')
    FirstName = Col('First Name')
    LastName = Col('Last Name')
    Time_In = Col('Time In')
    Time_Out = Col("Time Out")
    date_submitted = Col('date_submitted', show=False)



class SalesTable(Table):
    """table for requested shifts"""
    sales_id = Col("shift_id", show=False)
    user_id = Col("user_id", show= False)
    Date = Col("Date")
    FirstName = Col("First Name", show=False)
    LastName = Col("Last Name", show=False)
    vid_unit = Col("Video Units")
    hsd_unit = Col("Internet Units")
    voice_unit = Col("Voice Units")
    revenue = Col("Revenue")
    chat_id = Col("Chat ID")
    cust_id = Col("Cust ID")
    comment = Col("Comments")
