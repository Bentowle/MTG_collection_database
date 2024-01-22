import pandas as pd
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import io
import urllib 
import requests
import pickle


class MTGDatabase:
    def __init__(self):
        self.collection = {}

    def search_card(self, card_name):
        cards = []
        url = f'https://api.scryfall.com/cards/search?unique=prints&q={card_name}'
        while url:
            response = requests.get(url)
            data = response.json()
            if 'data' in data:
                cards.extend(data['data'])
            url = data.get('next_page')
        return cards

    def add_card(self, card_data):
        card_data['count'] = 1  # add a count field to the card data
        set_name = card_data['set']
        if set_name not in self.collection:
            self.collection[set_name] = pd.DataFrame()
        if self.collection[set_name].empty:
            self.collection[set_name] = self.collection[set_name].append(card_data, ignore_index=True)
        else:
            # if the card already exists in the collection with the same name and set, increment its count
            if ((self.collection[set_name]['name'] == card_data['name']) & (self.collection[set_name]['set'] == card_data['set'])).any():
                self.collection[set_name].loc[(self.collection[set_name]['name'] == card_data['name']) & (self.collection[set_name]['set'] == card_data['set']), 'count'] += 1
            else:
                self.collection[set_name] = self.collection[set_name].append(card_data, ignore_index=True)
        self.collection[set_name] = self.collection[set_name].sort_values(['name', 'set'])  # sort the collection by name and set

    def save_database(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.collection, f)

    def load_database(self, filename):
        with open(filename, 'rb') as f:
            self.collection = pickle.load(f)


db = MTGDatabase()

def search_card_gui():
    card_list.delete(0, tk.END)
    cards = db.search_card(name_entry.get())
    for card in cards:
        card_list.insert(tk.END, f"{card['name']} ({card['set']})")

def on_card_select(event):
    selected_card = card_list.curselection()
    if not selected_card:
        card_image_label.config(image=placeholder_photo)
        return
    card_data = db.search_card(name_entry.get())[selected_card[0]]
    image_url = card_data['image_uris']['small']
    with urllib.request.urlopen(image_url) as u:
        raw_data = u.read()
    im = Image.open(io.BytesIO(raw_data))
    im = im.resize((200, 280))  # resize the image to the desired size
    photo = ImageTk.PhotoImage(im)

    card_image_label.config(image=photo)
    card_image_label.image = photo  # keep a reference to the image

def add_card_gui():
    selected_card = card_list.curselection()
    if not selected_card:
        messagebox.showinfo("Error", "No card selected.")
        return
    card_data = db.search_card(name_entry.get())[selected_card[0]]
    confirm = messagebox.askyesno("Confirm", f"Do you want to add {card_data['name']} to the collection?")
    if confirm:
        db.add_card(card_data)
        update_collection_display()

def update_collection_display():
    collection_list.delete(0, tk.END)
    for set_name, set_df in db.collection.items():
        if not set_df.empty:
            for index, row in set_df.iterrows():
                collection_list.insert(tk.END, f"{row['name']} ({row['set']}, {row['rarity']}, {row['type_line']}, Count: {row['count']})")

def on_collection_select(event):
    selected_card = collection_list.curselection()
    if not selected_card:
        card_image_label.config(image=placeholder_photo)
        return
    card_info = collection_list.get(selected_card).split(' (')  # split the selected item into parts
    card_name = card_info[0]  # get the card name from the selected item
    card_set = card_info[1].split(',')[0]  # get the card set from the selected item
    # get the card with the selected name and set
    card_data = db.collection[card_set].loc[(db.collection[card_set]['name'] == card_name) & (db.collection[card_set]['set'] == card_set)].iloc[0]
    image_url = card_data['image_uris']['small']
    with urllib.request.urlopen(image_url) as u:
        raw_data = u.read()
    im = Image.open(io.BytesIO(raw_data))
    im = im.resize((200, 280))  # resize the image to the desired size
    photo = ImageTk.PhotoImage(im)

    card_image_label.config(image=photo)
    card_image_label.image = photo  # keep a reference to the image

def save_database_gui():
    db.save_database('mtg_database.pkl')

def load_database_gui():
    db.load_database('mtg_database.pkl')
    update_collection_display()

root = tk.Tk()

name_label = tk.Label(root, text="Card Name")
name_label.grid(row=0, column=0)
name_entry = tk.Entry(root)
name_entry.grid(row=1, column=0)

search_button = tk.Button(root, text="Search Card", command=search_card_gui)
search_button.grid(row=2, column=0)

card_list = tk.Listbox(root)
card_list.grid(row=3, column=0)
card_list.bind('<<ListboxSelect>>', on_card_select)

placeholder_url = "https://backs.scryfall.io/large/8/0/80e6ae77-74c3-450d-a0a2-01f3168d7712.jpg?1665006204"
with urllib.request.urlopen(placeholder_url) as u:
    raw_data = u.read()
im = Image.open(io.BytesIO(raw_data))
im = im.resize((200, 280))  # resize the image to the desired size
placeholder_photo = ImageTk.PhotoImage(im)

card_image_label = tk.Label(root, image=placeholder_photo)
card_image_label.image = placeholder_photo  # keep a reference to the image
card_image_label.grid(row=3, column=1)

add_button = tk.Button(root, text="Add Card", command=add_card_gui)
add_button.grid(row=4, column=0)

save_button = tk.Button(root, text="Save Collection", command=save_database_gui)
save_button.grid(row=5, column=0)

load_button = tk.Button(root, text="Load Collection", command=load_database_gui)
load_button.grid(row=6, column=0)

collection_list = tk.Listbox(root, width=100)  # increase the width of the listbox to accommodate the count
collection_list.grid(row=7, column=0)
collection_list.bind('<<ListboxSelect>>', on_collection_select)

root.mainloop()