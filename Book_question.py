# importing the necessary libraries
# If the code shows any error like package not found or xyz not installed, considering installing them with pip
# pip install streamlit pandas langchain openai pydantic
import streamlit as st
import pandas as pd
from langchain.document_loaders import PyPDFLoader
import os
from langchain_openai import OpenAI
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from typing import Annotated,List
import random

# Configuring the environment with OpenAI API key and os library.
os.environ["OPENAI_API_KEY"]="*********"

# Initializing the model with init_chat_model which is a function on langchain that we have imported
# Temperature is set to be zero to make the model more deterministic and less creative. It can be increased
# but that may require some tweaking in prompts as well.
llm = init_chat_model("gpt-4o-mini", model_provider="openai",temperature=0)

# Creating the header and a multi file uploader in the sidebar of the streamlit page
st.header("Generate Questions from Book/PDF")
st.sidebar.header("Upload Your Book in pdf format")
files = st.sidebar.file_uploader('Upload multiple files',accept_multiple_files=True)

# if files are uploaded a dictionary is created with the file names
# a selectbox is added to select the document from the uploaded files
if files:
    file_names = [file.name for file in files]
    selected_file = st.sidebar.selectbox("Select the Chapters", file_names)

# file_obj is the file that has been fetched from the uploaded documents after matching the name of the 
# selected file with the uploaded files
    if selected_file:
        file_dict = {file.name: file for file in files}
        file_obj = file_dict[selected_file]
        
# a temporary object is created for the selected file which will be later loaded as document.
        temp_path = f"temp_{selected_file}"
        with open(temp_path, "wb") as f:
            f.write(file_obj.read())
            
# The file is read with PyPDFLoader. PyPDFLoader splits the files into pages because it is mostly used
# for semantic search. Since here the requirement is to have a consolidated document to be passed as context,
# the pages has been stitched with string-join operation.
        loader = PyPDFLoader(temp_path)
        docs = loader.load()
        full_text = " ".join([page.page_content for page in docs])
        
# An input form is created on streamlit consisting of options to select the question type, set the number
# of questions and a toogle to turn on/off the answers.
with st.form(key='my_form'):
    question_type = st.selectbox(
        "Select Type of Questions:", 
        ["Short Descriptive", "Long Descriptive", "Multiple Choice", "True/False", "Word-Puzzle"]
    )
    num_questions = st.number_input("Select a number", min_value=0, max_value=25, value=10, step=1)
    include_answer = st.toggle("Include Answer")
    submit_button = st.form_submit_button(label="Submit")

# If submit_button is clicked the code gets into a sequence of if elif blocks, where each block deals with
# a different question_type.
if submit_button:

# This block is for 'Short Descriptive'. The Review class inherits from BaseModel which has been imported from Pydantic
# The Review class defines the schema and 'Annotated' from 'typing' is being used to annotate the elements of the schema.
    if question_type=='Short Descriptive':
        class Review(BaseModel):
            Serial_No : Annotated[List[int],'Serial number of the question']
            Questions: Annotated[List[str],'Question statement']
            Answer:Annotated[List[str],'Descriptive answer']

# New model is instantiated by applying the 'Review' schema over llm with the help of with_structured_output
# which is a langchain function.
        
        structured_model=llm.with_structured_output(Review)

# prompt is passed in the model to get the result object. Note that the number of question as well as the selected 
# document has been passed in the prompt
        result=structured_model.invoke(f'''Frame exactly {num_questions} question/questions with solution out of the text. 
        Questions are short descriptive e.g. for 2 marks. Note that the question should not refer to the text as students 
        does not have access to the text while answering the questions : \n {full_text}''')

# a pandas dataframe is created by extracting the features from the result.
        df=pd.DataFrame({'Serial_no':result.Serial_No, 'Question':result.Questions, 'Answer':result.Answer})

# if include_answer is toggled on, streamlit displays the dataframe
        if include_answer==True:
            st.dataframe(df,
                         hide_index=True)

# if include_answer is toggled off, streamlit displays the dataframe except the answer column.
        else:
            st.dataframe(df[['Serial_no','Question']],
                         hide_index=True)
            
# Exactly same steps for Long Descriptive, Only the prompt would be a bit different, specifying that long
# answer type questions has to be created.
    elif question_type=='Long Descriptive':
        class Review(BaseModel):
            Serial_No : Annotated[List[int],'Serial number of the question']
            Questions: Annotated[List[str],'Question statement']
            Answer:Annotated[List[str],'Descriptive answer']
        structured_model=llm.with_structured_output(Review)
        result=structured_model.invoke(f'''Frame exactly {num_questions} question/questions with solution out of the text. 
        Questions are long descriptive e.g. for 5 to 10 marks. Note that the question should not refer to the text as students 
        does not have access to the text while answering the questions : \n {full_text}''')
    
        df=pd.DataFrame({'Serial_no':result.Serial_No, 'Question':result.Questions, 'Answer':result.Answer})
        if include_answer==True:
            st.dataframe(df,
                         hide_index=True)
        else:
            st.dataframe(df[['Serial_no','Question']],
                         hide_index=True)

