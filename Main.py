import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import json
import os

# --- Custom Color and Font Settings (Updated) ---
PASTEL_BG = "#f5f5f5"
PRIMARY_COLOR = "#b3e0ff"
ACCENT_COLOR = "#90EE90"
HOVER_COLOR = "#e0f7fa"
TEXT_COLOR = "#333333"

ELEGANT_FONT = ("Century Gothic", 12)
HEADER_FONT = ("Century Gothic", 35, "bold")
SUBHEADER_FONT = ("Century Gothic", 16, "bold")

# --- Custom Widgets ---
class RoundedButton(tk.Button):
    def __init__(self, master=None, cnf={}, **kw):
        bg = kw.pop('bg', PRIMARY_COLOR)
        fg = kw.pop('fg', TEXT_COLOR)
        font = kw.pop('font', ELEGANT_FONT)
        super().__init__(master, cnf, bg=bg, fg=fg, font=font, bd=0, relief=tk.FLAT, **kw)
        self.default_bg = bg
        self.config(pady=8, padx=15)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        try:
            self.config(relief=tk.RAISED, bd=2)
        except Exception:
            pass
        self.config(bg=self.default_bg)

    def _on_leave(self, e):
        try:
            self.config(relief=tk.FLAT, bd=0)
        except Exception:
            pass
        self.config(bg=self.default_bg)

class IngredientButton(tk.Checkbutton):
    def __init__(self, master=None, cnf={}, **kw):
        bg = kw.pop('bg', PASTEL_BG)
        fg = kw.pop('fg', TEXT_COLOR)
        font = kw.pop('font', ELEGANT_FONT)
        super().__init__(master, cnf, bg=bg, fg=fg, font=font, bd=1,
                         relief=tk.GROOVE, indicatoron=False, width=15, height=2,
                         activebackground=HOVER_COLOR, activeforeground=TEXT_COLOR, **kw)
        self.orig_bg = bg
        self.config(padx=5, pady=5)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.config(bg=HOVER_COLOR)

    def _on_leave(self, e):
        if str(self.cget("relief")).lower() in ("sunken",):
            self.config(bg=ACCENT_COLOR)
        else:
            self.config(bg=self.orig_bg)


def _bind_mousewheel(widget, command):
    def _on_mousewheel(event):
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
        command(delta)
        return "break"

    widget.bind("<MouseWheel>", _on_mousewheel)
    widget.bind("<Button-4>", _on_mousewheel)
    widget.bind("<Button-5>", _on_mousewheel)

# ---------- Load Recipes (from recipes.json) ----------
script_dir = os.path.dirname(os.path.abspath(__file__))
recipes_path = os.path.join(script_dir, "recipes.json")
recipes = []
if os.path.exists(recipes_path):
    try:
        with open(recipes_path, "r", encoding="utf-8") as f:
            recipes = json.load(f)
            if not isinstance(recipes, list):
                # if file had dict, try to transform
                if isinstance(recipes, dict):
                    # expected list of {"name":..., "ingredients":..., "instructions":...}
                    recipes = list(recipes.values())
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load recipes.json: {e}")
else:
    # If no recipes.json, leave recipes empty; make_meal will handle empty case.
    recipes = []

# --- Core Functions ---
def show_frame(frame):
    frame.tkraise()
    if frame == outer_ing_frame:
        root.after(100, lambda: canvas.yview_moveto(0))

# ---------- Ingredient Feature ----------
def toggle_ingredient(name, var, button):
    if var.get():
        button.config(relief="sunken", bg=ACCENT_COLOR, bd=2)
    else:
        button.config(relief=tk.GROOVE, bg=PASTEL_BG, bd=1)

    update_make_meal_button()

def update_make_meal_button():
    selected = [v.get() for v in ingredient_vars.values()].count(True)
    if selected >= 2:
        make_meal_btn.config(state="normal", bg=PRIMARY_COLOR)
        instruction_label.config(text="")
    else:
        make_meal_btn.config(state="disabled", bg=PASTEL_BG)
        instruction_label.config(text="Please choose at least 2 ingredients")

# ---------- Make Meal ----------
make_meal_in_progress = False

def make_meal():
    global make_meal_in_progress
    if make_meal_in_progress:
        return
    make_meal_in_progress = True
    make_meal_btn.config(state="disabled", text="⏳ Searching...")
    root.update()
    try:
        selected_ingredients = [name for name, var in ingredient_vars.items() if var.get()]
        if not recipes:
            messagebox.showerror("No Recipes", "No recipes loaded (recipes.json missing or invalid).")
            return

        # find matching recipes (any ingredient overlap)
        matching_recipes = [r for r in recipes if any(ing in selected_ingredients for ing in r.get("ingredients", []))]
        if not matching_recipes:
            messagebox.showinfo("No Recipes", "No matching recipes found!")
            return

        display_recipe_list_with_boxes(matching_recipes, selected_ingredients)
        show_frame(meal_suggestion_frame)
    finally:
        make_meal_in_progress = False
        make_meal_btn.config(state="normal", text="Make Meal")

