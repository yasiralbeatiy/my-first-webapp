import streamlit as st 
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import plotly.express as px
import plotly.graph_objects as go 
from datetime import timedelta

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

# --- Main app ---



#Display title and Description 
def retm_readings():
    st.title("RETM Monitoring sheet")
    st.markdown("Updating daily readings and give insghits")

    url = "https://docs.google.com/spreadsheets/d/1E6XfwNLvw8m8oj2lVtglxvyC3edI70qIQOQKFmSYXcc"

    #My Excel Sheet headers
    col1 = "Date"
    col2 = "Total Injection"
    col3 = "Flow Meter"
    col4 = "Tank Level"
    col5 = "Volume in Tank"
    col6 = "Export"
    col7 = "Req Dosage"
    col8 = "Inj Dosage"

    tab1 , tab2 = st.tabs(["RETM Readings","RETM Graphs"])

    #Establish connection to google sheet
    conn = st.connection("gsheets", type=GSheetsConnection)

    #Fetch the data to
    data = conn.read(spreadsheet=url ,worksheet = "RETM", usecols=list(range(8)),ttl=5)
    data = data.dropna(how="all")

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
            calculate = st.form_submit_button("Calculate")
            submit = st.form_submit_button("Submit")

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
            elif data[col1].str.contains(datenow.strftime("%Y-%m-%d")).any():
                st.warning("The Data already inserted")
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

            updated_df = pd.concat([data,new_data],ignore_index=True)
            conn.update(spreadsheet=url ,worksheet = "RETM",data=updated_df)
            st.success("Data Updated Successfully!")
        
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
            elif data[col1].str.contains(datenow.strftime("%Y-%m-%d")).any():
                st.warning("The Data already inserted")
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

def main_app():
    st.title(f"Welcome {st.session_state['username']} 👋")
    st.write("This is your protected content.")

    retm_readings()
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login()
else:
    main_app()