# Simple Password Keeper



This is a project for storing password on PCs. It was orginaly created by me for me but I thought it was a a good idea to make it public.

⚠️  It may be not secure. If you use this code make sure no breach were found on the Fernet part of the cryptography package.


🏗️ Work in progress

Everything is written in Python so feel free to read and change the code to your liking

## How to run

These instructions are temporary. They will change in a near future.

These instructions are just cloning the repo, creating a venv and running.
1. Go wherever you want on your PC
2. Run `git clone <the github url of this repo>`
3. Run `cd <the name of the repo>/src`
4. Run `python -m venv .venv`
5. Run `source .venv/bin/activate`
6. Run `pip install -r requirements.txt`
7. Finally, all there is to do is to run the `main.py` file

## Theming and configuration

It is possible to change the default theme and the config through files. 
In the future you should be able to specify the config and theme using arguments, but for now, the config file must be labeled `spk_settings.json` and the theme file `spk.conf` (you can easily change this in the main.py file)


### The spk.conf file

There are two ways to write arguments : 

1. name_of_the_argument {

    CSS_arg = value;

    CSS_arg = value;

    ...

    CSS_arg = value;

}

2. name_of_the_argument = CSS_arg = value; CSS_arg = value; ... ; CSS_arg = value;

You can use all of the CSS that is supported by Qt (PySide6)

If you want to see an example and the list of all of the valid arguments names, go to the src/spk.conf file

### The spk_settings.json

Go to the spk_settings.json to see the valid arguments.




## List of features

- [x] Encryption
- [x] Notes-like interface
- [x] Config and theme files 
- [x] The app times out 
- [x] A search field
- []

