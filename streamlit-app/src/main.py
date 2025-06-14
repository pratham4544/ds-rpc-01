import streamlit as st
# from streamlit_extras.switch_page_button import switch_page

# Sample data for account profiles
profiles = [
    {
        "logo": "https://via.placeholder.com/100",
        "department": "Engineering",
        "name": "Alice Johnson"
    },
    {
        "logo": "https://via.placeholder.com/100",
        "department": "Marketing",
        "name": "Bob Smith"
    },
    {
        "logo": "https://via.placeholder.com/100",
        "department": "Finance",
        "name": "Charlie Brown"
    },
    {
        "logo": "https://via.placeholder.com/100",
        "department": "HR",
        "name": "Diana Prince"
    },
    {
        "logo": "https://via.placeholder.com/100",
        "department": "Sales",
        "name": "Ethan Hunt"
    }
]

# Initialize session state for department information
if 'selected_department' not in st.session_state:
    st.session_state.selected_department = None

st.title("Account Profiles")

# Display account profiles
for profile in profiles:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(profile["logo"], width=100)
    with col2:
        st.subheader(profile["name"])
        st.write(f"Department: {profile['department']}")
        if st.button(f"Select {profile['name']}", key=profile['name']):
            st.session_state.selected_department = profile['department']

# Display selected department
if st.session_state.selected_department:
    st.success(f"You have selected the {st.session_state.selected_department} department.")
    if st.button("Go to Chatbot"):
        st.switch_page('pages/chatbot.py')
        # switch_page("chatbot")