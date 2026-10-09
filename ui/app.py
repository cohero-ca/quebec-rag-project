import os
import sys
import re
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_cookies_controller import CookieController

FAVICON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'img', 'favicon.png'))

st.set_page_config(
    page_title="Cohero Portal", 
    page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else None, 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

cookies = CookieController()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.drive_manager import get_or_create_tenant_folder, upload_file_to_drive, list_tenant_files, delete_tenant_file

load_dotenv()
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
API_KEY = os.getenv("API_KEY", "")

LOCAL_HOST = "[http://127.0.0.1:8000](http://127.0.0.1:8000)"
API_URL = os.getenv("API_URL", f"{LOCAL_HOST}/api/rag/query")
BASE_API_URL = API_URL.rsplit('/', 1)[0]
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "hr-chatbot-tenant-vault")

ADMIN_EMAIL = "benjaminlarouch3@hotmail.com"
LOGO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'img', 'titlelogo.png'))

I18N = {
    "EN": {
        "title": "Quebec Insurance & Regulatory Assistant",
        "portal_title": "Plan Sponsor Portal",
        "portal_subtitle": "Secure access for answers about your Group Benefits",
        "login": "Sign In",
        "logout": "Logout",
        "admin_active": "Admin Privileges Active - Third-Party sources enabled.",
        "connected_as": "Connected as",
        "tenant_id": "Tenant ID",
        "sync_button": "Sync & Repair",
        "sync_tooltip_synced": "Everything is already synced",
        "sync_tooltip_unsynced": "Click to repair unindexed files",
        "upload_btn": "Upload to Secure Vault",
        "manage_hdr": "Document Vault",
        "upload_section_title": "Upload",
        "upload_section_subtitle": "Upload Group Benefits contractual documents to receive personalized answers to your questions",
        "vault_section_title": "Documents manager",
        "doc_name": "Document Name",
        "ai_status": "Indexed",
        "upload_date": "Upload Date",
        "indexed": "🟢",
        "not_indexed": "🔴",
        "delete": "Delete",
        "query_label": "Ask a question about Quebec insurance regulations or your plan documents:",
        "submit": "Submit Query",
        "answer_hdr": "Answer",
        "copy_lbl": "📋 Copy Raw Answer",
        "prev_qa_hdr": "Previous Question & Answer",
        "vault_sources_hdr": "Vaulted Documents Referenced",
        "ext_sources_hdr": "External & Regulatory Sources Referenced",
        "no_docs": "No documents found in your vault.",
        "page_str": "page",
        "pages_str": "pages",
        "uploader_label": "Upload new policies, contracts, or census data (PDF)",
        "drop_text": "Drag and drop file here",
        "browse_text": "Browse files",
        "limit_text": "Limit 200MB per file • PDF",
        "invalid_creds": "Invalid email or password.",
        "support_text": "For questions or troubleshooting, contact us at",
        "or_call": "or call",
        "logging_in": "Signing in..."
    },
    "FR": {
        "title": "Assistant en Assurances & Réglementation du Québec",
        "portal_title": "Portail de l'Administrateur du Régime",
        "portal_subtitle": "Accès sécurisé à des réponses pour vos avantages sociaux",
        "login": "Se connecter",
        "logout": "Déconnexion",
        "admin_active": "Privilèges Administrateur Actifs - Sources tierces activées.",
        "connected_as": "Connecté en tant que",
        "tenant_id": "ID Tenant",
        "sync_button": "Synchroniser",
        "sync_tooltip_synced": "Tout est déjà synchronisé",
        "sync_tooltip_unsynced": "Cliquer pour réparer les fichiers non indexés",
        "upload_btn": "Téléverser dans le Coffre Sécurisé",
        "manage_hdr": "Coffre de documents",
        "upload_section_title": "Téléverser",
        "upload_section_subtitle": "Téléversez vos documents contractuels d'avantages sociaux pour obtenir des réponses personnalisées à vos questions",
        "vault_section_title": "Gestionnaire de documents",
        "doc_name": "Nom du Document",
        "ai_status": "Indexé",
        "upload_date": "Date de Téléversement",
        "indexed": "🟢",
        "not_indexed": "🔴",
        "delete": "Supprimer",
        "query_label": "Posez une question sur les règlements d'assurance au Québec ou vos documents :",
        "submit": "Soumettre la Question",
        "answer_hdr": "Réponse",
        "copy_lbl": "📋 Copier la réponse",
        "prev_qa_hdr": "Question et réponse précédente",
        "vault_sources_hdr": "Documents du Coffre Référencés",
        "ext_sources_hdr": "Sources Externes & Réglementaires Référencées",
        "no_docs": "Aucun document trouvé dans votre coffre.",
        "page_str": "page",
        "pages_str": "pages",
        "uploader_label": "Téléverser de nouvelles politiques, contrats ou données de recensement (PDF)",
        "drop_text": "Glissez et déposez le fichier ici",
        "browse_text": "Parcourir les fichiers",
        "limit_text": "Limite 200 Mo par fichier • PDF",
        "invalid_creds": "Identifiants invalides.",
        "support_text": "Pour toute question ou assistance, contactez-nous à",
        "or_call": "ou appelez le",
        "logging_in": "Connexion en cours..."
    }
}

