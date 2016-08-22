# Database Schemas

# ===============
# COMPANY
# ===============
company_info
	name: # STR
	logo: # STR (url)
	contact:
		person # used as the default signature at the invoice
		email # email
		phone
		fax
		address
		city
		state
		country
    postal
	gov_registries: { name, value, tax } # list of objects
  currency # keywords (USD, CAD, BRL, etc)
	bank_info: # text, with line breaks

# ===============
# CLIENT
# ===============
client_info
	name
	vendor_number
  currency
  calculate_taxes
	contact:
    person
		email # email
		phone
		fax
		address
		city
		state
		country
    postal

# ===============
# INVOICE
# ===============
invoice_info
	number # auto-increment
  client # client unique ID
  company # company unique ID
	time_based / value_based # boolean
	service_title
	service_description
	amount # manually added or calculated by the timesheet
	date # manually added or fallback to "TODAY"
	timesheet # CSV
	custom_signature
  draft # Bool
  paid # Bool
  archived # Bool
  currency # keywords (USD, CAD, BRL, etc)
  calculate_taxes
  timesheet # CSV to be mapped
    "user": "claudioccm",
    "email": "claudioccm@gmail.com",
    "client": "bernstein",
    "project": "player annotation",
    "task": "",
    "description": "reviewing",
    "billable": "yes",
    "start_date": "2016-08-01",
    "start_time": "17:40:00",
    "end_date": "2016-08-01",
    "end_time": "18:38:00",
    "duration": "00:58:00",
    "tags": "",
    "amount": 999