# ---------- Display matching recipes in the styled meal_suggestion_frame ----------
instruction_box = None  # scrolledtext for instructions (set in display function)
def display_recipe_list_with_boxes(recipes_to_show, selected_ingredients):
    # Clear previous content frames if present
    for widget in recipe_left_frame.winfo_children():
        widget.destroy()
    for widget in recipe_right_frame.winfo_children():
        widget.destroy()

    # Ingredients box at top of left column
    ing_box = tk.Frame(recipe_left_frame, bg="#ffffff", bd=0)
    ing_box.pack(fill="x", padx=10, pady=(6, 8))
    tk.Label(ing_box, text="Your Ingredients", font=("Century Gothic", 13, "bold"), bg="#ffffff", fg=TEXT_COLOR).pack(anchor="w")
    tk.Label(ing_box, text=", ".join(selected_ingredients), font=ELEGANT_FONT, wraplength=320, justify="left", bg="#ffffff").pack(anchor="w", pady=(4,0))

    # Available recipes list
    list_frame = tk.Frame(recipe_left_frame, bg="#ffffff", bd=0)
    list_frame.pack(fill="both", expand=True, padx=10, pady=(0,8))
    list_canvas = tk.Canvas(list_frame, bg="#ffffff", highlightthickness=0)
    scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=list_canvas.yview)
    scrollable_frame = tk.Frame(list_canvas, bg="#ffffff")
    scrollable_frame.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
    window = list_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    list_canvas.configure(yscrollcommand=scrollbar.set)
    list_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Fill buttons
    for r in recipes_to_show:
        btn = tk.Button(scrollable_frame, text=r.get("name", "Unnamed"), font=ELEGANT_FONT, width=36, anchor="w",
                        relief=tk.FLAT, bd=0,
                        command=lambda recipe=r: update_instruction_box(recipe))
        btn.pack(pady=6, anchor="w", fill="x", padx=4)

    # Right side: Instructions area (scrolledtext)
    global instruction_box
    instruction_box = scrolledtext.ScrolledText(recipe_right_frame, wrap=tk.WORD, width=50, height=25, font=ELEGANT_FONT)
    instruction_box.pack(fill="both", expand=True, padx=8, pady=8)
    instruction_box.insert(tk.END, "Select a recipe to view instructions")
    instruction_box.config(state=tk.DISABLED)

def update_instruction_box(recipe):
    if instruction_box is None:
        return
    instruction_box.config(state=tk.NORMAL)
    instruction_box.delete(1.0, tk.END)
    instruction_box.insert(tk.END, f"{recipe.get('name','')}:\n\n")
    instruction_box.insert(tk.END, "Ingredients:\n")
    for ing in recipe.get('ingredients', []):
        instruction_box.insert(tk.END, f"• {ing}\n")
    instruction_box.insert(tk.END, "\nInstructions:\n")
    instr = recipe.get('instructions', "")
    if isinstance(instr, list):
        for step in instr:
            step = step.strip()
            if step:
                instruction_box.insert(tk.END, f"• {step}\n")
    else:
        for step in str(instr).split("\n"):
            step = step.strip()
            if step:
                instruction_box.insert(tk.END, f"• {step}\n")
    instruction_box.config(state=tk.DISABLED)

# ---------- Root Window ----------
root = tk.Tk()
root.title("Meal Planner Software")
root.geometry("950x750")
root.configure(bg=PASTEL_BG)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# ---------- Frames ----------
main_menu = tk.Frame(root, bg=PASTEL_BG)
daily_meal_frame = tk.Frame(root, bg=PASTEL_BG)
meal_suggestion_frame = tk.Frame(root, bg=PASTEL_BG)  # reused for both make_meal results and other suggestion view

for frame in (main_menu, daily_meal_frame, meal_suggestion_frame):
    frame.grid(row=0, column=0, sticky="nsew")

# ---------- Main Menu ----------
title = tk.Label(main_menu, text="Meal Planner", font=HEADER_FONT, bg=PASTEL_BG, fg=TEXT_COLOR)
title.pack(pady=60)

btn1 = RoundedButton(main_menu, text="Available Ingredients", font=SUBHEADER_FONT, width=25, height=2)
btn1.pack(pady=20)

btn2 = RoundedButton(main_menu, text="Manage Meal Plans", font=SUBHEADER_FONT, width=25, height=2)
btn2.pack(pady=20)

btn3 = RoundedButton(main_menu, text="Daily Meal Suggestions", font=SUBHEADER_FONT, width=25, height=2,
                 command=lambda: [show_frame(daily_meal_frame), generate_daily_meals()])
btn3.pack(pady=20)

# ---------- Ingredients Page ----------
ingredient_vars = {}
buttons = {}
ingredients = {
    "Grains & Starches": ["Rice", "Pasta", "Bread", "Potatoes", "Flour"],
    "Protein": ["Chicken", "Beef", "Fish", "Eggs", "Pork"],
    "Vegetables": ["Tomatoes", "Carrots", "Cabbage", "Onion", "Cauliflower"],
    "Fruits": ["Bananas", "Apples", "Oranges", "Coconut", "Lemons"]
}

outer_ing_frame = tk.Frame(root, bg=PASTEL_BG)
outer_ing_frame.grid(row=0, column=0, sticky="nsew")

canvas = tk.Canvas(outer_ing_frame, bg="#ffffff", highlightthickness=0)
vscroll = tk.Scrollbar(outer_ing_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=vscroll.set)

canvas.grid(row=0, column=0, sticky="nsew")
vscroll.grid(row=0, column=1, sticky="ns")

outer_ing_frame.grid_rowconfigure(0, weight=1)
outer_ing_frame.grid_columnconfigure(0, weight=1)

