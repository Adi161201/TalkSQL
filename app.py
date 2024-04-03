from dotenv import load_dotenv
load_dotenv()   ## Load all env variables from .env file

import os
import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel('gemini-pro')

def get_response(prompt, question):
    response = model.generate_content([prompt, question])
    try :
        return response.text
   
    except ValueError:
        # If the response doesn't contain text, check if the prompt was blocked.
        print(response.prompt_feedback)
        # Also check the finish reason to see if the response was blocked.
        print(response.candidates[0].finish_reason)
        # If the finish reason was SAFETY, the safety ratings have more details.
        print(response.candidates[0].safety_ratings)

    return None

def execute_sql_from_file(file_content):
    conn = sqlite3.connect('my_db.db')  # Create or connect to SQLite database
    cursor = conn.cursor()
    
    # Execute all statements in the file
    cursor.executescript(file_content)
    st.success("SQL statements executed successfully.")
    conn.commit()
    conn.close()

def extract_table_info_from_db(db_path):
    with st.spinner('Extracting table information...'):
        conn = sqlite3.connect(db_path)  # Connect to the database
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {}

        table_info_text = ""
        for table_name in cursor.fetchall():
            table_name = table_name[0]  # Extract table name from tuple
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [row[1] for row in cursor.fetchall()]  # Extract column names
            tables[table_name] = columns
            table_info_text += f"Table Name: {table_name}, Columns in {table_name}: {', '.join(columns)} | \n"

        # print(table_info_text)
        
        if not tables:
            return "No tables found in the connected database."

        return table_info_text



st.title("TalkSQL: Your Data Speaks Your Language")
st.subheader("Text to SQL webapp")

uploaded_file = st.file_uploader("Upload SQL file containing tables and data", type="sql")



str1 = "You are an expert in converting English questions to SQL query! I am providing you the details of tables along with their column names.\n"
str3 = '''For example,\nExample 1 - How many entries of records are present?, 
the SQL command will be something like this SELECT COUNT(*) FROM STUDENT;
\nExample 2 - Tell me all the students studying in Data Science class?, 
the SQL command will be something like this SELECT * FROM STUDENT WHERE CLASS="Data Science";
Also, the sql code should not have ```sql in the beginning or end and sql word in output . '''

prompt = ""

if uploaded_file:
    file_contents = uploaded_file.read().decode("utf-8")
    execute_sql_from_file(file_contents)
    str2 = extract_table_info_from_db('my_db.db')
    prompt += str1 + str2 + str3 


input_query = st.text_input("Input Query:", key="input")
if st.button("Execute SQL"):
    if uploaded_file:
        try:
            with st.spinner('Processing...'):

                print(prompt)
                response = get_response(prompt, input_query)  # (prompt, question)
                print(response)
                st.text(response)
                
                conn = sqlite3.connect('my_db.db')
                cursor = conn.cursor()
                cursor.execute(response)
                result = cursor.fetchall()
                df = pd.DataFrame(result, columns=[desc[0] for desc in cursor.description])
                st.write(df)
                conn.close()
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("No File Uploaded")
