import streamlit as st

# Sample data for account profiles
profiles = [
    {
        "logo": "resources/assets/engineering.png",
        "department": "engineering",
        "name": "Alice Johnson"
    },
    {
        "logo": "resources/assets/influencer.png",
        "department": "marketing",
        "name": "Bob Smith"
    },
    {
        "logo": "resources/assets/loan.png",
        "department": "finance",
        "name": "Charlie Brown"
    },
    {
        "logo": "resources/assets/human-resources.png",
        "department": "hr",
        "name": "Diana Prince"
    },
    {
        "logo": "resources/assets/office.png",
        "department": "general",
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
        st.switch_page("pages/chatbot.py")