def update_language():
    st.session_state.lang = st.session_state.lang_radio

def inject_theme_css():
    css = """
    <style>
    @import url('[https://fonts.googleapis.com/css2?family=Manrope:wght@400;600&family=Oswald:wght@500;700&display=swap](https://fonts.googleapis.com/css2?family=Manrope:wght@400;600&family=Oswald:wght@500;700&display=swap)');
    
    html, body, [class*="css"] {
        font-family: 'Manrope', sans-serif !important;
        color: #1c1c1c !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Oswald', sans-serif !important;
        color: #004daa !important;
    }
    
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .compact-sync-btn button {
        padding: 4px 8px !important;
        font-size: 0.8rem !important;
        min-height: 0 !important;
        height: auto !important;
    }

    .stButton > button[kind="primary"] {
        background-color: #e57200 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        font-family: 'Manrope', sans-serif !important;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #cc6500 !important;
    }
    .stButton > button[kind="secondary"] {
        border-radius: 8px;
        font-family: 'Manrope', sans-serif !important;
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        padding: 10px 14px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #004daa;
        box-shadow: 0 0 0 2px rgba(0, 77, 170, 0.2);
    }
    
    a {
        color: #004daa !important;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def inject_uploader_css(t_dict):
    css = f"""
    <style>
    [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p {{ font-size: 0px !important; color: transparent !important; }}
    [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p::before {{
        content: "{t_dict['drop_text']}";
        font-size: 16px !important;
        color: #1c1c1c !important;
        display: block;
    }}
    [data-testid="stFileUploaderDropzone"] button {{ font-size: 0px !important; color: transparent !important; }}
    [data-testid="stFileUploaderDropzone"] button::before {{
        content: "{t_dict['browse_text']}";
        font-size: 14px !important;
        color: #1c1c1c !important;
        visibility: visible;
    }}
    [data-testid="stFileUploaderDropzoneInstructions"] {{ font-size: 0px !important; color: transparent !important; }}
    [data-testid="stFileUploaderDropzoneInstructions"]::after {{
        content: "{t_dict['limit_text']}";
        font-size: 12px !important;
        color: #64748b !important;
        visibility: visible;
        display: block;
        margin-top: 5px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def clean_wayback_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    match = re.search(r"web\.archive\.org/web/[^/]+/(https?://.*)", raw_url)
    if match:
        return match.group(1)
    return raw_url

def format_page_numbers(pages):
    if not pages:
        return ""
    try:
        sorted_pages = sorted(list(set(int(p) for p in pages if str(p).strip().isdigit())))
    except Exception:
        return ", ".join(map(str, set(pages)))
        
    if not sorted_pages:
        return ""
    
    ranges = []
    start = sorted_pages[0]
    end = sorted_pages[0]
    
    for p in sorted_pages[1:]:
        if p == end + 1:
            end = p
        else:
            ranges.append(f"{start}-{end}" if start != end else f"{start}")
            start = p
            end = p
    ranges.append(f"{start}-{end}" if start != end else f"{start}")
    return ", ".join(ranges)

def login_user(email, password):
    base_auth = "[https://identitytoolkit.googleapis.com](https://identitytoolkit.googleapis.com)"
    url = f"{base_auth}/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    return response.json()

def refresh_user_token(refresh_token):
    base_refresh = "[https://securetoken.googleapis.com](https://securetoken.googleapis.com)"
    url = f"{base_refresh}/v1/token?key={FIREBASE_API_KEY}"
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    response = requests.post(url, data=payload)
    return response.json()

def perform_logout():
    cookies.remove("refresh_token")
    cookies.remove("tenant_id")
    cookies.remove("user_email")
    cookies.remove("vault_path")
    st.session_state.clear()

def run_vault_sync_and_heal():
    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
    files = list_tenant_files(st.session_state.vault_path)
    valid_filenames = [f['name'] for f in files]
    
    sync_url = f"{BASE_API_URL}/sync"
    res = requests.post(sync_url, headers=headers, json={"tenant_id": st.session_state.tenant_id, "valid_filenames": valid_filenames}, timeout=20)
    
    if res.status_code == 200:
        data = res.json()
        indexed = set(data.get("indexed", []))
        
        unindexed_files = [f for f in files if f['name'] not in indexed]
        for missing in unindexed_files:
            ingest_url = f"{BASE_API_URL}/ingest"
            vpath = str(st.session_state.vault_path).strip('/')
            gcs_uri = f"gs://{vpath}/{missing['name']}" if vpath.startswith("gs://") else f"gs://{BUCKET_NAME}/{vpath}/{missing['name']}"
                
            payload = {"tenant_id": st.session_state.tenant_id, "filename": missing['name'], "gcs_uri": gcs_uri, "category": "vault"}
            requests.post(ingest_url, headers=headers, json=payload, timeout=60)
            indexed.add(missing['name'])
                
        st.session_state.indexed_files = list(indexed)

if "id_token" not in st.session_state:
    st.session_state.id_token = None
    st.session_state.tenant_id = None
    st.session_state.user_email = None
    st.session_state.vault_path = None
    st.session_state.needs_sync = False
    st.session_state.indexed_files = []
    st.session_state.lang = "EN"

if "prev_qa" not in st.session_state:
    st.session_state.prev_qa = None

if not st.session_state.id_token:
    refresh_cookie = cookies.get("refresh_token")
    if refresh_cookie:
        auth_res = refresh_user_token(refresh_cookie)
        if "id_token" in auth_res:
            st.session_state.id_token = auth_res["id_token"]
            st.session_state.tenant_id = cookies.get("tenant_id")
            st.session_state.user_email = cookies.get("user_email")
            st.session_state.vault_path = cookies.get("vault_path")
            st.session_state.lang = cookies.get("lang") or "EN"
            st.session_state.needs_sync = True
            cookies.set("refresh_token", auth_res["refresh_token"], max_age=43200)

inject_theme_css()

if not st.session_state.id_token:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=400)
        st.markdown("<hr style='margin-top: 15px; margin-bottom: 25px; border-color: #e2e8f0;'>", unsafe_allow_html=True)
        
    col_spacer, col_lang = st.columns([9, 1])
    with col_lang:
        lang_choice = st.radio("Lang", ["EN", "FR"], key="login_lang", label_visibility="collapsed", horizontal=True)
    
    t = I18N[lang_choice]
    
    st.markdown("<div style='height: 2vh;'></div>", unsafe_allow_html=True)
    col_left, col_card, col_right = st.columns([1, 1.8, 1])
    
    with col_card:
        with st.container(border=True):
            st.markdown(f"<h2 style='color:#004daa; margin-top:0;'>{t['portal_title']}</h2>", unsafe_allow_html=True)
            st.caption(t["portal_subtitle"])
            st.markdown("<hr style='margin-top:10px; margin-bottom:20px; border-color:#e2e8f0;'>", unsafe_allow_html=True)
            
            email_label = "Email" if lang_choice == "EN" else "Courriel"
            password_label = "Password" if lang_choice == "EN" else "Mot de passe"
            
            email = st.text_input(email_label, placeholder="name@company.com")
            password = st.text_input(password_label, type="password")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            if st.button(t["login"], type="primary", use_container_width=True):
                if not email or not password:
                    st.warning("Please fill in all fields." if lang_choice == "EN" else "Veuillez remplir tous les champs.")
                else:
                    with st.spinner(t.get("logging_in", "Signing in...")):
                        auth_res = login_user(email, password)
                        if "idToken" in auth_res:
                            st.session_state.id_token = auth_res["idToken"]
                            st.session_state.tenant_id = auth_res["localId"]
                            st.session_state.user_email = auth_res.get("email", email).lower().strip()
                            st.session_state.vault_path = get_or_create_tenant_folder(st.session_state.tenant_id)
                            st.session_state.needs_sync = True
                            st.session_state.lang = lang_choice
                            
                            cookies.set("refresh_token", auth_res["refreshToken"], max_age=43200)
                            cookies.set("tenant_id", st.session_state.tenant_id, max_age=43200)
                            cookies.set("user_email", st.session_state.user_email, max_age=43200)
                            cookies.set("vault_path", st.session_state.vault_path, max_age=43200)
                            cookies.set("lang", st.session_state.lang, max_age=43200)
                            
                            st.rerun()
                        else:
                            st.error(t["invalid_creds"])
                        
            st.markdown("<hr style='margin-top:25px; margin-bottom:15px; border-color:#e2e8f0;'>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='text-align: center; font-size: 0.85rem; line-height: 1.4;'>"
                f"{t['support_text']} <a href='mailto:info@cohero.ca'>info@cohero.ca</a> "
                f"{t['or_call']} <a href='tel:5144051185'>514-405-1185</a>."
                f"</div>",
                unsafe_allow_html=True
            )
    st.stop()

if "lang" not in st.session_state:
    st.session_state.lang = "EN"

t = I18N[st.session_state.lang]
is_admin = (st.session_state.user_email == ADMIN_EMAIL.lower())

if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=400)
    st.markdown("<hr style='margin-top: 15px; margin-bottom: 25px; border-color: #e2e8f0;'>", unsafe_allow_html=True)

col_spacer, col_logout, col_lang = st.columns([8, 1, 1], vertical_alignment="center")

with col_logout:
    st.button(t["logout"], on_click=lambda: perform_logout() or st.rerun(), use_container_width=True)

with col_lang:
    st.radio(
        "Lang", 
        ["EN", "FR"], 
        index=0 if st.session_state.lang == "EN" else 1, 
        key="lang_radio",
        on_change=update_language,
        horizontal=True, 
        label_visibility="collapsed"
    )

if is_admin:
    st.info(t["admin_active"])
else:
    st.success(f"{t['connected_as']} {st.session_state.user_email} | {t['tenant_id']}: {st.session_state.tenant_id}")

if st.session_state.needs_sync:
    with st.spinner("..."):
        try:
            run_vault_sync_and_heal()
        except Exception:
            pass
    st.session_state.needs_sync = False

# ==========================================
# ADMIN ONLY: GLOBAL VALIDATED ANSWERS VAULT
# ==========================================
if is_admin:
    with st.expander("👑 Admin: Global Validated Answers Repository", expanded=False):
        st.markdown("Upload PDFs, Word (DOCX), or Excel (XLSX) files here. These form the 'Tier 2' validated database used to answer queries for ALL tenants.")
        
        global_path = "global_validated"
        
        col_up_admin, _ = st.columns([1, 1])
        with col_up_admin:
            uploaded_global = st.file_uploader("Upload Global Reference File", type=["pdf", "docx", "xlsx"], key="admin_uploader")
            if uploaded_global is not None and st.button("Ingest Global File"):
                with st.spinner("Uploading and indexing globally..."):
                    try:
                        gcs_uri = upload_file_to_drive(uploaded_global, uploaded_global.name, global_path)
                        headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
                        payload = {
                            "tenant_id": "global", 
                            "filename": uploaded_global.name, 
                            "gcs_uri": gcs_uri,
                            "category": "validated"
                        }
                        res = requests.post(f"{BASE_API_URL}/ingest", headers=headers, json=payload, timeout=60)
                        if res.status_code == 200:
                            st.success("Successfully ingested into global database!")
                        else:
                            st.error(f"Error: {res.text}")
                    except Exception as e:
                        st.error(str(e))
                        
        st.markdown("#### Global Files")
        global_files = list_tenant_files(global_path)
        if not global_files:
            st.info("No global validated files found.")
        else:
            for g_file in global_files:
                colA, colB, colC = st.columns([5, 2, 1], vertical_alignment="center")
                colA.write(f"📄 {g_file['name']}")
                colB.write(g_file.get('date', ''))
                with colC:
                    if st.button("Delete", key=f"del_{g_file['blob_name']}", type="secondary"):
                        try:
                            headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
                            requests.post(f"{BASE_API_URL}/delete", headers=headers, json={"tenant_id": "global", "filename": g_file['name']})
                            delete_tenant_file(g_file['blob_name'])
                            st.rerun()
                        except Exception:
                            pass
        st.markdown("<hr style='border-color:#e2e8f0; margin: 25px 0;'>", unsafe_allow_html=True)

# ==========================================
# STANDARD TENANT VAULT (TIER 1)
# ==========================================
with st.expander(t["manage_hdr"], expanded=False):
    inject_uploader_css(t)
    
    st.markdown(f"### {t['upload_section_title']}")
    st.caption(t["upload_section_subtitle"])
    
    col_upload, col_empty = st.columns([1, 1])
    with col_upload:
        uploaded_file = st.file_uploader(t["uploader_label"], type=["pdf"], label_visibility="collapsed")
        if uploaded_file is not None and st.button(t["upload_btn"]):
            with st.spinner("..."):
                try:
                    gcs_uri = upload_file_to_drive(uploaded_file, uploaded_file.name, st.session_state.vault_path)
                    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
                    payload = {"tenant_id": st.session_state.tenant_id, "filename": uploaded_file.name, "gcs_uri": gcs_uri, "category": "vault"}
                    ingest_res = requests.post(f"{BASE_API_URL}/ingest", headers=headers, json=payload, timeout=60)
                    if ingest_res.status_code == 200:
                        st.session_state.needs_sync = True
                    st.rerun()
                except Exception:
                    pass
                
    st.markdown("<hr style='border-color:#e2e8f0; margin: 25px 0;'>", unsafe_allow_html=True)
    
    st.markdown(f"### {t['vault_section_title']}")
    
    files = list_tenant_files(st.session_state.vault_path)
    has_unindexed = any(f['name'] not in st.session_state.indexed_files for f in files) if files else False

    if not files:
        st.info(t["no_docs"])
    else:
        col1, col2, col3, col4 = st.columns([4, 2, 2, 1], vertical_alignment="bottom")
        col1.write(f"**{t['doc_name']}**")
        col2.write(f"**{t['ai_status']}**")
        col3.write(f"**{t['upload_date']}**")
        
        with col4:
            st.markdown("<div class='compact-sync-btn'>", unsafe_allow_html=True)
            tooltip_msg = t["sync_tooltip_unsynced"] if has_unindexed else t["sync_tooltip_synced"]
            if st.button(
                t["sync_button"], 
                disabled=not has_unindexed, 
                type="secondary",
                help=tooltip_msg,
                use_container_width=True
            ):
                with st.spinner("..."):
                    run_vault_sync_and_heal()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.divider()
        
        for file in files:
            col1, col2, col3, col4 = st.columns([4, 2, 2, 1], vertical_alignment="center")
            with col1:
                st.write(f"{file['name']}")
            with col2:
                if file['name'] in st.session_state.indexed_files:
                    st.write(t["indexed"])
                else:
                    st.write(t["not_indexed"])
            with col3:
                st.write(file.get('date', 'Unknown'))
            with col4:
                if st.button(t["delete"], key=file['blob_name'], type="secondary"):
                    try:
                        headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
                        requests.post(f"{BASE_API_URL}/delete", headers=headers, json={"tenant_id": st.session_state.tenant_id, "filename": file['name']}, timeout=10)
                    except Exception:
                        pass
                    delete_tenant_file(file['blob_name'])
                    st.session_state.needs_sync = True
                    st.rerun()

st.markdown("<hr style='border-color:#e2e8f0;'>", unsafe_allow_html=True)

query = st.text_area(t["query_label"])
if st.button(t["submit"], type="primary") and query:
    if not API_KEY:
        st.error("API_KEY not configured.")
    else:
        headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
        api_lang = "French" if st.session_state.lang == "FR" else "English"
        payload = {
            "query": query,
            "tenant_id": st.session_state.tenant_id,
            "include_third_parties": is_admin,
            "language": api_lang,
            "history": st.session_state.prev_qa
        }
        
        with st.spinner("..."):
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    answer_text = data.get("answer", "")
                    raw_sources = data.get("sources", [])
                    
                    st.subheader(t["answer_hdr"])
                    
                    with st.container(border=True):
                        st.markdown(answer_text)
                        
                    with st.expander(t["copy_lbl"], expanded=False):
                        st.code(answer_text, language="markdown")
                    
                    vault_map = {}
                    ext_sources = []
                    
                    for src in raw_sources:
                        if src.get("is_vault") or src.get("is_validated"):
                            doc_name = src.get("source_file", "Unknown Document")
                            pg = src.get("page")
                            prefix = "👑 " if src.get("is_validated") else ""
                            key = f"{prefix}{doc_name}"
                            if key not in vault_map:
                                vault_map[key] = []
                            if pg is not None:
                                vault_map[key].append(pg)
                        else:
                            clean_url = clean_wayback_url(src.get("url"))
                            site_name = src.get("source_file") or "Web Source"
                            if clean_url:
                                ext_sources.append(f"🔗 [{site_name}]({clean_url})")
                            else:
                                ext_sources.append(f"🌐 {site_name}")
                                
                    if vault_map:
                        st.markdown("<hr style='border-color:#e2e8f0;'>", unsafe_allow_html=True)
                        st.markdown(f"### {t['vault_sources_hdr']}")
                        for key_name, pages in vault_map.items():
                            p_str = format_page_numbers(pages)
                            if p_str and "Part" not in p_str:
                                p_label = t['pages_str'] if ("-" in p_str or "," in p_str) else t['page_str']
                                st.markdown(f"- 📄 **{key_name}** ({p_label} {p_str})")
                            else:
                                st.markdown(f"- 📄 **{key_name}**")

                    if ext_sources:
                        st.markdown("<hr style='border-color:#e2e8f0;'>", unsafe_allow_html=True)
                        st.markdown(f"### {t['ext_sources_hdr']}")
                        for e_src in sorted(list(set(ext_sources))):
                            st.markdown(f"- {e_src}")

                    if st.session_state.prev_qa:
                        st.markdown("<hr style='border-color:#e2e8f0; margin: 40px 0 20px 0;'>", unsafe_allow_html=True)
                        st.subheader(t["prev_qa_hdr"])
                        st.markdown(f"**Q: {st.session_state.prev_qa['q']}**")
                        with st.container(border=True):
                            st.markdown(st.session_state.prev_qa['a'])

                    st.session_state.prev_qa = {
                        "q": query,
                        "a": answer_text
                    }

                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")