ingredients_frame = tk.Frame(canvas, bg="#ffffff")
window_id = canvas.create_window((0, 0), window=ingredients_frame, anchor="nw")

def on_canvas_configure(event):
    canvas.itemconfig(window_id, width=event.width)
    canvas.configure(scrollregion=canvas.bbox("all"))

canvas.bind("<Configure>", on_canvas_configure)

def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

ingredients_frame.bind("<Configure>", on_frame_configure)

for c in range(4):
    ingredients_frame.grid_columnconfigure(c, weight=1, uniform="ingcol")

tk.Label(ingredients_frame, text="Choose ingredients", font=HEADER_FONT, fg=TEXT_COLOR,
         bg="#ffffff").grid(row=0, column=0, columnspan=4, pady=(20, 15), sticky="n")

max_rows = max(len(items) for items in ingredients.values())
for r in range(max_rows):
    col = 0
    for category, items in ingredients.items():
        if r < len(items):
            item = items[r]
            var = tk.BooleanVar()
            ingredient_vars[item] = var
            btn = IngredientButton(
                ingredients_frame, text=item, variable=var,
                command=lambda i=item, v=var: toggle_ingredient(i, v, buttons[i][0])
            )
            btn.grid(row=r+1, column=col, padx=8, pady=6, sticky="nsew")
            buttons[item] = (btn, None)
        col += 1

# Inline edit function for custom ingredients
def edit_ingredient_inline(old_name):
    btn, edit_btn = buttons[old_name]
    if edit_btn:
        try:
            edit_btn.place_forget()
        except Exception:
            pass

    entry = tk.Entry(ingredients_frame, font=ELEGANT_FONT, width=15, bd=2, relief=tk.GROOVE)
    entry.insert(0, old_name)
    entry.grid(row=btn.grid_info()["row"], column=btn.grid_info()["column"],
               padx=8, pady=6, sticky="nsew", ipady=8)
    btn.grid_forget()

    def save_new_name(event=None):
        new_name = entry.get().strip()
        if not new_name:
            messagebox.showwarning("Empty", "Name cannot be empty.")
            entry.focus()
            return
        if new_name in ingredient_vars and new_name != old_name:
            messagebox.showwarning("Duplicate", f"'{new_name}' already exists!")
            entry.focus()
            return

        ingredient_vars[new_name] = ingredient_vars.pop(old_name)
        buttons[new_name] = buttons.pop(old_name)

        var = ingredient_vars[new_name]
        new_btn = IngredientButton(
            ingredients_frame, text=new_name, variable=var,
            command=lambda i=new_name, v=var: toggle_ingredient(i, v, buttons[i][0])
        )
        new_btn.grid(row=entry.grid_info()["row"], column=entry.grid_info()["column"],
                     padx=8, pady=6, sticky="nsew")

        new_edit_btn = tk.Button(
            ingredients_frame, text="✎", font=("Century Gothic", 16),
            fg="black", bg=PASTEL_BG, bd=0, relief=tk.FLAT,
            command=lambda n=new_name: edit_ingredient_inline(n)
        )
        new_edit_btn.place(in_=new_btn, relx=1.0, x=-8, y=2, anchor="ne")

        buttons[new_name] = (new_btn, new_edit_btn)
        entry.destroy()
        update_make_meal_button()
        if var.get():
             toggle_ingredient(new_name, var, new_btn)

    entry.bind("<Return>", save_new_name)
    entry.bind("<FocusOut>", save_new_name)
    entry.focus()

# Dynamic custom ingredients
custom_row = max_rows + 1
custom_col = 0

def add_more_textbox(event=None):
    global custom_row, custom_col
    name = others_entry.get().strip()
    if not name:
        return
    if name in ingredient_vars:
        messagebox.showinfo("Duplicate", f"'{name}' already exists!")
        others_entry.delete(0, tk.END)
        return

    var = tk.BooleanVar()
    ingredient_vars[name] = var

    btn = IngredientButton(
        ingredients_frame, text=name, variable=var,
        command=lambda i=name, v=var: toggle_ingredient(i, v, buttons[i][0])
    )
    btn.grid(row=custom_row, column=custom_col, padx=8, pady=6, sticky="nsew")

    edit_btn = tk.Button(
        ingredients_frame, text="✎", font=("Century Gothic", 16),
        fg="black", bg=PASTEL_BG, bd=0, relief=tk.FLAT,
        command=lambda n=name: edit_ingredient_inline(n)
    )
    edit_btn.place(in_=btn, relx=1.0, x=-8, y=2, anchor="ne")

    buttons[name] = (btn, edit_btn)
    others_entry.delete(0, tk.END)

    custom_col += 1
    if custom_col >= 4:
        custom_col = 0
        custom_row += 1

    ingredients_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.yview_moveto(1.0)

# Bottom fixed controls
bottom_fixed_frame = tk.Frame(outer_ing_frame, bg=PASTEL_BG)
bottom_fixed_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 15))
bottom_fixed_frame.grid_columnconfigure(0, weight=1)

others_label = tk.Label(bottom_fixed_frame, text="Others:", font=ELEGANT_FONT, bg=PASTEL_BG, fg=TEXT_COLOR)
others_label.pack(side="left", padx=(10, 6))

others_entry = tk.Entry(bottom_fixed_frame, font=ELEGANT_FONT, width=30, bd=1, relief=tk.SOLID)
others_entry.pack(side="left", padx=5, ipady=4)
others_entry.bind("<Return>", add_more_textbox)

