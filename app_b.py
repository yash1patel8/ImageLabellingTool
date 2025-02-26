import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from PIL import Image
import os


from google.cloud import firestore
from google.auth.exceptions import DefaultCredentialsError
print(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
try:
    # Attempt to fetch data from Firestore
    user_ref = db.collection('users').document('user_id')
    user = user_ref.get()
    print(user.to_dict())
except DefaultCredentialsError as e:
    print(f"Credentials error: {e}")
except Exception as e:
    print(f"Error occurred: {e}")

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate("/home/ec2-user/ImageLabellingTool/key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Custom CSS for styling
st.markdown(
    """
    <style>
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
        font-size: 16px;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .stTextInput input {
        border-radius: 5px;
        padding: 10px;
    }
    .stSelectbox select {
        border-radius: 5px;
        padding: 10px;
    }
    .stRadio label {
        font-size: 16px;
    }
    .stCheckbox label {
        font-size: 16px;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #4CAF50;
    }
    .stSidebar .sidebar-content {
        background-color: #f0f2f6;
        padding: 20px;
    }
    .stSidebar img {
        max-width: 100%;
        border-radius: 10px;
    }
    .stMarkdown p {
        font-size: 16px;
        line-height: 1.6;
    }
    .bordered-section {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def user_signup():
    st.subheader("Create New Account 🆕")
    with st.container():
        st.markdown('<div class="bordered-section">', unsafe_allow_html=True)
        new_name = st.text_input("Name", placeholder="Enter your name")
        new_email = st.text_input("Email", placeholder="Enter your email")
        new_university = st.text_input("University Name", placeholder="Enter your university name")
        new_user = st.text_input("Username", placeholder="Enter your username")
        new_password = st.text_input("Password", type='password', placeholder="Enter your password")

        if st.button("Sign Up 🚀", key="signup_button"):
            user_ref = db.collection('users').document(new_user)
            user_ref.set({
                'name': new_name,
                'email': new_email,
                'university': new_university,
                'username': new_user,
                'password': new_password
            })
            st.success("You have successfully created a valid Account ✅")
            st.info("Go to Login Menu to login 🔑")
            st.session_state['current_page'] = "Login 🔑"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def user_login():
    st.subheader("Login Section 🔑")
    with st.container():
        st.markdown('<div class="bordered-section">', unsafe_allow_html=True)
        username = st.text_input("User Name", placeholder="Enter your username")
        password = st.text_input("Password", type='password', placeholder="Enter your password", key='login_password')

        if st.button("Login 🚪", key="login_button"):
            user_ref = db.collection('users').document(username)
            user = user_ref.get()
            if user.exists:
                user_data = user.to_dict()
                if password == user_data['password']:
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = username
                    st.success(f"Logged In as {username} ✅")
                    st.session_state['current_page'] = "Project Selection 📂"
                    st.rerun()
                else:
                    st.warning("Incorrect Password ❌")
            else:
                st.warning("User not found ❌")
        st.markdown('</div>', unsafe_allow_html=True)

def project_selection():
    st.subheader("Project Selection 📂")
    with st.container():
        st.markdown('<div class="bordered-section">', unsafe_allow_html=True)
        
        # Get user's existing projects
        projects_ref = db.collection('projects').where('user_id', '==', st.session_state['user_id']).stream()
        existing_projects = [doc.to_dict()['project_name'] for doc in projects_ref]
        
        # Project selection
        project_type = st.radio("Choose project type:", ["New Project ➕", "Existing Project 📁"])
        
        if project_type == "New Project ➕":
            new_project_name = st.text_input("Enter new project name:", 
                                   placeholder="e.g., Road Survey 2024")
            if st.button("Create Project 📁", key="create_project_button"):
                if new_project_name:
                    # Check if project name already exists for this user
                    existing_project = db.collection('projects').document(f"{st.session_state['user_id']}_{new_project_name}").get()
                    
                    if existing_project.exists:
                        st.error("A project with this name already exists. Please choose a different name.")
                    else:
                        # Create new project with custom document ID
                        project_ref = db.collection('projects').document(f"{st.session_state['user_id']}_{new_project_name}")
                        project_ref.set({
                            'user_id': st.session_state['user_id'],
                            'project_name': new_project_name,
                            'created_at': firestore.SERVER_TIMESTAMP
                        })
                        st.session_state['current_project'] = new_project_name
                        st.session_state['current_page'] = "Classify Images 🖼️"
                        st.success(f"Project '{new_project_name}' created successfully! ✅")
                        st.rerun()
                else:
                    st.warning("Please enter a project name")
                    
        else:
            if existing_projects:
                selected_project = st.selectbox("Select existing project:", existing_projects)
                if st.button("Open Project 📂", key="open_project_button"):
                    st.session_state['current_project'] = selected_project
                    st.session_state['current_page'] = "View All Classifications 📊"
                    st.rerun()
            else:
                st.info("No existing projects found. Create a new project to get started!")
        
        st.markdown('</div>', unsafe_allow_html=True)

def classify_image(user_id):
    st.subheader("Classify Images 🖼️")
    with st.container():
        st.markdown('<div class="bordered-section">', unsafe_allow_html=True)
        
        # File uploader for images
        uploaded_files = st.file_uploader(
            "Choose images for classification", 
            accept_multiple_files=True,
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp']
        )
        
        if not uploaded_files:
            st.warning("Please upload some images to continue")
            return
            
        # Create a selectbox with the uploaded files
        file_names = [file.name for file in uploaded_files]
        selected_image_name = st.selectbox("Select an image to classify", file_names, key='selected_image')
        
        # Find the selected file object
        selected_file = next(file for file in uploaded_files if file.name == selected_image_name)
        
        # Display the selected image
        image = Image.open(selected_file)
        st.image(image, caption=selected_image_name, use_container_width=True)

        # Reset classification inputs when image changes
        if 'prev_selected_image' not in st.session_state or st.session_state['prev_selected_image'] != selected_image_name:
            st.session_state['road_condition'] = "Good"
            st.session_state['lane_marking'] = False
            st.session_state['shadow'] = False
            st.session_state['micro_cracks'] = False
            st.session_state['obstacles'] = False
            st.session_state['unclear'] = False
            st.session_state['no_cracks'] = False
            st.session_state['clear'] = False
            st.session_state['potholes'] = False
            st.session_state['large_cracking'] = False
            st.session_state['multiple_cracks'] = False
            st.session_state['prev_selected_image'] = selected_image_name

        st.markdown("#### Road Condition 🛣️")
        road_conditions = ["Good", "Bad", "Unclear"]
        if 'road_condition' not in st.session_state:
            st.session_state['road_condition'] = road_conditions[0]
        road_condition = st.radio("Select road condition", road_conditions, key='road_condition')

        st.markdown("### Features 🛠️")
        col1, col2, col3 = st.columns(3)
        with col1:
            lane_marking = st.checkbox("Lane Marking 🚦", key='lane_marking', value=st.session_state.get('lane_marking', False))
            shadow = st.checkbox("Shadow 🌑", key='shadow', value=st.session_state.get('shadow', False))
            micro_cracks = st.checkbox("Micro Cracks 🕳️", key='micro_cracks', value=st.session_state.get('micro_cracks', False))
        with col2:
            obstacles = st.checkbox("Obstacles 🚧", key='obstacles', value=st.session_state.get('obstacles', False))
            unclear = st.checkbox("Unclear ❓", key='unclear', value=st.session_state.get('unclear', False))
            no_cracks = st.checkbox("No Cracks ✅", key='no_cracks', value=st.session_state.get('no_cracks', False))
        with col3:
            clear = st.checkbox("Clear 🌟", key='clear', value=st.session_state.get('clear', False))
            potholes = st.checkbox("Potholes 🕳️", key='potholes', value=st.session_state.get('potholes', False))
            large_cracking = st.checkbox("Large Cracking 🚨", key='large_cracking', value=st.session_state.get('large_cracking', False))
            multiple_cracks = st.checkbox("Multiple Cracks 🚨", key='multiple_cracks', value=st.session_state.get('multiple_cracks', False))

        if st.button("Submit 📤", key="submit_classification_button"):
            classification_ref = db.collection('classifications').document(f"{user_id}:{selected_image_name}")
            classification_ref.set({
                'user_id': user_id,
                'project_name': st.session_state['current_project'],
                'image_name': selected_image_name,
                'road_condition': road_condition,
                'lane_marking': lane_marking,
                'shadow': shadow,
                'micro_cracks': micro_cracks,
                'obstacles': obstacles,
                'unclear': unclear,
                'no_cracks': no_cracks,
                'clear': clear,
                'potholes': potholes,
                'large_cracking': large_cracking,
                'multiple_cracks': multiple_cracks
            })
            st.success("Classification data stored successfully! ✅")
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Log Out 🔒", key="logout_button_classify"):
            st.session_state['logged_in'] = False
            st.session_state['user_id'] = None
            st.session_state['current_page'] = "Login 🔑"
            st.rerun()

def view_all_classifications():
    st.subheader(f"View Classifications for Project: {st.session_state['current_project']} 📊")
    with st.container():
        st.markdown('<div class="bordered-section">', unsafe_allow_html=True)
        
        # Query classifications for current project
        classifications_ref = db.collection('classifications')
        query = classifications_ref.where('user_id', '==', st.session_state['user_id'])\
                                 .where('project_name', '==', st.session_state['current_project'])\
                                 .get()
        
        if not query:
            st.info("No classifications found for this project.")
        else:
            for doc in query:
                data = doc.to_dict()
                st.write(f"Image: {data['image_name']}")
                st.write(f"Road Condition: {data['road_condition']}")
                st.write("Features:")
                features = [k for k, v in data.items() if v == True and k not in 
                          ['user_id', 'image_name', 'road_condition', 'project_name']]
                st.write(", ".join(features))
                st.markdown("---")
        
        # Add button to start new classification
        if st.button("Add New Classification ➕", key="add_new_classification_button"):
            st.session_state['current_page'] = "Classify Images 🖼️"
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

def homepage():
    st.markdown("# Pothole Detection App 🕳️🚗")
    st.markdown("---")
    with st.container():
        st.markdown('<div class="bordered-section">', unsafe_allow_html=True)
        st.markdown("## About the Tool")
        st.markdown("""
            This tool helps you detect and classify road conditions, including potholes, cracks, and other obstacles. 
            It uses image analysis to provide insights into road quality and helps in maintaining safer roads.
        """)

        st.markdown("## Key Features")
        st.markdown("""
            - **Image Upload & Analysis:** Upload images of roads to detect potholes and cracks.
            - **Road Condition Classification:** Classify roads as Good, Bad, or Unclear.
            - **Feature Detection:** Identify lane markings, shadows, obstacles, and more.
            - **User Authentication:** Secure login and sign-up system.
            - **Project Management:** Create and manage multiple projects.
            - **Data Storage:** Store classification results in a database.
            - **Interactive UI:** Easy-to-use interface with visual feedback.
        """)

        st.markdown("## How to Use")
        st.markdown("""
            1. **Sign Up:** Create a new account if you don't have one.
            2. **Login:** Use your credentials to access the tool.
            3. **Create/Select Project:** Start a new project or continue an existing one.
            4. **Upload Images:** Select images from your computer.
            5. **Classify:** Analyze the road conditions and submit your findings.
        """)

        st.markdown("---")
        st.markdown("### Get Started 🚀")
        if not st.session_state.get("logged_in"):
            st.warning("Please login to access the full features of the app. 🔑")
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = None
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Home 🏠"
    if 'current_project' not in st.session_state:
        st.session_state['current_project'] = None

    st.sidebar.markdown("# Navigation 🧭")
    st.sidebar.markdown("---")

    # Modify sidebar navigation
    if st.sidebar.button("Home 🏠", key="nav_home"):
        st.session_state['current_page'] = "Home 🏠"
        st.rerun()
    if not st.session_state.get('logged_in'):
        if st.sidebar.button("Login 🔑", key="nav_login"):
            st.session_state['current_page'] = "Login 🔑"
            st.rerun()
        if st.sidebar.button("Sign Up 🆕", key="nav_signup"):
            st.session_state['current_page'] = "Sign Up 🆕"
            st.rerun()
    else:
        if st.sidebar.button("Project Selection 📂", key="nav_project"):
            st.session_state['current_page'] = "Project Selection 📂"
            st.rerun()
        if st.session_state.get('current_project'):
            if st.sidebar.button("Classify Images 🖼️", key="nav_classify"):
                st.session_state['current_page'] = "Classify Images 🖼️"
                st.rerun()
            if st.sidebar.button("View All Classifications 📊", key="nav_view"):
                st.session_state['current_page'] = "View All Classifications 📊"
                st.rerun()
        if st.sidebar.button("Log Out 🔒", key="nav_logout"):
            st.session_state['logged_in'] = False
            st.session_state['user_id'] = None
            st.session_state['current_project'] = None
            st.session_state['current_page'] = "Home 🏠"
            st.rerun()

    # Page routing
    if st.session_state['current_page'] == "Home 🏠":
        homepage()
    elif st.session_state['current_page'] == "Login 🔑":
        user_login()
    elif st.session_state['current_page'] == "Sign Up 🆕":
        user_signup()
    elif st.session_state['current_page'] == "Project Selection 📂":
        if st.session_state.get("logged_in"):
            project_selection()
        else:
            st.warning("Please login to access this section. 🔑")
    elif st.session_state['current_page'] == "Classify Images 🖼️":
        if st.session_state.get("logged_in") and st.session_state.get("current_project"):
            classify_image(st.session_state.user_id)
        else:
            st.warning("Please login and select a project to access this section. 🔑")
    elif st.session_state['current_page'] == "View All Classifications 📊":
        if st.session_state.get("logged_in") and st.session_state.get("current_project"):
            view_all_classifications()
        else:
            st.warning("Please login and select a project to access this section. 🔑")

if __name__ == "__main__":
    main()
