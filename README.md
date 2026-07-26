# Mew Version Control (MVC)
Have you ever had a problem, where you were using Scratch, and you don't have a version control?  
MVC has got you covered!

## Features
* Storing your projects to version control
* Roll back your changes

## Preview
You can see a working preview on https://mew.quack.zip!

## Running
You will need both [Deno](https://deno.com/) and [Python](https://www.python.org/downloads/) installed! Each project is located in their own seperate directories!
### Backend (PY)
Define the .env for its specific folder & run the following command(s):
```
python3 -m venv venv

source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

pip install -r requirements.txt
python3 main.py
```

### Frontend (TS)
Define the .env for its specific folder & run the following command(s):
```
deno run prod
```