import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Menu, simpledialog
from datetime import datetime
from PIL import Image, ImageTk
import json

class FileExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("Explorateur de Fichiers")
        self.current_path = os.path.expanduser("~")
        self.favorites = self.load_favorites()
        self.filter_ext = "*"
        self.icon_cache = {}
        
        # Configuration de la fenêtre
        self.root.geometry("1000x700")
        self.setup_icons()
        self.create_widgets()
        self.load_content()
        
        # Initialisation des piles d'historique
        self.history = []       # Historique des chemins visités
        self.future = []        # Chemins pour la navigation "forward"
        self.current_index = -1 # Index courant dans l'historique
        
        
    
        
    def setup_icons(self):
        """Crée des icônes pour les dossiers et fichiers"""
        try:
            # Icône dossier
            folder_img = Image.open("folder_icon.jpg") if os.path.exists("folder_icon.jpg") else Image.new('RGB', (16, 16), 'blue')
            self.folder_icon = ImageTk.PhotoImage(folder_img.resize((16, 16)))
            
            # Icône fichier
            file_img = Image.open("file_icon.png") if os.path.exists("file_icon.png") else Image.new('RGB', (16, 16), 'gray')
            self.file_icon = ImageTk.PhotoImage(file_img.resize((16, 16)))
        except:
            self.folder_icon = None
            self.file_icon = None
    
    def create_widgets(self):
        """Crée tous les widgets de l'interface"""
        # Barre d'outils en haut
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(toolbar, text="←", command=self.go_back).pack(side="left")
        ttk.Button(toolbar, text="→", command=self.go_forward).pack(side="left")
        ttk.Button(toolbar, text="↑", command=self.go_up).pack(side="left")
        ttk.Button(toolbar, text="Actualiser", command=self.load_content).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Nouveau dossier", command=self.create_folder).pack(side="left", padx=5)
        
        # Barre de recherche
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side="right", padx=5)
        self.search_entry = tk.Entry(search_frame, font=("Arial", 12), width=25)
        self.search_entry.pack(padx=10, pady=5, side="left")
        
        # Bouton Rechercher
        ttk.Button(
        search_frame, 
        text="Rechercher", 
        command=self.search  # Appel direct
        ).pack(side="left", padx=2)
        
        # Bouton Annuler
        ttk.Button(
            search_frame,
            text="×",
            width=2,
            command=self.cancel_search
        ).pack(side="left")
        
        # Barre de chemin
        self.path_var = tk.StringVar()
        path_frame = ttk.Frame(self.root)
        path_frame.pack(fill="x", padx=5, pady=(0,5))
        
        ttk.Label(path_frame, text="Chemin:").pack(side="left")
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=70)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.path_entry.bind("<Return>", lambda e: self.navigate_to(self.path_var.get()))
        
        ttk.Button(path_frame, text="Parcourir...", command=self.browse_folder).pack(side="left")
        
        # Filtres
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill="x", padx=5, pady=(0,5))
        
        ttk.Label(filter_frame, text="Filtrer:").pack(side="left")
        ttk.Button(filter_frame, text="Tous", command=lambda: self.set_filter("*")).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Images", command=lambda: self.set_filter(".jpg;.png;.gif")).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Documents", command=lambda: self.set_filter(".txt;.pdf;.docx")).pack(side="left", padx=5)
        
        # Panneau principal
        main_panel = ttk.PanedWindow(self.root, orient="horizontal")
        main_panel.pack(fill="both", expand=True)
        
        # Panneau latéral
        side_panel = ttk.Frame(main_panel, width=200)
        main_panel.add(side_panel)
        
        # Section Favoris
        fav_frame = ttk.LabelFrame(side_panel, text="Favorites")
        fav_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.fav_listbox = tk.Listbox(fav_frame)
        self.fav_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.fav_listbox.bind("<Double-1>", self.on_fav_double_click)
        self.update_favorites_list()
        
        # Zone de contenu principale
        content_frame = ttk.Frame(main_panel)
        main_panel.add(content_frame, weight=1)
        
        # Treeview avec barre de défilement
        self.tree = ttk.Treeview(content_frame, columns=("Size", "Type", "Modified"), selectmode="browse")
        self.tree.heading("#0", text="Nom", anchor="w")
        self.tree.heading("Size", text="Taille", anchor="w")
        self.tree.heading("Type", text="Type", anchor="w")
        self.tree.heading("Modified", text="Modifié le", anchor="w")
        
        self.tree.column("#0", width=300)
        self.tree.column("Size", width=100)
        self.tree.column("Type", width=100)
        self.tree.column("Modified", width=150)
        
        vsb = ttk.Scrollbar(content_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(content_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Barre de statut
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken")
        status_bar.pack(fill="x", padx=5, pady=5)
        
        # Menu contextuel
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Ouvrir", command=self.open_selected)
        self.context_menu.add_command(label="Ajouter aux favoris", command=self.add_to_favorites)
        self.context_menu.add_command(label="Renommer", command=self.rename_item)
        self.context_menu.add_command(label="Supprimer", command=self.delete_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Propriétés", command=self.show_properties)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def search(self):
        """Filtre les éléments en fonction de la recherche."""
        query = self.search_entry.get().lower()
        if not query:
            self.load_content()
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            # Ajouter le dossier parent (..)
            self.tree.insert("", "end", text="..", values=("", "Dossier", ""), 
                            image=self.folder_icon, tags=("dir",))
            
            # Recherche dans le dossier courant
            for item in os.listdir(self.current_path):
                if query in item.lower():
                    full_path = os.path.join(self.current_path, item)
                    
                    if os.path.isdir(full_path):
                        # Dossier - utiliser l'icône dossier
                        self.tree.insert("", "end", 
                                    text=item,
                                    values=("", "Dossier", ""),
                                    image=self.folder_icon,
                                    tags=("dir",))
                    else:
                        # Fichier - utiliser l'icône fichier
                        size = os.path.getsize(full_path)
                        mtime = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M")
                        ext = os.path.splitext(item)[1][1:].upper() or "Fichier"
                        
                        self.tree.insert("", "end",
                                    text=item,
                                    values=(self.format_size(size), ext, mtime),
                                    image=self.file_icon,
                                    tags=("file",))
            self.status_var.set(f"Résultats pour: {query}")
                            
        except PermissionError:
            messagebox.showerror("Erreur", "Accès refusé à ce dossier.")
            self.load_content()
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la recherche: {str(e)}")
            self.load_content()

    def cancel_search(self):
        """Annule la recherche et réaffiche tout"""
        self.search_entry.delete(0, tk.END)
        self.load_content()
        
    def load_favorites(self):
        """Charge les favoris depuis un fichier JSON"""
        try:
            with open("favorites.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
    def save_favorites(self):
        """Enregistre les favoris dans un fichier JSON"""
        with open("favorites.json", "w") as f:
            json.dump(self.favorites, f)

    def update_favorites_list(self):
        """Met à jour la liste des favoris dans le panneau latéral"""
        self.fav_listbox.delete(0, tk.END)
        for fav in self.favorites:
            self.fav_listbox.insert(tk.END, fav)

    def add_to_favorites(self):
        """Ajoute l'élément sélectionné aux favoris"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            path = os.path.join(self.current_path, item["text"])
            if path not in self.favorites:
                self.favorites.append(path)
                self.save_favorites()
                self.update_favorites_list()
                messagebox.showinfo("Favoris", f"{item['text']} ajouté aux favoris")

    def on_fav_double_click(self, event):
        """Navigation vers un favori"""
        selection = self.fav_listbox.curselection()
        if selection:
            path = self.favorites[selection[0]]
            if os.path.exists(path):
                self.navigate_to(path)
            else:
                messagebox.showerror("Erreur", "Le chemin n'existe plus")
                self.favorites.pop(selection[0])
                self.save_favorites()
                self.update_favorites_list()

    def set_filter(self, ext):
        """Définit un filtre pour les extensions de fichiers"""
        self.filter_ext = ext
        self.load_content()
    
    def browse_folder(self):
        """Ouvre une boîte de dialogue pour choisir un dossier"""
        folder = filedialog.askdirectory(initialdir=self.current_path)
        if folder:
            self.navigate_to(folder)
    
    def navigate_to(self, path):
        """Navigue vers le chemin spécifié et met à jour l'historique"""
        if os.path.exists(path):
            path = os.path.abspath(path)
        
            # Si on navigue vers un nouveau chemin (pas via back/forward)
            if not self.future and (not self.history or self.history[-1] != path):
                # Ajouter à l'historique seulement si différent du dernier
                if not self.history or self.history[-1] != path:
                    self.history.append(path)
                    self.current_index = len(self.history) - 1
            
                    # Vider la pile "future" car on a pris une nouvelle direction
                    self.future = []
        
            self.current_path = path
            self.path_var.set(self.current_path)
            self.load_content()
        else:
            messagebox.showerror("Erreur", "Chemin invalide")
    
    def go_back(self):
        """Retourne au dossier précédent dans l'historique"""
        if self.current_index > 0:
            # Ajouter le chemin courant à la pile "future"
            self.future.append(self.history[self.current_index])
        
            # Décrémenter l'index et aller au chemin précédent
            self.current_index -= 1
            self.current_path = self.history[self.current_index]
            self.path_var.set(self.current_path)
            self.load_content()
        else:
            messagebox.showinfo("Information", "Début de l'historique atteint")
    
    def go_forward(self):
        """Avance au dossier suivant dans l'historique"""
        if self.future:
            # Ajouter le chemin courant à l'historique
            if not self.history or self.history[-1] != self.current_path:
                self.history.append(self.current_path)
                self.current_index = len(self.history) - 1
        
            # Prendre le dernier chemin de la pile "future"
            next_path = self.future.pop()
            self.current_path = next_path
            self.path_var.set(self.current_path)
        
            # Mettre à jour l'historique et l'index
            self.history.append(next_path)
            self.current_index = len(self.history) - 1
        
            self.load_content()
        else:
            messagebox.showinfo("Information", "Aucun historique futur disponible")
    
    def go_up(self):
        """Remonte d'un niveau dans l'arborescence"""
        parent = os.path.dirname(self.current_path)
        if os.path.exists(parent):
            self.navigate_to(parent)
    
    def load_content(self):
        """Charge le contenu du dossier courant"""
        # Vider le treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter le dossier parent (..)
        self.tree.insert("", "end", text="..", values=("", "Dossier", ""), 
                        image=self.folder_icon, tags=("dir",))
        
        try:
            # Lister le contenu du dossier
            for item in sorted(os.listdir(self.current_path)):
                full_path = os.path.join(self.current_path, item)
                
                # Vérifier le filtre
                if self.filter_ext != "*":
                    if os.path.isfile(full_path):
                        ext = os.path.splitext(item)[1].lower()
                        if ext not in self.filter_ext.split(";"):
                            continue
                
                if os.path.isdir(full_path):
                    self.tree.insert("", "end", text=item, values=("", "Dossier", ""), 
                                    image=self.folder_icon, tags=("dir",))
                else:
                    size = os.path.getsize(full_path)
                    mtime = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M")
                    ext = os.path.splitext(item)[1][1:].upper() or "Fichier"
                    self.tree.insert("", "end", text=item, 
                                    values=(self.format_size(size), ext, mtime), 
                                    image=self.file_icon, tags=("file",))
            
            self.status_var.set(f"{len(os.listdir(self.current_path))} éléments")
        except PermissionError:
            self.status_var.set("Erreur: Accès refusé")
        except Exception as e:
            self.status_var.set(f"Erreur: {str(e)}")
    
    def format_size(self, size):
        """Formate la taille en unités lisible"""
        for unit in ['', 'K', 'M', 'G', 'T']:
            if size < 1024:
                return f"{size:.1f}{unit}B"
            size /= 1024
        return f"{size:.1f}PB"
    
    def on_double_click(self, event):
        """Gère le double-clic sur un élément"""
        item = self.tree.selection()[0]
        name = self.tree.item(item, "text")
        
        if name == "..":
            self.go_up()
        else:
            full_path = os.path.join(self.current_path, name)
            if os.path.isdir(full_path):
                self.navigate_to(full_path)
            else:
                self.open_file(full_path)
    
    def show_context_menu(self, event):
        """Affiche le menu contextuel"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def open_selected(self):
        """Ouvre l'élément sélectionné"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            name = item["text"]
            full_path = os.path.join(self.current_path, name)
            
            if name == "..":
                self.go_up()
            elif os.path.isdir(full_path):
                self.navigate_to(full_path)
            else:
                self.open_file(full_path)
    
    def open_file(self, path):
        """Ouvre un fichier avec l'application par défaut"""
        try:
            os.startfile(path)  # Windows
        except:
            try:
                os.system(f'xdg-open "{path}"')  # Linux
            except:
                try:
                    os.system(f'open "{path}"')  # macOS
                except:
                    messagebox.showerror("Erreur", "Impossible d'ouvrir le fichier")
    
    def create_folder(self):
        """Crée un nouveau dossier"""
        name = simpledialog.askstring("Nouveau dossier", "Nom du dossier:")
        if name:
            try:
                os.mkdir(os.path.join(self.current_path, name))
                self.load_content()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de créer le dossier: {str(e)}")
    
    def rename_item(self):
        """Renomme l'élément sélectionné"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            old_name = item["text"]
            new_name = simpledialog.askstring("Renommer", "Nouveau nom:", initialvalue=old_name)
            
            if new_name and new_name != old_name:
                try:
                    os.rename(
                        os.path.join(self.current_path, old_name),
                        os.path.join(self.current_path, new_name)
                    )
                    self.load_content()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de renommer: {str(e)}")
    
    def delete_item(self):
        """Supprime l'élément sélectionné"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            name = item["text"]
            
            if messagebox.askyesno("Confirmer", f"Supprimer {name} ?"):
                try:
                    path = os.path.join(self.current_path, name)
                    if os.path.isdir(path):
                        os.rmdir(path)
                    else:
                        os.remove(path)
                    self.load_content()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer: {str(e)}")
    
    def show_properties(self):
        """Affiche les propriétés de l'élément sélectionné"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            name = item["text"]
            path = os.path.join(self.current_path, name)
            
            try:
                stat = os.stat(path)
                size = self.format_size(stat.st_size)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                ctime = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                
                messagebox.showinfo("Propriétés",
                    f"Nom: {name}\n"
                    f"Chemin: {path}\n"
                    f"Taille: {size}\n"
                    f"Type: {'Dossier' if os.path.isdir(path) else 'Fichier'}\n"
                    f"Créé le: {ctime}\n"
                    f"Modifié le: {mtime}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'obtenir les propriétés: {str(e)}")

if __name__ == "__main__":
    from tkinter import simpledialog
    root = tk.Tk()
    app = FileExplorer(root)
    root.mainloop()