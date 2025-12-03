import streamlit as st 
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import plotly.express as px
import plotly.graph_objects as go 
from datetime import timedelta , datetime
import re
import pyperclip


#Function to Calculate Percentage of Tank level
def percentage_level(data: pd.DataFrame,column_header):
     results = (data[column_header].iloc[-1]/10000)*100
     return results

#Variables
url = "https://docs.google.com/spreadsheets/d/1E6XfwNLvw8m8oj2lVtglxvyC3edI70qIQOQKFmSYXcc"
def format(enter_number):
    formatted_number = f"{enter_number:.2f}"
    return formatted_number
#Function to connection to google sheet data
def connect_gsheet(url,_worksheet):
    #Establish connection to google sheet
    conn = st.connection("gsheets", type=GSheetsConnection)
    #Fetch the data to
    data = conn.read(spreadsheet=url ,worksheet = _worksheet, usecols=list(range(8)),ttl=5)
    data = data.dropna(how="all")
    return data

data = connect_gsheet(url,"RETM")

#Function to update Google Sheet with new Data frame ##########################################
def update_data(url,_worksheet,old_data,new_data):
     conn = st.connection("gsheets", type=GSheetsConnection)
     updated_df = pd.concat([old_data,new_data],ignore_index=True)
     conn.update(spreadsheet=url ,worksheet = _worksheet,data=updated_df)
     st.success("Data Updated Successfully!")

#Function Delete Selected row in data sheet.####################################################
def delete_row(url,_worksheet,rowIndex):
    #Establish connection to google sheet
    conn = st.connection("gsheets", type=GSheetsConnection)
    #Fetch the data to
    data = conn.read(spreadsheet=url ,worksheet = _worksheet, usecols=list(range(8)),ttl=5)
    data = data.dropna(how="all")
    data = data.drop(data.index[rowIndex])
    conn.update(spreadsheet=url,worksheet=_worksheet,data=data)

#################################################################################################
#Function for getting data from Clipboard
def parse_operator_message(text):

    # Extract date (dd-mm-yyyy)
    date_match = re.search(r"Date[:\s]+(\d{1,2}-\d{1,2}-\d{4})", text)
    date_value = datetime.strptime(date_match.group(1), "%d-%m-%Y") if date_match else None

    # Extract tank level in cm
    level_match = re.search(r"Tank Level\(cm\)[:\s]+([\d\.]+)", text)
    level_value = float(level_match.group(1)) if level_match else None

    # Extract flow rate (L/d)
    flow_rate_match = re.search(r"Flow Rate\(L/d\)[:\s]+([\d\.]+)", text)
    flow_rate_value = float(flow_rate_match.group(1)) if flow_rate_match else None

    # Extract total flow (bbl)
    total_flow_match = re.search(r"Total Flow\s*[:\s]+([\d\.]+)", text)
    total_flow_value = float(total_flow_match.group(1)) if total_flow_match else None

    # Return as a dictionary
    return {
        "Date": date_value,
        "Tank_Level_cm": level_value,
        "Flow_Rate_Ld": flow_rate_value,
        "Total_Flow_bbl": total_flow_value
    }


st.set_page_config(layout="wide")

def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        # Load credentials from secrets.toml
        credentials = st.secrets["credentials"]

        if username in credentials and credentials[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"Welcome, {username}!")
            main_app()
        else:
            st.error("Invalid username or password")

