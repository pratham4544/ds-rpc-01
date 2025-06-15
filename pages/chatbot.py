from src.helper import *
import streamlit as st

# Load and process documents
# docs = load_data_path(path='resources/data')
# docs_2 = update_metadata_into_docs(docs=docs)

st.subheader('Hello, how can I help you?')

# Create vector store
# vector_store = create_and_store_vs(docs_2)

# Get the selected department from session state
selected_department = st.session_state.get('selected_department', None)

# Display selected department if available
if selected_department:
    st.info(f"Current department: {selected_department}")
else:
    st.warning("No department selected. Please go back and select a department first.")

# Chat input
prompt = st.chat_input("Say something")
if prompt:
    st.write(f"User has sent the following prompt: {prompt}")
    
    # Check if department is selected before proceeding
    if selected_department:
        response, context = answer(question=prompt, input_department=selected_department)
        
        # Display the response
        st.write(f"**Response:** {response}")
        
        # Display the context in small text
        if context:
            st.markdown("---")
            st.markdown("**Sources/Context:**")
            st.markdown(f"<small>{context}</small>", unsafe_allow_html=True)
    else:
        st.error("Please select a department first before asking questions.")