add_btn = RoundedButton(bottom_fixed_frame, text="+", font=("Century Gothic", 12, "bold"), width=3,
                    command=lambda: add_more_textbox())
add_btn.pack(side="left", padx=6)

instruction_label = tk.Label(bottom_fixed_frame, text="Please choose at least 2 ingredients",
                             font=ELEGANT_FONT, fg="#ff6961", bg=PASTEL_BG)
instruction_label.pack(side="left", padx=12)

make_meal_btn = RoundedButton(bottom_fixed_frame, text="Make Meal", font=("Century Gothic", 14, "bold"),
                          state="disabled", command=make_meal, bg=PASTEL_BG, fg=TEXT_COLOR)
make_meal_btn.pack(side="right", padx=12)

back_btn = RoundedButton(bottom_fixed_frame, text="🏠", font=("Century Gothic", 14, "bold"), width=3,
                     command=lambda: show_frame(main_menu))
back_btn.pack(side="right", padx=6)

btn1.config(command=lambda: show_frame(outer_ing_frame))

# ---------- Meal Suggestions Page (where make_meal shows results) ----------
header_suggestion = tk.Label(meal_suggestion_frame, text="Meal suggestions for you",
                             font=HEADER_FONT, bg=PASTEL_BG, fg=TEXT_COLOR)
header_suggestion.pack(pady=18)

nav_frame_suggest = tk.Frame(meal_suggestion_frame, bg=PASTEL_BG)
nav_frame_suggest.pack(pady=8)

back_suggestion_btn = RoundedButton(nav_frame_suggest, text="← Back to Ingredients",
                                font=ELEGANT_FONT,
                                command=lambda: show_frame(outer_ing_frame))
back_suggestion_btn.pack(side="left", padx=10)

back_to_main_btn = RoundedButton(nav_frame_suggest, text="🏠",
                             font=ELEGANT_FONT,
                             command=lambda: show_frame(main_menu))
back_to_main_btn.pack(side="left", padx=10)

# Create left & right frames inside meal_suggestion_frame for recipe list + instructions
recipe_top_holder = tk.Frame(meal_suggestion_frame, bg=PASTEL_BG)
recipe_top_holder.pack(fill="both", expand=True, padx=10, pady=(10,8))

recipe_left_frame = tk.Frame(recipe_top_holder, bg="#ffffff", bd=0, highlightthickness=1, highlightbackground="#DADADA")
recipe_left_frame.pack(side="left", fill="y", padx=(10,6), pady=6, ipadx=6, ipady=6)

recipe_right_frame = tk.Frame(recipe_top_holder, bg="#ffffff", bd=0, highlightthickness=1, highlightbackground="#DADADA")
recipe_right_frame.pack(side="right", fill="both", expand=True, padx=(6,10), pady=6)

# ---------- Daily Meal Suggestions (cards styled like draft) ----------
header = tk.Label(daily_meal_frame, text="Today's Meals Suggestion", font=HEADER_FONT, bg=PASTEL_BG, fg=TEXT_COLOR)
header.pack(pady=22)

cards_container = tk.Frame(daily_meal_frame, bg=PASTEL_BG)
cards_container.pack(fill='both', expand=True)

for c in range(3):
    cards_container.grid_columnconfigure(c, weight=1, uniform="meal")
cards_container.grid_rowconfigure(0, weight=1)

# --- Recipe Detail Frame (used when clicking a card) ---
recipe_frame = tk.Frame(root, bg=PASTEL_BG)
recipe_frame.grid(row=0, column=0, sticky="nsew")

recipe_title_label = tk.Label(recipe_frame, text="", font=("Century Gothic", 26, "bold"), bg=PASTEL_BG, fg=TEXT_COLOR)
recipe_title_label.pack(pady=40)

back_from_recipe_btn = RoundedButton(recipe_frame, text="← Back to Daily Suggestions", font=ELEGANT_FONT,
                                 command=lambda: show_frame(daily_meal_frame))
back_from_recipe_btn.pack(pady=10)

detail_text = tk.Text(recipe_frame, font=ELEGANT_FONT, bg="#ffffff", bd=0, height=20, wrap="word")
detail_text.pack(padx=20, pady=12, fill="both", expand=True)

def open_recipe(meal_name):
    # Try to find recipe by name in recipes; otherwise show the name only
    recipe_title_label.config(text=f"{meal_name} Recipe")
    detail_text.config(state=tk.NORMAL)
    detail_text.delete("1.0", tk.END)
    found = None
    for r in recipes:
        if r.get("name") == meal_name:
            found = r
            break
    if found:
        detail_text.insert(tk.END, "Ingredients:\n")
        for ing in found.get("ingredients", []):
            detail_text.insert(tk.END, f"• {ing}\n")
        detail_text.insert(tk.END, "\nInstructions:\n")
        instr = found.get("instructions", "")
        if isinstance(instr, list):
            for step in instr:
                step = step.strip()
                if step:
                    detail_text.insert(tk.END, f"• {step}\n")
        else:
            for step in str(instr).split("\n"):
                step = step.strip()
                if step:
                    detail_text.insert(tk.END, f"• {step}\n")
    else:
        detail_text.insert(tk.END, "(No detailed recipe found)")
    detail_text.config(state=tk.DISABLED)
    show_frame(recipe_frame)

