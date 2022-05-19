# aspire-api

Aspire Budgeting is an envelope-based-budgeting tool built on top of google spreadsheets. I like it a lot, so I made an API for it.

I think the use cases are obvious. Aspire *is* literally just a spreadsheet, so it's not wonder that its ability to interface with the outside world is a bit lacking - particularly having to introduce all transactions by hand. I don't think this is a bad thing, really, as it helps you be more conscientious about spending - as opposed to having your computerized lackey run all the budgeting in the background so you can ignore it when it tells you to stop spending so much on scented candles. Nonetheless, ever since I realized my bank lets me download csv transcripts of all my spending, doing it by hand just seemed like pointless effort, so I invested 10 hours into doing this repo by hand instead.

This is provided without warranty, etc (read the license if you like). I was pretty anal in making sure that the code can't ruin your spreadsheet unless you jump through several ill-advised hoops, but still, I'd recommend making a backup before trying anything.

### Setup
The top-level directory is *not* the package - that would be the AspireAPI folder within it. The other two files next to this folder are a few tests and an example main - a simple script that tops up all your envelopes and sends the rest of the money to a savings account (well, you have to send the money yourself). To run either of these two, you will need to do a few things.

#### Change the locale

In AspireAPI.Locale, go to the last line, "Locale = EuropeLocale", and change it to the Locale corresponding to the spreadsheet you're using. Presently there's locales for Europe (€, d/m/y), the US ($, m/d/y), and China (¥, y/m/d). I'd be surprised if someone who doesn't fit into those wants to use this, but if so, feel free to email me if you can't figure out how to add your own Locale.

#### Find your spreadsheet's id

This is one of the two things you'll need to initialize an Aspire object (notice how in main.py it is loaded from an external file). To find your id, open the spreadsheet on any browser, and look at the url. It should look something like this:

https://docs.google.com/spreadsheets/d/<spreadsheet-id\>/edit#gid=0

Maybe not exactly for that last part, but in any case it's pretty easy to distinguish the id-looking string of characters.
  
#### Get your hands on a google oauth2 token
  
I have found this to be a bit fiddly. In any case, follow this tutorial: https://developers.google.com/sheets/api/quickstart/python
  
Note that, as best as I can tell, your only option if you want to (a) get an oauth2 token and (b) not spend money on it, is to create an app in testing and register yourself as a tester. I think it's rather likely that I'm missing an obvious alternative, since it seems that having access to your own spreadsheets should be less convoluted.

Also, regarding the code in the example above - this might not be the case for you, but in my case creds.valid always returned false (even for tokens that verifiably worked), which caused the program to always assume that the stored token was invalid and force me through the google permission-granting process again. If this happens to you too, you can circumvent it by checking whether the token works by doing a dummy query (or just not checking at all and hoping that it fails early).
  
#### Another option

Since I wanted the interface with the actual spreadsheet to be as minimal as possible, there's an intermediate class (well, interface), "AspireSpreadsheetInterface", that abstracts the only three operations that actually get performed on the spreadsheets. The Aspire object needs a subclass of this that actually implements these methods - in the text above I assume we're using GoogleSpreadsheetAPI, which, unsurprisingly, uses google's spreadsheet API. Nonetheless, one may well be insane enough to implement a spreadsheet interface with Selenium (but this would probably violate some TOS).
  
### What does it do?
  
Once you have an AspireSpreadsheetAPI object, you have all you need to pass to Aspire's constructor. The constructor will take a couple seconds (queries can be a bit slow). Then - what can you do with an Aspire object?
  
Things an Aspire object *can* do:
- Read the dashboard
- Read/write/edit transactions
- Read/write/edit category transfers
- Read the configuration
  
Things it *can't* do:
- Write/edit the configuration
- Anything with any of the other sheets

#### The dashboard

is accessed through Aspire.dashboard. It lets you read the balance from your accounts (Aspire.dashboard.balance(account)), the amount that's available to budget and how much you've spent/budgeted this month (Aspire.dashboard.available_to_budget(), .spent_this_month() and .budgeted_this_month()), as well as the amount spend/budgeted/left in the envelope for each category/category group (Aspire.dashboard.activity(), .budgeted(), .available()).
  
Note that this is always fetched from the spreadsheet every time any of those functions are called - in general (except for the configuration), none of the data of the spreadsheet is ever looked at through a local copy.
  
#### Transactions
  
are handled through Aspire.transactions. The IO for this class uses exclusively a Transaction object (a namedtuple), which represents a single row of the table of transactions - it stores a date, inflow/outflow, category, account, memo and status. 
  
Transactions act like a pile - indeed, this API assumes that your transactions are all set one after the other, with no empty rows in between. If they *are* set up that way, then you have operations for getting, pushing (to the end of the pile), inserting, replacing, and popping transactions. These five also have batched variants, which are far faster (and also less likely to trigger the rate limiting of google's API). 
  
Be aware that the indexing is a bit atypical. Nonnegative indexes count from the start of the transactions (i.e. earliest first). When they grow past the last transaction (i.e. at the index Aspire.transactions.first_empty_index()), it is understood that the indices refer to an infinite list of empty transactions beyond the pile - for this reason, get will return None, but all other methods will fail. As for negative indexing - this counts from the last transaction (at -1) backwards, down to the first transaction. Any index beyond that will always raise an exception.
  
#### Category Transfers
  
this is the job of Aspire.category_transfers, which is essentially identical to Aspire.transactions, except that it does all its business with CategoryTransfer objects. These are also namedtuples representing rows of the category transfer table.
  
#### Configuration
  
Differs from the above in that it is read once then forgotten about, as it is assumed to not change during execution. If for whatever reason it does, one may call Aspire.reload_configuration() to reread the values.
  
Reading the configuration spreadsheet populates a few attributes directly in the Aspire object. Namely,
  
- Aspire.monthly_income
- Aspire.unallocated_income
- Aspire.half_year_fund
- Aspire.accounts
- Aspire.credit_cards
- Aspire.asset_categories
- Aspire.debt_categories
- Aspire.hidden_categories
- Aspire.hidden_accounts
  
These are all rather self-explanatory. they are stored as strings, lists of strings, or floats. Moreover, we have Aspire.categories, a list of category names, and Aspire.category_groups, a dictionary keyed by group names referring to the list of categories in that group. The rest of the data is stored in private, and should be accessed through the methods:

- Aspire.category_symbol(category)
- Aspire.category_amount(category)
- Aspire.category_goal(category):
- Aspire.is_category_necessary(category)
  
  
