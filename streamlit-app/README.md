# Streamlit Account Profiles and Chatbot Application

This project is a Streamlit application that displays account profiles and includes a chatbot feature for user inquiries. The application is structured to facilitate easy navigation and interaction.

## Project Structure

```
streamlit-app
├── pages
│   └── chatbot.py        # Chatbot application for user inquiries
├── src
│   ├── main.py           # Entry point of the Streamlit application
│   └── utils.py          # Utility functions for the application
├── requirements.txt       # List of dependencies
└── README.md              # Project documentation
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd streamlit-app
   ```

2. **Install Dependencies**
   It is recommended to create a virtual environment before installing the dependencies.
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   To start the Streamlit application, run:
   ```bash
   streamlit run src/main.py
   ```

## Usage

- The main page displays five account profiles, including profile logos, department names, and user names.
- Users can navigate to the chatbot page to ask questions and receive answers based on the loaded documents.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.