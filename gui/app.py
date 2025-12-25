import streamlit as st
import pandas as pd
import numpy as np

st.title('Code Assessment Dashboard')

repo_url = st.text_input("Github Repository", key="repo_url", placeholder="Enter the GitHub repository  here")
load_button = st.button("Load Repository")

if load_button and repo_url:
    st.write(f"Loading repository from {repo_url}")

st.divider()
with st.chat_message("user"):
    st.write()


prompt = st.chat_input(placeholder="Say Something",
              accept_file= True,
              file_type= ["py", "java", "cpp"],
              on_submit = None,
              args = None
              )


if prompt and prompt.text:
    st.markdown(prompt.text)
if prompt and prompt["files"]:
    st.image(prompt["files"][0])