#Display title and Description 
def retm_readings():
    st.title("RETM Monitoring sheet")
    st.markdown("Updating daily readings and give insghits")
    #My Excel Sheet headers
    col1 = "Date"
    col2 = "Total Injection"
    col3 = "Flow Meter"
    col4 = "Tank Level"
    col5 = "Volume in Tank"
    col6 = "Export"
    col7 = "Req Dosage"
    col8 = "Inj Dosage"

    tab1 , tab2 , tab3 = st.tabs(["RETM Readings","RETM Graphs","Editing Data"])

    yesterday_level = data["Tank Level"].iloc[-1]
    yesterday_vol = data[col5].iloc[-1]

    with tab1:
        with st.form("user_form"):
            today_date = st.date_input("Enter the date")
            yesterday = st.number_input("Yesterday level , cm ",value= yesterday_level)
            yester_voll = st.number_input("Yesterday Tank Volume (L)", value=yesterday_vol)
            level = st.number_input("Today Level , cm")
            export = st.number_input("Export , bbl")
            req_dosage = st.number_input("Required Dosage , ppm")
            get_clipboard = st.form_submit_button("Copy from clipboard")
            calculate = st.form_submit_button("Calculate")
            submit = st.form_submit_button("Submit")

        if get_clipboard:
            raw_text = parse_operator_message(pyperclip.paste())
            dada = pd.DataFrame([raw_text])
            st_data = dada["Date"]
            st_level = dada["Tank_Level_cm"].iloc[-1]
            st_export = dada["Total_Flow_bbl"].iloc[-1]

            st.number_input("Level is :",value=st_level)
            st.number_input("Export is :",value=st_export)

          

        if submit:
            
            #Performing Calculations
            datenow = today_date -timedelta(days=1)
            total_injected = "{:.2f}".format((yesterday-level)*38)
            inj_dosage = "{:.2f}".format((float(total_injected)/(export*0.159))*1000)
            flowmeter =  "{:.2f}".format(float(total_injected)- float(random.uniform(1,3)))
            today_vol = "{:.2f}".format(float(yester_voll)-float(total_injected))

            if not level or not export or not req_dosage:
                st.warning("Please enter all required field before calculate")
                st.stop()
            elif data[col1].str.contains(datenow.strftime("%m/%d/%Y")).any():
                st.warning("The Data already inserted")
                st.stop()
            else:
                new_data = pd.DataFrame([{
                    col1 : datenow.strftime("%m/%d/%Y"),
                    col2 : total_injected,
                    col3 : flowmeter, 
                    col4 : level,
                    col5 : today_vol,
                    col6 : export,
                    col7 : req_dosage,
                    col8 : inj_dosage
                }])
            
            update_data(url,"RETM",data,new_data)
        
        if calculate:
            
            #Performing Calculations
            datenow = today_date -timedelta(days=1)
            total_injected = "{:.2f}".format((yesterday-level)*38)
            inj_dosage = "{:.2f}".format((float(total_injected)/(export*0.159))*1000)
            flowmeter =  "{:.2f}".format(float(total_injected)- float(random.uniform(1,3)))
            today_vol = "{:.2f}".format(float(yester_voll)-float(total_injected))

            if not level or not export or not req_dosage:
                st.warning("Please enter all required field before calculate")
                st.stop()

            else:
                new_data = pd.DataFrame([{
                    col1 : datenow.strftime("%Y-%m-%d"),
                    col2 : total_injected,
                    col3 : flowmeter, 
                    col4 : level,
                    col5 : today_vol,
                    col6 : export,
                    col7 : req_dosage,
                    col8 : inj_dosage
                }])

                average = pd.to_numeric(data[col2].mean(),errors='coerce')

                remaing_days = pd.to_numeric((float(today_vol)-2000)/average,errors= 'coerce')
                remaing_days = "{:.1f}".format(float(remaing_days))
                data_strr = (f"RETM: {datenow} \n"
                            "\n"
                f"Total Injection : {total_injected} L/d \n"
                f"Flowmeter : {flowmeter} L/d \n"
                f"Tank Level : {level} cm \n"
                f"Volume in Tank: {today_vol} L \n"
                f"Export : {export} bbl \n"
                "\n"
                f"Required Dosage : {req_dosage} ppm \n"
                f"Injected Dosage : {inj_dosage} \n"
                f"Next Decanting : {remaing_days} days")

                st.code(data_strr)
    with tab2:
        st.markdown("Actual Dosage Vs Required Dosage (PPM)")


        data['Date'] = pd.to_datetime(data['Date'], errors= 'coerce')
        data['date_str'] = data['Date'].dt.strftime('%Y-%m-%d')

        fig_tankLevel = px.line(data, x= "date_str" , 
                                y = col4,
                                template= "gridon" ,
                                title= "Tank Level (CM)")
        fig_tankLevel.update_xaxes(type='category' , title_text = "Date")
        ########################################################################
        fig_tankVol=  px.line(data, x= "date_str" , 
                                y = col5,
                                template= "gridon" ,
                                title= "Tank Volume (Liters)")
        fig_tankVol.update_xaxes(type='category' , title_text = "Date")
        ########################################################################
        fig_actualDosage = px.line(data,x = "date_str", y = col8,
                                    template= "gridon" ,
                                    title= "Actual Dosage Vs Target (PPM)")
        fig_actualDosage.update_xaxes(type='category' , title_text = "Date")

        st.plotly_chart(fig_tankVol,use_container_width=True)
        st.plotly_chart(fig_tankLevel,use_container_width=True)
        st.plotly_chart(fig_actualDosage,use_container_width=True)


    with tab3:
       with st.form("Editing Data"):
                st.subheader("Select the Row you need to delete")
                selected_row = st.selectbox("Select data",connect_gsheet(url,"RETM").index +2)
                btn_deleteRow = st.form_submit_button("Delete Selected Row")
                if btn_deleteRow:
                    delete_row(url,"RETM",selected_row-2)
                    st.progress(100,"Deleteing..")
                    st.success(f"Deleted Row {selected_row}")