# Create modern card function (returns outer frame and label used to show recipe name/content)
def create_meal_card(parent, title):
    shadow_frame = tk.Frame(parent, bg="#e0e0e0", bd=0)
    frame = tk.Frame(shadow_frame, bd=0, relief=tk.GROOVE, bg="#ffffff", padx=20, pady=20, width=260, height=220)
    frame.pack(padx=5, pady=5)
    shadow_frame.pack_propagate(False)
    frame.pack_propagate(False)

    lbl_title = tk.Label(frame, text=title, font=("Century Gothic", 18, "bold"), bg="#ffffff", fg=TEXT_COLOR)
    lbl_title.pack(pady=(0, 12))

    lbl_content = tk.Label(frame, text="(waiting)", font=("Century Gothic", 14), bg="#ffffff", fg=TEXT_COLOR, wraplength=220, justify="center")
    lbl_content.pack(pady=(8,0))

    def on_enter(event):
        frame.config(bg=HOVER_COLOR)
        lbl_title.config(bg=HOVER_COLOR)
        lbl_content.config(bg=HOVER_COLOR)
        shadow_frame.config(bg=PRIMARY_COLOR)

    def on_leave(event):
        frame.config(bg="#ffffff")
        lbl_title.config(bg="#ffffff")
        lbl_content.config(bg="#ffffff")
        shadow_frame.config(bg="#e0e0e0")

    for widget in (frame, lbl_title, lbl_content):
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<Button-1>", lambda e, lbl=lbl_content: open_recipe(lbl.cget("text")))

    return shadow_frame, lbl_content

# Meal cards for breakfast/lunch/dinner
breakfast_frame, breakfast_label = create_meal_card(cards_container, "Breakfast")
breakfast_frame.grid(row=0, column=0, padx=24, pady=40, sticky="nsew")

lunch_frame, lunch_label = create_meal_card(cards_container, "Lunch")
lunch_frame.grid(row=0, column=1, padx=24, pady=40, sticky="nsew")

dinner_frame, dinner_label = create_meal_card(cards_container, "Dinner")
dinner_frame.grid(row=0, column=2, padx=24, pady=40, sticky="nsew")

def update_daily_meals_with_recipes(breakfast, lunch, dinner):
    breakfast_label.config(text=breakfast.get("name", "(no name)") if isinstance(breakfast, dict) else str(breakfast))
    lunch_label.config(text=lunch.get("name", "(no name)") if isinstance(lunch, dict) else str(lunch))
    dinner_label.config(text=dinner.get("name", "(no name)") if isinstance(dinner, dict) else str(dinner))

def generate_daily_meals():
    if not recipes:
        update_daily_meals_with_recipes("No recipes", "No recipes", "No recipes")
        return
    breakfast = random.choice(recipes)
    lunch = random.choice(recipes)
    dinner = random.choice(recipes)
    update_daily_meals_with_recipes(breakfast, lunch, dinner)

regen_btn = RoundedButton(daily_meal_frame, text="Other Suggestions", font=ELEGANT_FONT,
                      command=generate_daily_meals)
regen_btn.pack(pady=12)

back_daily_btn = RoundedButton(daily_meal_frame, text="🏠", font=("Century Gothic", 14, "bold"), width=3,
                           command=lambda: show_frame(main_menu))
back_daily_btn.pack(pady=18)

# ===================== Manage Meal Plans (unchanged core, styled to draft) =====================
MEALS_FILE = "meals.json"
saved_meals = {}
editor_mode = "create"
editing_original_name = None

def load_saved_meals():
    if not os.path.exists(MEALS_FILE):
        return {}
    try:
        with open(MEALS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        clean = {}
        if isinstance(data, dict):
            for name, value in data.items():
                if not isinstance(name, str):
                    continue
                if isinstance(value, list):
                    ings = [str(x) for x in value]
                    clean[name] = {"ingredients": ings, "description": ""}
                elif isinstance(value, dict):
                    ings = value.get("ingredients", [])
                    desc = value.get("description", "")
                    if isinstance(ings, list):
                        ings = [str(x) for x in ings]
                    else:
                        ings = []
                    clean[name] = {"ingredients": ings, "description": str(desc)}
        return clean
    except Exception:
        return {}

def save_saved_meals():
    try:
        with open(MEALS_FILE, "w", encoding="utf-8") as f:
            json.dump(saved_meals, f, indent=2, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Save error", f"Couldn't save meals.json\n\n{e}")

saved_meals = load_saved_meals()

manage_menu_frame = tk.Frame(root, bg=PASTEL_BG)
saved_list_frame = tk.Frame(root, bg=PASTEL_BG)
meal_editor_frame = tk.Frame(root, bg=PASTEL_BG)

for f in (manage_menu_frame, saved_list_frame, meal_editor_frame):
    f.grid(row=0, column=0, sticky="nsew")

tk.Label(
    manage_menu_frame, text="Manage Meal Plans", font=HEADER_FONT, bg=PASTEL_BG, fg=TEXT_COLOR
).pack(pady=30)

RoundedButton(manage_menu_frame, text="Add New Meal", font=SUBHEADER_FONT,
              width=22, height=2, command=lambda: open_meal_editor()).pack(pady=12)

RoundedButton(manage_menu_frame, text="Saved Meals", font=SUBHEADER_FONT,
              width=22, height=2, command=lambda: [refresh_saved_list(), show_frame(saved_list_frame)]).pack(pady=12)

RoundedButton(manage_menu_frame, text="🏠", font=ELEGANT_FONT,
              command=lambda: show_frame(main_menu)).pack(pady=26)

# Saved list layout
saved_list_frame.grid_columnconfigure(0, weight=1)
saved_list_frame.grid_columnconfigure(1, weight=1)
saved_list_frame.grid_rowconfigure(1, weight=1)

left_card = tk.Frame(saved_list_frame, bg="#ffffff", bd=0, highlightthickness=1, highlightbackground="#DADADA")
left_card.grid(row=1, column=0, sticky="nsew", padx=(30, 10), pady=(10, 20))
left_card.grid_columnconfigure(0, weight=1)
left_card.grid_rowconfigure(2, weight=1)

right_card = tk.Frame(saved_list_frame, bg="#ffffff", bd=0, highlightthickness=1, highlightbackground="#DADADA")
right_card.grid(row=1, column=1, sticky="nsew", padx=(10, 30), pady=(10, 20))
right_card.grid_columnconfigure(0, weight=1)
right_card.grid_rowconfigure(1, weight=1)
right_card.grid_rowconfigure(3, weight=1)

title_lbl = tk.Label(saved_list_frame, text="Saved Meals", font=("Century Gothic", 20, "bold"), bg=PASTEL_BG, fg=TEXT_COLOR)
title_lbl.grid(row=0, column=0, columnspan=2, pady=(15, 5))

search_var = tk.StringVar()

search_row = tk.Frame(left_card, bg="#ffffff")
search_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 6))
search_row.grid_columnconfigure(0, weight=0)
search_row.grid_columnconfigure(1, weight=1)

