import os
import sys
import time
import httpx
import requests
import shutil
import chainlit as cl
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.drive_manager import get_or_create_tenant_folder, upload_file_to_drive, list_tenant_files, delete_tenant_file

load_dotenv()

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
API_KEY = os.getenv("API_KEY", "")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/rag/query")
BASE_API_URL = API_URL.rsplit('/', 1)[0]
ADMIN_EMAIL = "benjaminlarouch3@hotmail.com"

def login_firebase_user(email, password):
    _scheme = "https"
    _domain = "identitytoolkit.googleapis.com"
    url = f"{_scheme}://{_domain}/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        return res.json()
    return None

# ==========================================
# AUTHENTICATION
# ==========================================
@cl.password_auth_callback
def auth_callback(username, password):
    auth_data = login_firebase_user(username, password)
    if auth_data:
        tenant_id = auth_data["localId"]
        email = auth_data.get("email", username).lower().strip()
        is_admin = (email == ADMIN_EMAIL.lower())
        
        display_name = f"👑 Admin | {email}" if is_admin else email
        
        return cl.User(
            identifier=display_name,
            metadata={
                "tenant_id": tenant_id,
                "role": "admin" if is_admin else "user",
                "vault_path": get_or_create_tenant_folder(tenant_id)
            }
        )
    return None

# ==========================================
# VAULT ACTION HANDLERS (ORANGE BULLETS)
# ==========================================
@cl.action_callback("manage_vault")
async def on_manage_vault(action: cl.Action):
    user = cl.user_session.get("user")
    vault_path = user.metadata.get("vault_path")
    
    try:
        files = list_tenant_files(vault_path)
        if not files:
            await cl.Message(content="<span style='color:#e57200;'>■</span> **Your Vault is empty / Votre coffre-fort est vide.**").send()
            return
        
        await cl.Message(content="### <span style='color:#e57200;'>■</span> Document Vault\n*Here are your stored documents:*").send()
        
        for f in files:
            f_name = f.get("name") if isinstance(f, dict) else str(f)
            f_id = f.get("id") if isinstance(f, dict) else f_name
            local_file_path = os.path.join(vault_path, f_name)
            
            date_str = "N/A"
            if isinstance(f, dict) and "created" in f:
                date_str = f["created"][:16].replace("T", " ")
            
            elements = []
            actions = []
            
            # Cohero Orange HTML Bullets
            bullet = "<span style='color: #e57200; font-size: 1.1em;'>■</span>"
            sub_bullet = "<span style='color: #e57200; margin-left: 15px;'>▸</span>"
            
            if os.path.exists(local_file_path):
                mtime = os.path.getmtime(local_file_path)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                
                elements.append(cl.File(name=f"Download {f_name}", path=local_file_path, display="inline"))
                content = f"{bullet} **{f_name}**\n{sub_bullet} *Uploaded: {date_str}*"
            else:
                content = f"{bullet} **{f_name}**\n{sub_bullet} *Cloud Only | Uploaded: {date_str}*"
            
            actions.append(cl.Action(
                name="delete_file",
                payload={"value": f_id, "name": f_name, "path": local_file_path},
                label=f"❌ Delete {f_name}"
            ))
            
            await cl.Message(content=content, elements=elements, actions=actions).send()
            
    except Exception as e:
        await cl.Message(content=f"⚠️ Vault Error: {str(e)}").send()

@cl.action_callback("delete_file")
async def on_delete_action(action: cl.Action):
    user = cl.user_session.get("user")
    vault_path = user.metadata.get("vault_path")
    
    file_identifier = action.payload.get("value") or action.payload.get("name")
    file_name = action.payload.get("name", file_identifier)
    file_path = action.payload.get("path") or os.path.join(vault_path, file_name)
    
    try:
        try:
            delete_tenant_file(file_path)
        except Exception:
            try:
                delete_tenant_file(file_identifier)
            except TypeError:
                delete_tenant_file(vault_path, file_identifier)
        
        await action.remove()
        await cl.Message(content=f"✅ `{file_name}` deleted.").send()
    except Exception as e:
        await cl.Message(content=f"❌ Error: {str(e)}").send()

# ==========================================
# CHAT START
# ==========================================
@cl.on_chat_start
async def on_chat_start():
    user = cl.user_session.get("user")
    cl.user_session.set("prev_qa", None)
    
    welcome_text = "### Assistant"
    
    # Hidden trigger block
    actions = [
        cl.Action(name="manage_vault", payload={"value": "open"}, label="hidden_vault_trigger")
    ]
    
    await cl.Message(content=welcome_text, actions=actions).send()