####################################################################################
def plot_gauge(_worksheet,gauge_title):
        l = percentage_level(connect_gsheet(url,_worksheet),"Volume in Tank")
        l = format(l)
        fig = go.Figure(go.Indicator(
             mode = "gauge+number",
             value = float(l),
             domain = {'x': [0, 1], 'y': [0, 1]},
             title = {'text': gauge_title},
              gauge = {
             "axis": {"range": [0, 100]}  # 👈 Set gauge range here
                        }
        ))
        st.plotly_chart(fig,use_container_width=True)
######################################################################################
def dashboard_page():
     col1,  col2, col3 = st.columns([1,1,1])
     with col1:
        plot_gauge("RETM","RETM Tank Level %")
     with col2:
        plot_gauge("36 KPS1","36 KPS1 Tank Level %")
     with col3:
        plot_gauge("24 KPS1","24 KPS1 Tank Level")
    
     st.selectbox("Select Chart to show",
                 ["RETM Level (L)","RETM Total Injection","RETM"])
########################################################################################
def kps1_36():
        #Google Sheet Headers
        col1 = "Date"
        col2 = "Total Injection"
        col3 = "Flow Meter"
        col4 = "Tank Level"
        col5 = "Volume in Tank"
        col6 = "Export"
        col7 = "Req Dosage"
        col8 = "Inj Dosage"

        data_kps1 = connect_gsheet(url,"36 KPS1")
        lvl_yesterday = data_kps1["Tank Level"].iloc[-1]
        volume_yesterday = data_kps1["Volume in Tank"].iloc[-1]
        form1 = st.form("form1")
        with form1:
            kps1_date = st.date_input("Select Date:")
            kps1_yesterday_level = st.number_input("Yesterday Level , cm:",value=lvl_yesterday)
            kps1_yesterday_volume = st.number_input("Yesterday Volume, L:",value=volume_yesterday)
            kps1_today_level = st.number_input("Enter Today Level: , cm")
            kps1_export = st.number_input("Enter  Total Export (36\" inch) , bbl:")
            kps1_target = st.number_input("Enter Dosage Target (36\" inch) ,ppm:")
            kps1_flowsource1 = st.checkbox("Kar (Khurmala)")
            kps1_flowsource2 = st.checkbox("KPS0 (NOC)")
            kps1_flowsource3 = st.checkbox("TTOPCO")

            kps1_btn_calculate = st.form_submit_button("Calculate")
            #Code for Calculate Button
            if kps1_btn_calculate:
                #Performing Calculations
                if not kps1_date or not kps1_yesterday_level or not kps1_yesterday_volume or not kps1_today_level or not kps1_export or not kps1_target:
                    st.warning("Please enter all required fields!!")
                    st.stop()
                else:
                    datenow = kps1_date -timedelta(days=1)
                    total_injected = ((kps1_yesterday_level-kps1_today_level)*38)
                    inj_dosage = ((float(total_injected)/(kps1_export*0.159))*1000)
                    flowmeter =  (float(total_injected)- float(random.uniform(1,3)))
                    today_vol = (float(kps1_yesterday_volume)-float(total_injected))
                    
                    src1 = "Kar (Khurmala)" if kps1_flowsource1 else ""
                    src2 = "KPS0 (NOC)" if kps1_flowsource2 else ""
                    src3 = "TTOPCO" if kps1_flowsource3 else ""
                    data_strr = (f"36\" KPS1: {datenow} \n"
                            "\n"
                f"Total Injection : {total_injected} L/d \n"
                f"Flowmeter : {format(flowmeter)} L/d \n"
                f"Tank Level : {kps1_today_level} cm \n"
                f"Volume in Tank: {today_vol} L \n"
                f"Export : {kps1_export} bbl \n"
                "\n"
                f"Required Dosage : {kps1_target} ppm \n"
                f"Injected Dosage : {format(inj_dosage)} \n"
                f"Croude Oil Soruces: \n"
                f"{src1}\n"
                f"{src2}\n"
                f"{src3}\n") # f"Next Decanting : {remaing_days} days

                st.code(data_strr)

            kps1_btn_submit = st.form_submit_button("Submit")
            #Code for Submit Button
            if kps1_btn_submit:
                 datenow = kps1_date -timedelta(days=1)
                 if not kps1_date or not kps1_yesterday_level or not kps1_yesterday_volume or not kps1_today_level or not kps1_export or not kps1_target:
                    st.warning("Please enter all required fields!!")
                 elif data_kps1[col1].str.contains(datenow.strftime("%m/%d/%Y")).any():
                     st.warning("Data already inserted!!")
                 else:
                    datenow = kps1_date -timedelta(days=1)
                    total_injected = ((kps1_yesterday_level-kps1_today_level)*38)
                    inj_dosage = ((float(total_injected)/(kps1_export*0.159))*1000)
                    flowmeter =  (float(total_injected)- float(random.uniform(1,3)))
                    today_vol = (float(kps1_yesterday_volume)-float(total_injected))
                    
                    new_data = pd.DataFrame([{
                    col1 : datenow.strftime("%m/%d/%Y"),
                    col2 : format(total_injected),
                    col3 : format(flowmeter), 
                    col4 : kps1_today_level,
                    col5 : format(today_vol),
                    col6 : kps1_export,
                    col7 : kps1_target,
                    col8 : format(inj_dosage)
                }])
                    update_data(url,"36 KPS1",data_kps1,new_data)
