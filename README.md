Small project to pull Prisma beer prices daily to a database with Github Actions.

The database is read and displayed by Streamlit.

Link: 
https://appapppy-cvsnbwwiasdy45mumq3gpw.streamlit.app/

Features;

- Updates database daily (430'ish beers)
- Database pulls daily data for historical purposes, but UI query limits visibility to 4 days. 
- Hides all beers that's price hasn't changed in 4 days (with 430ish beers would be tedious to scroll them all)
- Shows all beers that's price has changed in the past 4 days as yellow (price rises and lowerings)
- Shows all beers that have left the cataloque in the past 4 days as red (price likely 50% off in supermarket)
- Follows storeID "726109200"


Known caveats; 

- Product names may change, giving false results. This is because the DB only utilizes name and price, not sokUID, name and price. In future might fix this so that sokUID is used as static variable instead of product name that apparently can change. 

Todo; 

- Separate current database to a 4-day one and a historical price one. Even tho database size is not huge at the moment, it'll grow in the future. 
- Replace name with ProdUID, join name to produid.