# ==========================================
# MESSAGE HANDLER
# ==========================================
@cl.on_message
async def main(message: cl.Message):
    user = cl.user_session.get("user")
    tenant_id = user.metadata.get("tenant_id")
    vault_path = user.metadata.get("vault_path")
    is_admin = (user.metadata.get("role") == "admin")
    user_query = message.content.strip()

    if user_query.lower() in ["instructions", "instruction", "help"]:
        instructions_text = (
            "### 📖 System Instructions & Features\n\n"
            "1. **Quebec Insurance & Regulation Q&A:** Ask any questions regarding CNESST, RAMQ, group benefits, or policy administration.\n"
            "2. **Document Vault:** Drag and drop policy PDFs directly into this chat to index them into your private vault.\n"
            "3. **Vault Management:** Type `/vault` or click **Open Vault** to view your indexed documents, download them, or remove files.\n"
            "4. **Bilingual:** Answers automatically match the language of your query (English or French)."
        )
        await cl.Message(content=instructions_text).send()
        return

    # Silently intercept the text command
    if user_query.lower() == "/vault":
        mock_action = cl.Action(name="manage_vault", payload={"value": "open"}, label="cmd")
        await on_manage_vault(mock_action)
        return

    # --- A. HANDLE FILE UPLOADS ---
    if message.elements:
        for element in message.elements:
            if hasattr(element, "path") and element.path:
                file_name = element.name
                file_path = element.path
                category = "validated" if (is_admin and "validated" in file_name.lower()) else "vault"
                
                msg = cl.Message(content=f"⏳ Ingesting `{file_name}`...")
                await msg.send()
                
                try:
                    local_dest = os.path.join(vault_path, file_name)
                    os.makedirs(vault_path, exist_ok=True)
                    shutil.copy(file_path, local_dest)
                    
                    with open(file_path, "rb") as f:
                        gcs_uri = upload_file_to_drive(f, file_name, vault_path if category == "vault" else "global_validated")
                    
                    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
                    payload = {"tenant_id": "global" if category == "validated" else tenant_id, "filename": file_name, "gcs_uri": gcs_uri, "category": category}
                    
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        res = await client.post(f"{BASE_API_URL}/ingest", json=payload, headers=headers)
                        if res.status_code == 200:
                            msg.content = f"✅ `{file_name}` successfully added to your vault!"
                        else:
                            msg.content = f"❌ Ingestion failed: {res.text}"
                        await msg.update()
                except Exception as e:
                    msg.content = f"⚠️ Error: {str(e)}"
                    await msg.update()
        
        if not user_query:
            return

    # --- B. HANDLE TEXT QUERIES ---
    prev_qa = cl.user_session.get("prev_qa")
    
    payload = {
        "query": user_query,
        "tenant_id": tenant_id,
        "include_third_parties": is_admin,
        "language": "English",
        "history": prev_qa
    }
    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}

    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(API_URL, json=payload, headers=headers)
            if res.status_code == 200:
                data = res.json()
                formatted = data.get("answer", "No answer produced.")
                sources = data.get("sources", [])
                
                vault_sources = [s for s in sources if s.get("is_vault") or s.get("is_validated")]
                ext_sources = [s for s in sources if not (s.get("is_vault") or s.get("is_validated"))]

                bundled_vault = {}
                for s in vault_sources:
                    doc_name = s.get("source_file", "Document")
                    page = str(s.get("page", "")).replace("None", "").strip()
                    
                    if doc_name not in bundled_vault:
                        bundled_vault[doc_name] = {"pages": set(), "is_validated": s.get("is_validated")}
                    if page:
                        bundled_vault[doc_name]["pages"].add(page)

                bundled_ext = set()
                for s in ext_sources:
                    url = s.get("url")
                    site_name = s.get("source_file") or "Web Source"
                    bundled_ext.add(f"🔗 [{site_name}]({url})" if url else f"🌐 {site_name}")

                if bundled_vault or bundled_ext:
                    formatted += "\n\n---\n### 📚 Sources\n"

                if bundled_vault:
                    for doc_name, v_data in bundled_vault.items():
                        icon = "👑 " if v_data["is_validated"] else "📄 "
                        
                        def sort_key(x):
                            try: return int(x)
                            except: return x
                            
                        pages_list = sorted(list(v_data["pages"]), key=sort_key)
                        page_str = f" (Pages: {', '.join(pages_list)})" if pages_list else ""
                        formatted += f"- {icon}**{doc_name}**{page_str}\n"

                if bundled_ext:
                    for site in bundled_ext:
                        formatted += f"- {site}\n"

                response_msg.content = formatted
                await response_msg.update()

                cl.user_session.set("prev_qa", {"q": user_query, "a": data.get("answer", "")})
            else:
                response_msg.content = f"❌ Error {res.status_code}: {res.text}"
                await response_msg.update()

    except Exception as e:
        response_msg.content = f"⚠️ Connection error: {str(e)}"
        await response_msg.update()