def kps1_24():
        #Google Sheet Headers
        col1 = "Date"
        col2 = "Total Injection"
        col3 = "Flow Meter"
        col4 = "Tank Level"
        col5 = "Volume in Tank"
        col6 = "Export"
        col7 = "Req Dosage"
        col8 = "Inj Dosage"

        data_kps1= connect_gsheet(url,"24 KPS1")
        lvl_yesterday = data_kps1["Tank Level"].iloc[-1]
        volume_yesterday = data_kps1["Volume in Tank"].iloc[-1]
        form2 = st.form("form2")
        with form2:
            kps1_date = st.date_input("Select Date:")
            kps1_yesterday_level = st.number_input("Yesterday Level , cm:",value=lvl_yesterday)
            kps1_yesterday_volume = st.number_input("Yesterday Volume, L:",value=volume_yesterday)
            kps1_today_level = st.number_input("Enter Today Level: , cm")
            kps1_export = st.number_input("Enter  Total Export (24\" inch) , bbl:")
            kps1_target = st.number_input("Enter Dosage Target (24\" inch) ,ppm:")
            kps1_flowsource1 = st.checkbox("Kar (Khurmala)")
            kps1_flowsource2 = st.checkbox("KPS0 (NOC)")
            kps1_flowsource3 = st.checkbox("TTOPCO")

            kps1_btn_calculate = st.form_submit_button("Calculate")
            #Code for Calculate Button
            if kps1_btn_calculate:
                #Performing Calculations
                if not kps1_date or not kps1_yesterday_level or not kps1_yesterday_volume or not kps1_today_level or not kps1_export or not kps1_target:
                    st.warning("Please enter all required fields!!")
                    st.stop()
                else:
                    datenow = kps1_date -timedelta(days=1)
                    total_injected = ((kps1_yesterday_level-kps1_today_level)*38)
                    inj_dosage = ((float(total_injected)/(kps1_export*0.159))*1000)
                    flowmeter =  (float(total_injected)- float(random.uniform(1,3)))
                    today_vol = (float(kps1_yesterday_volume)-float(total_injected))
                    
                    src1 = "Kar (Khurmala)" if kps1_flowsource1 else ""
                    src2 = "KPS0 (NOC)" if kps1_flowsource2 else ""
                    src3 = "TTOPCO" if kps1_flowsource3 else ""
                    data_strr = (f"24\" KPS1: {datenow} \n"
                            "\n"
                f"Total Injection : {total_injected} L/d \n"
                f"Flowmeter : {format(flowmeter)} L/d \n"
                f"Tank Level : {kps1_today_level} cm \n"
                f"Volume in Tank: {today_vol} L \n"
                f"Export : {kps1_export} bbl \n"
                "\n"
                f"Required Dosage : {kps1_target} ppm \n"
                f"Injected Dosage : {format(inj_dosage)} \n"
                f"Croude Oil Soruces: \n"
                f"{src1}\n"
                f"{src2}\n"
                f"{src3}\n") # f"Next Decanting : {remaing_days} days

                st.code(data_strr)

            kps1_btn_submit = st.form_submit_button("Submit")
            #Code for Submit Button
            if kps1_btn_submit:
                 datenow = kps1_date -timedelta(days=1)
                 if not kps1_date or not kps1_yesterday_level or not kps1_yesterday_volume or not kps1_today_level or not kps1_export or not kps1_target:
                    st.warning("Please enter all required fields!!")
                 elif data_kps1[col1].str.contains(datenow.strftime("%m/%d/%Y")).any():
                     st.warning("Data already inserted!!")
                 else:
                    datenow = kps1_date -timedelta(days=1)
                    total_injected = ((kps1_yesterday_level-kps1_today_level)*38)
                    inj_dosage = ((float(total_injected)/(kps1_export*0.159))*1000)
                    flowmeter =  (float(total_injected)- float(random.uniform(1,3)))
                    today_vol = (float(kps1_yesterday_volume)-float(total_injected))
                    
                    new_data = pd.DataFrame([{
                    col1 : datenow.strftime("%m/%d/%Y"),
                    col2 : format(total_injected),
                    col3 : format(flowmeter), 
                    col4 : kps1_today_level,
                    col5 : format(today_vol),
                    col6 : kps1_export,
                    col7 : kps1_target,
                    col8 : format(inj_dosage)
                }])
                    update_data(url,"24 KPS1",data_kps1,new_data)
def kps1_readings():
   

    st.subheader("KPS1 Readings Update")
    kps1_tab1,kps1_tab2 = st.tabs(["36 Readings Update","24 Readings Updates"])
    
    with kps1_tab1:
       kps1_36()

    with kps1_tab2:
        kps1_24()

########################################################################################
def main_app():
    page = st.sidebar.radio("Naviagation",["Dashboard","RETM Readings Update","KPS1 Readings Update"])

    if page == "Dashboard":
        dashboard_page()
    if page =="RETM Readings Update":
         retm_readings()
    if page == "KPS1 Readings Update":
        kps1_readings()
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login()
else:
    main_app()

def plot_lineChart(_data , _title):
    print("Hello world")