tk.Label(search_row, text="Search meal:", font=ELEGANT_FONT, bg="#ffffff").grid(row=0, column=0, sticky="w", padx=(0, 8))
search_entry = tk.Entry(search_row, textvariable=search_var, font=ELEGANT_FONT, bd=1, relief=tk.SOLID)
search_entry.grid(row=0, column=1, sticky="ew")

listbox = tk.Listbox(left_card, font=("Century Gothic", 13), bd=0, highlightthickness=0)
listbox.grid(row=2, column=0, sticky="nsew", padx=(12, 6), pady=(0, 12))
scroll = tk.Scrollbar(left_card, orient="vertical", command=listbox.yview)
scroll.grid(row=2, column=1, sticky="ns", padx=(0, 12), pady=(0, 12))
listbox.configure(yscrollcommand=scroll.set)

tk.Label(right_card, text="Ingredients:", font=ELEGANT_FONT, bg="#ffffff").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

ing_frame = tk.Frame(right_card, bg="#ffffff")
ing_frame.grid(row=1, column=0, sticky="nsew", padx=12)
ing_frame.grid_rowconfigure(0, weight=1)
ing_frame.grid_columnconfigure(0, weight=1)

view_ingredients_text = tk.Text(ing_frame, font=ELEGANT_FONT, height=6, state="disabled", bd=0, relief=tk.FLAT)
view_ingredients_text.grid(row=0, column=0, sticky="nsew")
ing_scroll = tk.Scrollbar(ing_frame, orient="vertical", command=view_ingredients_text.yview)
ing_scroll.grid(row=0, column=1, sticky="ns")
view_ingredients_text.configure(yscrollcommand=ing_scroll.set)

tk.Label(right_card, text="Instructions:", font=ELEGANT_FONT, bg="#ffffff").grid(row=2, column=0, sticky="w", padx=12, pady=(8, 4))

desc_frame = tk.Frame(right_card, bg="#ffffff")
desc_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))
desc_frame.grid_rowconfigure(0, weight=1)
desc_frame.grid_columnconfigure(0, weight=1)

view_description_text = tk.Text(desc_frame, font=ELEGANT_FONT, wrap="word", state="disabled", bd=0, relief=tk.FLAT)
view_description_text.grid(row=0, column=0, sticky="nsew")
desc_scroll = tk.Scrollbar(desc_frame, orient="vertical", command=view_description_text.yview)
desc_scroll.grid(row=0, column=1, sticky="ns")
view_description_text.configure(yscrollcommand=desc_scroll.set)

_bind_mousewheel(listbox, lambda d: listbox.yview_scroll(d, "units"))
_bind_mousewheel(view_ingredients_text, lambda d: view_ingredients_text.yview_scroll(d, "units"))
_bind_mousewheel(view_description_text, lambda d: view_description_text.yview_scroll(d, "units"))

def refresh_saved_list():
    listbox.delete(0, tk.END)
    query = search_var.get().strip().lower()
    for name in sorted(saved_meals.keys(), key=str.lower):
        if not query or query in name.lower():
            listbox.insert(tk.END, name)

def _update_details(name):
    view_ingredients_text.config(state="normal")
    view_ingredients_text.delete("1.0", tk.END)
    view_description_text.config(state="normal")
    view_description_text.delete("1.0", tk.END)

    if not name:
        view_ingredients_text.insert(tk.END, "(Select a meal)")
    else:
        data = saved_meals.get(name)
        if not data:
            view_ingredients_text.insert(tk.END, "(No data)")
        else:
            ings = data.get("ingredients", [])
            desc = data.get("description", "")

            if ings:
                for ing in ings:
                    view_ingredients_text.insert(tk.END, f"• {ing}\n")
            else:
                view_ingredients_text.insert(tk.END, "(No ingredients)")

            if desc:
                view_description_text.insert(tk.END, desc)
            else:
                view_description_text.insert(tk.END, "(No description)")

    view_ingredients_text.config(state="disabled")
    view_description_text.config(state="disabled")

