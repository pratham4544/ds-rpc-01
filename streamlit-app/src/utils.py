def load_profiles():
    profiles = [
        {
            "logo": "path/to/logo1.png",
            "department": "Engineering",
            "username": "Alice Johnson"
        },
        {
            "logo": "path/to/logo2.png",
            "department": "Marketing",
            "username": "Bob Smith"
        },
        {
            "logo": "path/to/logo3.png",
            "department": "Finance",
            "username": "Charlie Brown"
        },
        {
            "logo": "path/to/logo4.png",
            "department": "HR",
            "username": "Diana Prince"
        },
        {
            "logo": "path/to/logo5.png",
            "department": "Sales",
            "username": "Ethan Hunt"
        }
    ]
    return profiles

def get_department_info():
    return {
        "Engineering": "Responsible for product development and engineering.",
        "Marketing": "Handles marketing strategies and campaigns.",
        "Finance": "Manages financial planning and analysis.",
        "HR": "Oversees human resources and employee relations.",
        "Sales": "Focuses on sales strategies and customer relationships."
    }