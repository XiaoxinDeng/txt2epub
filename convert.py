#!/usr/bin/env python

from langdetect import detect
from ebooklib import epub
import os, re, json
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

def get_vscode_settings()->str:
    """Get the book file directory recorded in VScode settings z-reader

    Returns:
        str: The book file directory recorded in VScode settings z-reader
    """    
    home_directory = Path.home()
    settings_directory = home_directory / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
    if os.path.exists(settings_directory):
        with(open(settings_directory, 'r', encoding='utf-8')) as f:
            settings = dict(json.load(f))
            if hasattr(settings, "z-reader.fileDir"):
                return settings["z-reader.fileDir"]

def get_documents_directory()->str:
    """Obtain the User document directory

    Returns:
        str: the User document directory
    """    
    home_directory = Path.home()
    documents_directory = home_directory / 'Documents'  # This is typical for Windows and Linux
    # documents_directory = home_directory / 'Documents' / 'Books'  # This is typical for Windows and Linux
    if documents_directory.exists():
        return documents_directory
    else:
        # On macOS, the path is usually /Users/[Username]/Documents
        return home_directory / 'Documents'
    
def select_file(default_dir:str=None, file_types:str=None, title:str=None):
    """Creates a window for the user to select arbitary files

    Args:
        default_dir (str, optional): The default opening directory. Defaults to None.
        file_types (str, optional): Filter the type of the file. Defaults to None.
        title (str, optional): Title of the window. Defaults to None.

    Returns:
        str: The user selected file directory 
    """    
    # Create a root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    if not default_dir:
        default_dir = get_documents_directory()

    # Open the file dialog
    file_path = filedialog.askopenfilename(
        initialdir=default_dir,
        filetypes=file_types,
        title=title
    )
    if file_path:
        print(f'Selected .txt file: {file_path}.')
    else:
        print('No txt file is selected')
    return file_path

def select_txt_file(default_directory:str):
    """Wrapper for user-customized file selection function, specifying the type of the file to ".txt"

    Args:
        default_directory (str): The default opening directory. Defaults to None.

    Returns:
        str: The user selected file directory 
    """    
    return select_file(default_directory, 
                        [("Text files", "*.txt"), ("All files", "*.*")],
                        'Select a .txt file for epub file conversion')

def txt_to_epub(txt_file_path:str, 
                epub_file_path:str=None, 
                author:str=None, 
                title:str=None, 
                id:str=None, 
                lang:str=None):
    """Convert a .txt file into .epub file

    Args:
        txt_file_path (str): The directory of the text file
        epub_file_path (str, optional): The directory of the epub file. Defaults to None, save to the same directory and the same file name as the original file, with different extension.
        author (str, optional): The name of the author of the book. Defaults to None.
        title (str, optional): The title of the book. Defaults to the txt file name without the extension.
        id (str, optional): Defaults to None.
        lang (str, optional): The language of the book. Defaults to None: detect it automatically. Choices: ['en', 'zh-cn']
    """    
    if not txt_file_path:
        return
        
    # Create a new EPUB book
    book = epub.EpubBook()

    # Read text file content
    with open(txt_file_path, 'r') as file:
        book_content = file.read()

    # Set default values
    if not epub_file_path:
        epub_file_path = os.path.splitext(txt_file_path)[0] + '.epub'
    if not title:
        title = os.path.splitext(os.path.split(txt_file_path)[-1])[0]
    if not lang:
        try:
            lang = detect(book_content)
        except Exception as e:
            lang = 'zh-cn'
            print(f"Error in language detection: {e}, use {lang} instead.")
    
    # Set metadata (title, author, etc.)
    book.set_title(title)
    book.set_language(lang)
    
    # Optional metadata
    if id:
        book.set_identifier(id)
    if author:
        book.add_author(author)
        
    # Language specific settings
    if lang == 'zh-cn':
        # 中文章节
        regex = r"^\s*([第卷][0123456789一二三四五六七八九十零〇百千两]*[章回部节集卷].*)\s*"
        spine_uid = '目录'
    elif lang == 'en':
        # English chapters
        regex = r"^\s*([Chapter].*)\s*" 
        spine_uid = 'Table of Content'
    else:
        print(f'Language "{lang}" not supported')   
        return

    # Split chapter 'C' and chapter content 'c' into list: ['', C1, c1, C2, c2, ..., Cn, cn]
    splits = re.split(regex, book_content, flags=re.M)
    book.spine = [spine_uid]
    
    # Add chapters into epub
    for i in range(1, len(splits) - 1, 2):
        # Add chapter to the book
        chapter_title = splits[i]
        chapter = epub.EpubHtml(title=chapter_title, file_name=f'chap_{i}.xhtml', lang=lang)
        chapter.content = '<html><body><p>{}</p></body></html>'.format(splits[i+1].replace('\n', '<br/>'))
        book.add_item(chapter)
        book.toc.append(epub.Link(f'chap_{i}.xhtml', chapter_title, f'chap{i}'))
        book.spine.append(chapter)

    # Define Table Of Contents and book spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav(uid=spine_uid))

    # Write the EPUB file
    epub.write_epub(epub_file_path, book, {})
    print(f'Save .epub file to: {epub_file_path}')

# Convert
txt_to_epub(select_txt_file(get_vscode_settings()))