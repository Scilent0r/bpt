Small project to pull Prisma beer prices daily to a database with Github Actions.
The database is read and displayed by Streamlit.

Link: 
https://appapppy-cvsnbwwiasdy45mumq3gpw.streamlit.app/


Known caveats; 

Product names may change, giving false results. This is because the DB only utilizes name and price, not sokUID, name and price. In future might fix this so that sokUID is used as static variable instead of product name that apparently can change. 
