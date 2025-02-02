#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import os
import zipfile
import shutil
import subprocess

UPDATES_FILE = "index.html"
DOCS_FILE    = "documents.html"
UPLOADS_DIR  = "uploads"  # dossier où on range les zip

class UpdateItem:
    def __init__(self, title, date_str, body):
        self.title = title
        self.date_str = date_str
        self.body = body

    def __str__(self):
        return f"{self.title}  [{self.date_str}]"

class DocItem:
    """
    name  : nom du document (affiché)
    date_str : date d'ajout/modif
    url   : chemin vers le ZIP (ex "uploads/MonDossier.zip")
    """
    def __init__(self, name, date_str, url):
        self.name = name
        self.date_str = date_str
        self.url = url

    def __str__(self):
        return f"{self.name}  [{self.date_str}]"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestion TIPE (GUI)")

        # Notebook -> 2 onglets
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # === Onglet Mises à jour ===
        self.tab_updates = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_updates, text="Mises à jour")

        self.update_list = tk.Listbox(self.tab_updates, height=10, width=60)
        self.update_list.grid(row=0, column=0, columnspan=3, padx=5, pady=5)

        btn_add_update = tk.Button(self.tab_updates, text="Ajouter", command=self.add_update_popup)
        btn_add_update.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        btn_edit_update = tk.Button(self.tab_updates, text="Modifier", command=self.edit_update_popup)
        btn_edit_update.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        btn_del_update = tk.Button(self.tab_updates, text="Supprimer", command=self.delete_update)
        btn_del_update.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        # === Onglet Documents ===
        self.tab_docs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_docs, text="Documents")

        self.docs_list = tk.Listbox(self.tab_docs, height=10, width=60)
        self.docs_list.grid(row=0, column=0, columnspan=3, padx=5, pady=5)

        btn_add_doc = tk.Button(self.tab_docs, text="Ajouter", command=self.add_doc_popup)
        btn_add_doc.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        btn_edit_doc = tk.Button(self.tab_docs, text="Modifier", command=self.edit_doc_popup)
        btn_edit_doc.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        btn_del_doc = tk.Button(self.tab_docs, text="Supprimer", command=self.delete_doc)
        btn_del_doc.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        # Données en mémoire
        self.updates_data = []
        self.docs_data    = []

        # Créer le dossier uploads si pas existant
        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR)

        # Charger depuis HTML
        self.load_updates_from_html()
        self.load_docs_from_html()
        self.refresh_updates_listbox()
        self.refresh_docs_listbox()

    # ------------------------------------------------------------------
    #  Mises à jour
    # ------------------------------------------------------------------
    def load_updates_from_html(self):
        self.updates_data.clear()
        if not os.path.exists(UPDATES_FILE):
            return
        with open(UPDATES_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        start = 0
        while True:
            start_div = content.find('<div class="update">', start)
            if start_div == -1:
                break
            end_div = content.find('</div>', start_div)
            if end_div == -1:
                break
            block = content[start_div:end_div+len('</div>')]
            start = end_div + len('</div>')

            title   = self.extract_tag(block, "strong")
            date_str= self.extract_tag(block, "em")
            body    = self.extract_tag(block, "p")
            if not date_str:
                date_str = ""
            self.updates_data.append(UpdateItem(title, date_str, body))

    def save_updates_to_html(self):
        if os.path.exists(UPDATES_FILE):
            with open(UPDATES_FILE, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>TIPE - Mises à jour</title></head><body>
<div class="container"><!-- Les mises à jour existantes s'insèrent ici --></div>
</body></html>
"""
        new_content = self.remove_all_blocks(content, 'update')
        blocks_html = ""
        for upd in self.updates_data:
            blocks_html += f"""
    <div class="update">
      <strong>{upd.title}</strong>
      <em>{upd.date_str}</em>
      <p>{upd.body}</p>
    </div>
"""

        marker = "<!-- Les mises à jour existantes s'insèrent ici -->"
        if marker in new_content:
            new_content = new_content.replace(marker, marker + blocks_html)
        else:
            new_content = new_content.replace("</div>", blocks_html + "\n</div>", 1)

        with open(UPDATES_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)

    def add_update_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Ajouter une mise à jour")

        tk.Label(popup, text="Titre :").pack(pady=5)
        entry_title = tk.Entry(popup, width=40)
        entry_title.pack()

        tk.Label(popup, text="Contenu :").pack(pady=5)
        txt_body = tk.Text(popup, width=40, height=5)
        txt_body.pack()

        def on_save():
            t = entry_title.get().strip()
            b = txt_body.get("1.0", "end").strip()
            if not t or not b:
                messagebox.showwarning("Erreur", "Veuillez remplir tous les champs.")
                return
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            new_item = UpdateItem(t, now_str, b)
            self.updates_data.append(new_item)
            self.save_updates_to_html()
            self.refresh_updates_listbox()
            commit_and_push("Ajout mise à jour")
            popup.destroy()

        tk.Button(popup, text="Enregistrer", command=on_save).pack(pady=10)

    def edit_update_popup(self):
        sel = self.update_list.curselection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez une mise à jour.")
            return
        idx = sel[0]
        upd = self.updates_data[idx]

        popup = tk.Toplevel(self)
        popup.title("Modifier la mise à jour")

        tk.Label(popup, text="Titre :").pack(pady=5)
        entry_title = tk.Entry(popup, width=40)
        entry_title.pack()
        entry_title.insert(0, upd.title)

        tk.Label(popup, text="Contenu :").pack(pady=5)
        txt_body = tk.Text(popup, width=40, height=5)
        txt_body.pack()
        txt_body.insert("1.0", upd.body)

        def on_save():
            new_t = entry_title.get().strip()
            new_b = txt_body.get("1.0", "end").strip()
            if not new_t or not new_b:
                messagebox.showwarning("Erreur", "Champs vides ?")
                return
            upd.title = new_t
            upd.body  = new_b
            self.save_updates_to_html()
            self.refresh_updates_listbox()
            commit_and_push("Modification mise à jour")
            popup.destroy()

        tk.Button(popup, text="Enregistrer", command=on_save).pack(pady=10)

    def delete_update(self):
        sel = self.update_list.curselection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez une mise à jour.")
            return
        idx = sel[0]
        conf = messagebox.askyesno("Confirmation", "Supprimer cette mise à jour ?")
        if not conf:
            return
        self.updates_data.pop(idx)
        self.save_updates_to_html()
        self.refresh_updates_listbox()
        commit_and_push("Suppression mise à jour")

    def refresh_updates_listbox(self):
        self.update_list.delete(0, tk.END)
        for u in self.updates_data:
            self.update_list.insert(tk.END, str(u))

    # ------------------------------------------------------------------
    #  Documents
    # ------------------------------------------------------------------
    def load_docs_from_html(self):
        self.docs_data.clear()
        if not os.path.exists(DOCS_FILE):
            return
        with open(DOCS_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        start = 0
        while True:
            start_div = content.find('<div class="doc-item">', start)
            if start_div == -1:
                break
            end_div = content.find('</div>', start_div)
            if end_div == -1:
                break
            block = content[start_div:end_div+len('</div>')]
            start = end_div + len('</div>')

            name = self.extract_tag(block, "strong")
            date_str = self.extract_tag(block, "em")
            url = self.extract_href(block)
            if not date_str:
                date_str = ""
            if not url:
                url = ""
            self.docs_data.append(DocItem(name, date_str, url))

    def save_docs_to_html(self):
        if os.path.exists(DOCS_FILE):
            with open(DOCS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Documents</title></head><body>
<div class="container"><!-- Les documents ajoutés s'insèrent ici --></div>
</body></html>
"""
        new_content = self.remove_all_blocks(content, 'doc-item')

        blocks_html = ""
        for d in self.docs_data:
            blocks_html += f"""
    <div class="doc-item">
      <strong>{d.name}</strong>
      <em>{d.date_str}</em>
      <a href="{d.url}" target="_blank">Ouvrir</a>
    </div>
"""

        marker = "<!-- Les documents ajoutés s'insèrent ici -->"
        if marker in new_content:
            new_content = new_content.replace(marker, marker + blocks_html)
        else:
            new_content = new_content.replace("</div>", blocks_html + "\n</div>", 1)

        with open(DOCS_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)

    def add_doc_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Ajouter un document (zippé)")

        tk.Label(popup, text="Nom du document :").pack(pady=5)
        entry_name = tk.Entry(popup, width=40)
        entry_name.pack()

        tk.Label(popup, text="Chemin local (fichier ou dossier) :").pack(pady=5)
        entry_path = tk.Entry(popup, width=40)
        entry_path.pack()

        frame_btns = tk.Frame(popup)
        frame_btns.pack(pady=5)

        def choose_file():
            path = filedialog.askopenfilename()
            if path:
                entry_path.delete(0, tk.END)
                entry_path.insert(0, path)

        def choose_folder():
            folder = filedialog.askdirectory()
            if folder:
                entry_path.delete(0, tk.END)
                entry_path.insert(0, folder)

        btn_file = tk.Button(frame_btns, text="Choisir un fichier...", command=choose_file)
        btn_file.pack(side="left", padx=5)
        btn_dir  = tk.Button(frame_btns, text="Choisir un dossier...", command=choose_folder)
        btn_dir.pack(side="left", padx=5)

        def on_save():
            n = entry_name.get().strip()
            p = entry_path.get().strip()
            if not n or not p:
                messagebox.showwarning("Erreur", "Champs vides ?")
                return

            # On crée un zip et récupère le chemin .zip
            new_zip_path = make_zip_in_uploads(p)

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            new_doc = DocItem(n, now_str, new_zip_path)
            self.docs_data.append(new_doc)
            self.save_docs_to_html()
            self.refresh_docs_listbox()
            commit_and_push("Ajout document (ZIP)")
            popup.destroy()

        tk.Button(popup, text="Enregistrer", command=on_save).pack(pady=10)

    def edit_doc_popup(self):
        sel = self.docs_list.curselection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez un document.")
            return
        idx = sel[0]
        doc = self.docs_data[idx]

        popup = tk.Toplevel(self)
        popup.title("Modifier le document (zippé)")

        tk.Label(popup, text="Nom du document :").pack(pady=5)
        entry_name = tk.Entry(popup, width=40)
        entry_name.pack()
        entry_name.insert(0, doc.name)

        tk.Label(popup, text="Nouveau chemin local :").pack(pady=5)
        entry_path = tk.Entry(popup, width=40)
        entry_path.pack()
        entry_path.insert(0, doc.url)  # On y met le chemin ZIP actuel (pas forcément utile)

        frame_btns = tk.Frame(popup)
        frame_btns.pack(pady=5)

        def choose_file():
            path = filedialog.askopenfilename()
            if path:
                entry_path.delete(0, tk.END)
                entry_path.insert(0, path)

        def choose_folder():
            folder = filedialog.askdirectory()
            if folder:
                entry_path.delete(0, tk.END)
                entry_path.insert(0, folder)

        btn_file = tk.Button(frame_btns, text="Choisir un fichier...", command=choose_file)
        btn_file.pack(side="left", padx=5)
        btn_dir  = tk.Button(frame_btns, text="Choisir un dossier...", command=choose_folder)
        btn_dir.pack(side="left", padx=5)

        def on_save():
            new_name = entry_name.get().strip()
            new_src  = entry_path.get().strip()
            if not new_name:
                messagebox.showwarning("Erreur", "Nom vide ?")
                return
            doc.name = new_name
            # Si l'utilisateur a indiqué un nouveau chemin existant, on refait un zip
            if os.path.exists(new_src):
                doc.url = make_zip_in_uploads(new_src)
            else:
                # sinon on garde le ZIP précédent
                pass

            self.save_docs_to_html()
            self.refresh_docs_listbox()
            commit_and_push("Modification document (ZIP)")
            popup.destroy()

        tk.Button(popup, text="Enregistrer", command=on_save).pack(pady=10)

    def delete_doc(self):
        sel = self.docs_list.curselection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionnez un document.")
            return
        idx = sel[0]
        conf = messagebox.askyesno("Confirmation", "Supprimer ce document ?")
        if not conf:
            return
        self.docs_data.pop(idx)
        self.save_docs_to_html()
        self.refresh_docs_listbox()
        commit_and_push("Suppression document")

    def refresh_docs_listbox(self):
        self.docs_list.delete(0, tk.END)
        for d in self.docs_data:
            self.docs_list.insert(tk.END, str(d))

    # ------------------------------------------------------------------
    #  Outils HTML
    # ------------------------------------------------------------------
    @staticmethod
    def extract_tag(block, tag):
        start_tag = f"<{tag}>"
        end_tag   = f"</{tag}>"
        s = block.find(start_tag)
        if s == -1:
            return ""
        e = block.find(end_tag, s)
        if e == -1:
            return ""
        return block[s+len(start_tag) : e].strip()

    @staticmethod
    def extract_href(block):
        href_idx = block.find('href="')
        if href_idx == -1:
            return ""
        end_quote = block.find('"', href_idx+len('href="'))
        if end_quote == -1:
            return ""
        return block[href_idx+len('href="') : end_quote]

    @staticmethod
    def remove_all_blocks(content, class_name):
        new_c = content
        while True:
            start_div = new_c.find(f'<div class="{class_name}">')
            if start_div == -1:
                break
            end_div = new_c.find('</div>', start_div)
            if end_div == -1:
                break
            end_div += len('</div>')
            new_c = new_c[:start_div] + new_c[end_div:]
        return new_c

# ----------------------------------------------------------------
#  FONCTION DE ZIP : make_zip_in_uploads
# ----------------------------------------------------------------
def make_zip_in_uploads(src_path):
    """
    Crée un zip dans UPLOADS_DIR à partir d'un fichier ou dossier src_path.
    Retourne le chemin relatif, ex: "uploads/MonFichier.zip"

    - On supprime l'ancienne archive si elle existe.
    - On zippe tout le contenu si c'est un dossier, ou un seul fichier si c'est un fichier.
    """
    # Nom de base sans extension
    base_name = os.path.splitext(os.path.basename(src_path))[0]
    # Chemin final pour le zip
    zip_filename = base_name + ".zip"
    zip_path = os.path.join(UPLOADS_DIR, zip_filename)

    # Supprime si déjà existant
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # Créer le zip
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
        if os.path.isdir(src_path):
            # Ajouter tout le contenu du dossier
            for root, dirs, files in os.walk(src_path):
                for f in files:
                    abs_file = os.path.join(root, f)
                    # chemin relatif pour stocker dans le zip
                    rel_file = os.path.relpath(abs_file, start=src_path)
                    zipf.write(abs_file, arcname=rel_file)
        else:
            # C'est un fichier
            zipf.write(src_path, arcname=os.path.basename(src_path))

    # On retourne un chemin relatif "uploads/...zip"
    return zip_path

# ----------------------------------------------------------------
#  Commandes GIT
# ----------------------------------------------------------------
def commit_and_push(message):
    """
    git add . ; git commit -m "message" ; git push origin main
    """
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        messagebox.showinfo("Git", f"Modifications poussées sur GitHub (commit: {message})")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Git Error", f"Une erreur est survenue:\n{e}")

# ----------------------------------------------------------------
#  MAIN
# ----------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()
