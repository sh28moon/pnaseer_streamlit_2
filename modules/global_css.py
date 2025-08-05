# pages/global_css.py

GLOBAL_CSS = """
:root {
  --font-small:       0.75rem;
  --font-medium:      1.5rem;
  --font-large:       2.5rem;
  --import-box-width: 500px;
  --tab-text-size:    1.5rem;
  --button-text-size: 0.2rem;
  --sidebar-selectbox-width: 120px;
  --sidebar-button-width: 180px;
  --sidebar-create-job-width: 80px;
  --sidebar-notification-width: 80px;
}

/* Utility font classes */
.font-small  { font-size: var(--font-small)  !important; }
.font-medium { font-size: var(--font-medium) !important; }
.font-large  { font-size: var(--font-large)  !important; }

/* File uploader width control */
div[data-testid="stFileUploader"] {
  width: var(--import-box-width) !important;
}

div[data-testid="stFileUploader"] > label {
  width: var(--import-box-width) !important;
}

div[data-testid="stFileUploader"] > label > div {
  width: var(--import-box-width) !important;
}

/* Tab text size control */
div[data-testid="stTabs"] button[role="tab"] {
  font-size: var(--tab-text-size) !important;
}

div[data-testid="stTabs"] button[role="tab"] > div {
  font-size: var(--tab-text-size) !important;
}

/* Reset regular buttons to normal size */
button:not([role="tab"]) {
  font-size: var(--button-text-size) !important;
}

[data-testid="stSidebar"] button {
  font-size: var(--button-text-size) !important;
}

/* Sidebar spacing reduction */
[data-testid="stSidebar"] .element-container {
  margin-bottom: 0.25rem !important;
}

[data-testid="stSidebar"] .stMarkdown {
  margin-bottom: 0.25rem !important;
}

[data-testid="stSidebar"] .stButton {
  margin-bottom: 0.25rem !important;
}

[data-testid="stSidebar"] .stSelectbox {
  margin-bottom: 0.25rem !important;
}

[data-testid="stSidebar"] .stTextInput {
  margin-bottom: 0.25rem !important;
}

/* Notification box spacing */
[data-testid="stAlert"] {
  margin-top: 0.25rem !important;
  margin-bottom: 0.25rem !important;
  padding: 0.5rem !important;
}

.stSuccess, .stWarning, .stError, .stInfo {
  margin-top: 0.25rem !important;
  margin-bottom: 0.25rem !important;
  padding: 0.5rem !important;
}

/* Status indicator spacing */
.status-indicator {
  margin-bottom: 0.1rem !important;
}

/* Sidebar width controls */
/* Job selection dropdown */
[data-testid="stSidebar"] [data-testid="stSelectbox"] {
  width: var(--sidebar-selectbox-width) !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] > div {
  width: var(--sidebar-selectbox-width) !important;
}

/* Job name text input */
[data-testid="stSidebar"] [data-testid="stTextInput"] {
  width: var(--sidebar-selectbox-width) !important;
}

[data-testid="stSidebar"] [data-testid="stTextInput"] > div {
  width: var(--sidebar-selectbox-width) !important;
}

/* Main navigation buttons */
[data-testid="stSidebar"] button {
  width: var(--sidebar-button-width) !important;
}

/* Create Job button override */
[data-testid="stSidebar"] .stColumns .stButton button {
  width: var(--sidebar-create-job-width) !important;
}

[data-testid="stSidebar"] div[data-testid="column"] button {
  width: var(--sidebar-create-job-width) !important;
}

/* Sidebar notification boxes */
[data-testid="stSidebar"] .stSuccess {
  width: var(--sidebar-notification-width) !important;
}

[data-testid="stSidebar"] .stWarning {
  width: var(--sidebar-notification-width) !important;
}

[data-testid="stSidebar"] .stError {
  width: var(--sidebar-notification-width) !important;
}

[data-testid="stSidebar"] .stInfo {
  width: var(--sidebar-notification-width) !important;
}
"""