def on_select_meal(event=None):
    sel = listbox.curselection()
    name = listbox.get(sel[0]) if sel else None
    _update_details(name)

listbox.bind("<<ListboxSelect>>", on_select_meal)
search_var.trace_add("write", lambda *args: (refresh_saved_list(), _update_details(None)))

btn_row = tk.Frame(saved_list_frame, bg=PASTEL_BG)
btn_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=30, pady=(0, 20))
btn_row.grid_columnconfigure(0, weight=0)
btn_row.grid_columnconfigure(1, weight=0)
btn_row.grid_columnconfigure(2, weight=1)
btn_row.grid_columnconfigure(3, weight=0)

def delete_selected_meal():
    sel = listbox.curselection()
    if not sel:
        messagebox.showinfo("Delete", "Please select a meal to delete.")
        return
    name = listbox.get(sel[0])
    if messagebox.askyesno("Confirm Delete", f"Delete '{name}'?"):
        saved_meals.pop(name, None)
        save_saved_meals()
        refresh_saved_list()
        _update_details(None)

def edit_selected_meal():
    sel = listbox.curselection()
    if not sel:
        messagebox.showinfo("Edit", "Please select a meal to edit.")
        return
    name = listbox.get(sel[0])
    open_meal_editor(existing_name=name)

RoundedButton(btn_row, text="Edit", width=12, command=edit_selected_meal).grid(row=0, column=0, sticky="w", padx=(0, 10))
RoundedButton(btn_row, text="Delete", width=12, command=delete_selected_meal).grid(row=0, column=1, sticky="w", padx=(0, 10))
RoundedButton(btn_row, text="Back", width=12, command=lambda: show_frame(manage_menu_frame)).grid(row=0, column=3, sticky="e")

# Meal editor (create/edit)
new_meal_vars = {}
meal_editor_frame.grid_columnconfigure(0, weight=1)
meal_editor_frame.grid_columnconfigure(1, weight=1)

tk.Label(meal_editor_frame, text="Meal Editor", font=HEADER_FONT, bg=PASTEL_BG, fg=TEXT_COLOR).grid(
    row=0, column=0, columnspan=2, pady=(20, 5)
)
editor_hint = tk.Label(meal_editor_frame, text="", fg="gray", bg=PASTEL_BG)
editor_hint.grid(row=1, column=0, columnspan=2, pady=(0, 10))

tk.Label(meal_editor_frame, text="Meal name:", font=ELEGANT_FONT, bg=PASTEL_BG).grid(
    row=2, column=0, sticky="e", padx=(40, 8), pady=5
)
name_entry = tk.Entry(meal_editor_frame, font=("Century Gothic", 13), width=28)
name_entry.grid(row=2, column=1, sticky="w", pady=5)

content_frame = tk.Frame(meal_editor_frame, bg=PASTEL_BG)
content_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=40, pady=(5, 10))
content_frame.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=1)
content_frame.grid_rowconfigure(0, weight=1)

ingredients_panel = tk.Frame(content_frame, bd=0, bg="#ffffff", highlightthickness=1, highlightbackground="#DADADA")
ingredients_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
ingredients_panel.grid_columnconfigure(0, weight=1)
ingredients_panel.grid_rowconfigure(1, weight=1)

tk.Label(ingredients_panel, text="Ingredients", font=ELEGANT_FONT, bg="#ffffff").grid(
    row=0, column=0, sticky="w", padx=10, pady=(8, 4)
)

selector_wrap = tk.Frame(ingredients_panel, bg="#ffffff")
selector_wrap.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
selector_wrap.grid_rowconfigure(0, weight=1)
selector_wrap.grid_columnconfigure(0, weight=1)

canvas_editor = tk.Canvas(selector_wrap, highlightthickness=0, bg="#ffffff")
canvas_editor.grid(row=0, column=0, sticky="nsew")
ybar = tk.Scrollbar(selector_wrap, orient="vertical", command=canvas_editor.yview)
ybar.grid(row=0, column=1, sticky="ns")
canvas_editor.configure(yscrollcommand=ybar.set)

inner_editor = tk.Frame(canvas_editor, bg="#ffffff")
_inner_window_editor = canvas_editor.create_window((0, 0), window=inner_editor, anchor="nw")

def _on_frame_configure_editor(event):
    canvas_editor.configure(scrollregion=canvas_editor.bbox("all"))

inner_editor.bind("<Configure>", _on_frame_configure_editor)

def _on_canvas_configure_editor(event):
    canvas_editor.itemconfigure(_inner_window_editor, width=event.width)

canvas_editor.bind("<Configure>", _on_canvas_configure_editor)

EDITOR_COLS = 2

def populate_selector(prechecked=None):
    for w in inner_editor.winfo_children():
        w.destroy()
    new_meal_vars.clear()

    pre = set(prechecked or [])
    all_ings = sorted(set(ingredient_vars.keys()) | pre, key=str.lower)

    for c in range(EDITOR_COLS):
        inner_editor.grid_columnconfigure(c, weight=1)

    for idx, ing in enumerate(all_ings):
        r, c = divmod(idx, EDITOR_COLS)
        var = tk.BooleanVar(value=(ing in pre))
        new_meal_vars[ing] = var
        cb = tk.Checkbutton(
            inner_editor, text=ing, variable=var,
            indicatoron=False, anchor="w", padx=10
        )
        cb.grid(row=r, column=c, sticky="ew", padx=6, pady=4)

