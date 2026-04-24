from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime

# ─────────────────────────────────────────
#  CONNECTION — MongoDB Compass (local)
# ─────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017"
DB_NAME   = "contacthub"

def get_db():
    """Connect to MongoDB and return the database."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("✅ Connected to MongoDB Compass!")
        return client[DB_NAME]
    except ConnectionFailure:
        print("❌ Connection failed. Make sure MongoDB Compass is open!")
        return None


# ─────────────────────────────────────────
#  CREATE — Add a new contact
# ─────────────────────────────────────────
def add_contact(db):
    print("\n─── Add Contact ───")
    name  = input("Name    : ").strip()
    phone = input("Phone   : ").strip()
    email = input("Email   : ").strip()
    group = input("Group (family / work / friends / other): ").strip().lower()

    if not name:
        print("❌ Name cannot be empty!")
        return

    contact = {
        "name"       : name,
        "phone"      : phone,
        "email"      : email,
        "group"      : group,
        "created_at" : datetime.now()
    }

    result = db.contacts.insert_one(contact)
    print(f"✅ Contact '{name}' added successfully! (ID: {result.inserted_id})")


# ─────────────────────────────────────────
#  READ — List all contacts (grouped + sorted)
# ─────────────────────────────────────────
def list_contacts(db):
    print("\n─── All Contacts (Grouped & Sorted) ───")

    # sort by group first, then name A→Z inside each group
    contacts = list(db.contacts.find().sort([("group", 1), ("name", 1)]))

    if not contacts:
        print("📭 No contacts yet. Add one first!")
        return

    # group them together
    groups = {}
    for c in contacts:
        grp = c.get("group", "other").capitalize()
        if grp not in groups:
            groups[grp] = []
        groups[grp].append(c)

    total = 0
    for grp, members in groups.items():
        print(f"\n  ┌── {grp} ({len(members)}) ──────────────────────────────────────")
        print(f"  │  {'No.':<5} {'Name':<20} {'Phone':<15} {'Email':<25}")
        print(f"  │  {'─'*63}")
        for i, c in enumerate(members, 1):
            print(f"  │  {i:<5} {c.get('name','—'):<20} {c.get('phone','—'):<15} {c.get('email','—'):<25}")
        print(f"  └{'─'*65}")
        total += len(members)

    print(f"\n  Total: {total} contact(s) across {len(groups)} group(s)")


# ─────────────────────────────────────────
#  SEARCH — Find contact by name
# ─────────────────────────────────────────
def search_contact(db):
    print("\n─── Search Contact ───")
    query = input("Enter name to search: ").strip()

    if not query:
        print("❌ Please enter a name to search!")
        return

    results = list(db.contacts.find(
        {"name": {"$regex": query, "$options": "i"}}
    ))

    if not results:
        print(f"❌ No contacts found matching '{query}'.")
        return

    print(f"\nFound {len(results)} result(s):\n")
    for c in results:
        print(f"  Name  : {c.get('name',  '—')}")
        print(f"  Phone : {c.get('phone', '—')}")
        print(f"  Email : {c.get('email', '—')}")
        print(f"  Group : {c.get('group', '—')}")
        print("  " + "─" * 30)


# ─────────────────────────────────────────
#  UPDATE — Edit a contact by name
# ─────────────────────────────────────────
def update_contact(db):
    print("\n─── Update Contact ───")
    name = input("Enter the name of contact to update: ").strip()

    contact = db.contacts.find_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}}
    )

    if not contact:
        print(f"❌ No contact named '{name}' found.")
        return

    print(f"\nFound: {contact['name']} | {contact.get('phone','—')} | {contact.get('email','—')}")
    print("Press Enter to keep the existing value.\n")

    new_name  = input(f"New name  [{contact.get('name',  '')}]: ").strip()
    new_phone = input(f"New phone [{contact.get('phone', '')}]: ").strip()
    new_email = input(f"New email [{contact.get('email', '')}]: ").strip()
    new_group = input(f"New group [{contact.get('group', '')}]: ").strip()

    updates = {}
    if new_name  : updates["name"]  = new_name
    if new_phone : updates["phone"] = new_phone
    if new_email : updates["email"] = new_email
    if new_group : updates["group"] = new_group

    if not updates:
        print("⚠️  No changes made.")
        return

    db.contacts.update_one({"_id": contact["_id"]}, {"$set": updates})
    print(f"✅ Contact '{contact['name']}' updated successfully!")


# ─────────────────────────────────────────
#  DELETE — Remove a contact by name
# ─────────────────────────────────────────
def delete_contact(db):
    print("\n─── Delete Contact ───")
    name = input("Enter the name of contact to delete: ").strip()

    contact = db.contacts.find_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}}
    )

    if not contact:
        print(f"❌ No contact named '{name}' found.")
        return

    print(f"\nFound: {contact['name']} | {contact.get('phone','—')} | {contact.get('email','—')}")
    confirm = input("Are you sure you want to delete? (yes / no): ").strip().lower()

    if confirm != "yes":
        print("❌ Deletion cancelled.")
        return

    db.contacts.delete_one({"_id": contact["_id"]})
    print(f"🗑️  Contact '{contact['name']}' deleted successfully!")


# ─────────────────────────────────────────
#  FILTER — Contacts by group
# ─────────────────────────────────────────
def filter_by_group(db):
    print("\n─── Filter by Group ───")
    group = input("Enter group (family / work / friends / other): ").strip().lower()

    results = list(db.contacts.find({"group": group}).sort("name", 1))

    if not results:
        print(f"📭 No contacts found in group '{group}'.")
        return

    print(f"\nContacts in '{group}' group:\n")
    for c in results:
        print(f"  • {c.get('name','—'):<20} | {c.get('phone','—'):<15} | {c.get('email','—')}")


# ─────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────
def main():
    print("=" * 40)
    print("    Welcome to ContactHub 📒")
    print("=" * 40)

    db = get_db()
    if db is None:
        return

    while True:
        print("""
  ┌─────────────────────────┐
  │        MAIN MENU        │
  ├─────────────────────────┤
  │  1. Add contact         │
  │  2. List all contacts   │
  │  3. Search contact      │
  │  4. Update contact      │
  │  5. Delete contact      │
  │  6. Filter by group     │
  │  0. Exit                │
  └─────────────────────────┘""")

        choice = input("\n  Choose an option: ").strip()

        if   choice == "1": add_contact(db)
        elif choice == "2": list_contacts(db)
        elif choice == "3": search_contact(db)
        elif choice == "4": update_contact(db)
        elif choice == "5": delete_contact(db)
        elif choice == "6": filter_by_group(db)
        elif choice == "0":
            print("\n  Goodbye! See you soon 👋")
            break
        else:
            print("  ⚠️  Invalid option. Please choose 0–6.")


if __name__ == "__main__":
    main()