# For MCQ the steps would be similar. The structure would be more elaborate to incorporate all the options and correct answer.
    elif question_type=='Multiple Choice':
        class Review(BaseModel):
            Serial_No:Annotated[List[int],'Serial number of the question']
            Question: Annotated[List[str],'Question statement']
            Option_A: Annotated[List[str],'List of option A']
            Option_B: Annotated[List[str],'List of option B']
            Option_C: Annotated[List[str],'List of option C']
            Option_D: Annotated[List[str],'List of option D']
            Answer:   Annotated[List[str],"The correct option out of 'A','B','C' and 'D'"]
            Explanation: Annotated[List[str],'Explanation of the correct answer']
        structured_model=llm.with_structured_output(Review)
        result=structured_model.invoke(f'''Frame {num_questions} MCQ questions with their options and solution out of the text. 
        Append all 1st option of all the questions in Option_A.Append all 2nd option of all the questions in Option_B. 
        Append all 3rd option of all the questions in Option_C. Append all 4th option of all the questions in Option_D. 
        Questions are Multiple choice correct type. Note that the question should not refer to the text as students does not 
        have access to the text while answering the questions : \n {full_text}''')
    
        df=pd.DataFrame({'Serial_no':result.Serial_No, 'Question':result.Question,'Option A':result.Option_A,
                         'Option B':result.Option_B,'Option C':result.Option_C,'Option D':result.Option_D,
                         'Answer':result.Answer,'Explanation':result.Explanation})
        if include_answer==True:
            st.dataframe(df,
                         hide_index=True)
        else:
            st.dataframe(df[['Serial_no','Question','Option A','Option B','Option C','Option D']],
                         hide_index=True)

# For True/False the procedure is exactly the same as previous.
    elif question_type=='True/False':
        class Review(BaseModel):
            Serial_No : Annotated[List[int],'Serial number of the question']
            Question: Annotated[List[str],'Question statement']
            Answer:Annotated[List[str],'Either True or False']
        structured_model=llm.with_structured_output(Review)
        result=structured_model.invoke(f'''Frame exactly {num_questions} question/questions out of the text whose answer is either 
        True or False. Questions are short statements which can either be true or false. Note that the question should not refer 
        to the text as students does not have access to the text while answering the questions : \n {full_text}''')
    
        df=pd.DataFrame({'Serial_no':result.Serial_No, 'Question':result.Question, 'Answer':result.Answer})
        if include_answer==True:
            st.dataframe(df,
                         hide_index=True)
        else:
            st.dataframe(df[['Serial_no','Question']],
                         hide_index=True)
            
# For word-puzzle we first geneerate a list of questions with one word answer with exactly same procedure as the previous one.
    elif question_type=='Word-Puzzle':
        class Review(BaseModel):
            Serial_No : Annotated[List[int],'Serial number of the question']
            Question: Annotated[List[str],'Descriptive question statement']
            Answer:Annotated[List[str],'Answer must be of exactly one word']
            
        structured_model=llm.with_structured_output(Review)
        result=structured_model.invoke(f'''Frame {num_questions} questions out of the text. The answer should be of exactly one word 
        and should not have any special character. Note that the question should not refer to the text as students does not have 
        access to the text while answering the questions : \n {full_text}''')
        
# Define a function that takes a one word string as input and replaces all characters with '_' except two random characters
# e.g. for input 'Abhishek' it may give output as 'A _ _ i _ _ _ _ or '_ b h _ _ _ _ _' etc
        def fun(s):
            a,b=random.sample(range(0, len(s)), 2)
            list1=[]
            for i in range(len(s)):
                if i==a or i==b:
                    list1.append(s[i])
                else:
                    list1.append('_')
            return " ".join(list1)

# Construct a dataframe with the features of result, then add 'Cue' column by applying the function on Answer series
        df=pd.DataFrame({'Serial_no':result.Serial_No, 'Question':result.Question, 'Answer':result.Answer})
        df['Cue']=df['Answer'].apply(fun)

# Displaying relevant features of the dataframe, based on the toggle status of include_answer.
        if include_answer==True:
            st.dataframe(df[['Serial_no','Question','Cue','Answer']],
                         hide_index=True)
        else:
            st.dataframe(df[['Serial_no','Question','Clue']],
                         hide_index=True)
                        