populate_selector()

description_panel = tk.Frame(content_frame, bd=0, bg="#ffffff", highlightthickness=1, highlightbackground="#DADADA")
description_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
description_panel.grid_columnconfigure(0, weight=1)
description_panel.grid_rowconfigure(1, weight=1)

tk.Label(description_panel, text="Type your instructions here", font=ELEGANT_FONT, bg="#ffffff").grid(
    row=0, column=0, sticky="w", padx=10, pady=(8, 4)
)

description_text = tk.Text(description_panel, wrap="word", font=ELEGANT_FONT, height=10, bd=0, relief=tk.FLAT)
description_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

bottom_row = tk.Frame(meal_editor_frame, bg=PASTEL_BG)
bottom_row.grid(row=4, column=0, columnspan=2, sticky="ew", padx=40, pady=(0, 10))
bottom_row.grid_columnconfigure(0, weight=1)
bottom_row.grid_columnconfigure(1, weight=0)

custom_row_editor = tk.Frame(bottom_row, bg=PASTEL_BG)
custom_row_editor.grid(row=0, column=0, sticky="w")

tk.Label(custom_row_editor, text="Add ingredient:", font=("Century Gothic", 11, "bold"), bg=PASTEL_BG).pack(
    side="left", padx=(0, 8)
)
custom_entry = tk.Entry(custom_row_editor, font=ELEGANT_FONT, width=22)
custom_entry.pack(side="left")

def add_custom_to_editor(event=None):
    name = custom_entry.get().strip()
    if not name:
        return
    if name in new_meal_vars:
        messagebox.showinfo("Duplicate", f"'{name}' is already listed.")
        custom_entry.delete(0, tk.END)
        return

    new_meal_vars[name] = tk.BooleanVar(value=True)
    idx = len(new_meal_vars) - 1
    r, c = divmod(idx, EDITOR_COLS)
    cb = tk.Checkbutton(
        inner_editor, text=name, variable=new_meal_vars[name],
        indicatoron=False, anchor="w", padx=10
    )
    cb.grid(row=r, column=c, sticky="ew", padx=6, pady=4)
    custom_entry.delete(0, tk.END)

custom_entry.bind("<Return>", add_custom_to_editor)
RoundedButton(custom_row_editor, text="+", width=3, command=add_custom_to_editor).pack(side="left", padx=6)

editor_btns = tk.Frame(bottom_row, bg=PASTEL_BG)
editor_btns.grid(row=0, column=1, sticky="e")

err_lbl = tk.Label(meal_editor_frame, text="", fg="red", bg=PASTEL_BG)
err_lbl.grid(row=5, column=0, columnspan=2, pady=(0, 6))

def _collect_selection():
    return [k for k, v in new_meal_vars.items() if v.get()]

def save_meal_from_editor():
    name = name_entry.get().strip()
    chosen = _collect_selection()
    desc = description_text.get("1.0", tk.END).strip()

    if not name:
        err_lbl.config(text="Please enter a meal name.")
        return
    if len(chosen) < 2:
        err_lbl.config(text="Select at least 2 ingredients.")
        return

    global saved_meals, editing_original_name

    if editor_mode == "edit" and editing_original_name and name != editing_original_name:
        if name in saved_meals:
            messagebox.showerror("Name exists", f"A meal named '{name}' already exists.")
            return
        saved_meals.pop(editing_original_name, None)

    saved_meals[name] = {
        "ingredients": chosen,
        "description": desc,
    }
    save_saved_meals()
    saved_meals.clear()
    saved_meals.update(load_saved_meals())

    refresh_saved_list()
    messagebox.showinfo("Saved", f"Meal '{name}' saved.")
    show_frame(saved_list_frame)

def cancel_editor():
    show_frame(manage_menu_frame)

RoundedButton(editor_btns, text="Save Meal", command=save_meal_from_editor).pack(side="left", padx=8)
RoundedButton(editor_btns, text="Cancel", command=cancel_editor).pack(side="left", padx=8)

def open_meal_editor(existing_name=None):
    global editor_mode, editing_original_name

    if existing_name is None:
        editor_mode = "create"
        editing_original_name = None
        name_entry.delete(0, tk.END)
        description_text.delete("1.0", tk.END)
        populate_selector(prechecked=None)
        editor_hint.config(text="Create a new meal.")
    else:
        editor_mode = "edit"
        editing_original_name = existing_name
        name_entry.delete(0, tk.END)
        name_entry.insert(0, existing_name)

        data = saved_meals.get(existing_name, {})
        ings = data.get("ingredients", [])
        desc = data.get("description", "")

        populate_selector(prechecked=set(ings))
        description_text.delete("1.0", tk.END)
        description_text.insert(tk.END, desc)

        editor_hint.config(text=f"Editing: {existing_name}")

    err_lbl.config(text="")
    show_frame(meal_editor_frame)

btn2.config(command=lambda: show_frame(manage_menu_frame))

# ---------- Start ----------
show_frame(main_menu)
root.mainloop()


