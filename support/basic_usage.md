# Use Cases

All information is saved to firebase on "on-blur".

## 1 - Quick Invoice
base_url: index.html

User gets to the index.html, clicks on the "Create Invoice" button, and goes to a blank invoice Page.
The whole invoice "form" is composed by CONTENTEDITABLE fields, and to avoid the blank page, we pre-populate the fields with Sample Data, to indicate where the user should place each info.


## 2 - Recurring Users
base_url: user-index.html

User created his accounted. (oAuth, use firebase Authentication to simplify)


### Adding new Info

New Company is pushed with "New Company Button"
"Add Gov_Registry" button.

"New Client Button" or when the 'client-name' changes, app "pushes" a new client to the list.


### Choosing Related Info

When the user starts to write a client name, the app auto-completes it, and populates the section.


### List Functionalities

- View invoices as "active" and "paid".
- Sort invoices by any column
- Mark invoices as "Paid" or "Archived"
- Download Invoice in PDF







