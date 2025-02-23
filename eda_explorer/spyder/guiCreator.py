from qtpy.QtWidgets import (QHBoxLayout, QVBoxLayout, QTabWidget, QSizePolicy,
                          QPushButton, QListWidget, QLineEdit, QComboBox,
                          QLabel, QMainWindow, QGroupBox)
# from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QWidget

def deTab(text):
    # Split into lines and strip trailing whitespace
    lines = [line.rstrip() for line in text.splitlines()]
    
    # Remove blank lines from start and end
    start = 0
    end = len(lines)
    
    # Find first non-empty line
    while start < end and not lines[start].strip():
        start += 1
        
    # Find last non-empty line
    while end > start and not lines[end - 1].strip():
        end -= 1
        
    # Get the working set of lines
    lines = lines[start:end]
    
    if not lines:  # Handle empty text case
        return ""
        
    # Find minimum indentation of non-empty lines
    min_spaces = float('inf')
    for line in lines:
        if line.strip():  # Only check non-empty lines
            spaces = len(line) - len(line.lstrip())
            min_spaces = min(min_spaces, spaces)
    
    # Remove minimum spaces from each line
    processed_lines = []
    for line in lines:
        if line.strip():  # If line is not empty
            processed_lines.append(line[min_spaces:])
        else:  # Preserve empty lines in the middle
            processed_lines.append('')
            
    # Join lines and return
    return '\n'.join(processed_lines)    

def popTabbed(lines):
    ans=[]
    while len(lines)>0 and lines[0].startswith(' '):
        ans+=[lines.pop(0)]
        
    if len(ans)<1:
        return []
    # Find minimum indentation of non-empty lines
    min_spaces=min([len(line)-len(line.lstrip()) for line in ans])    
    return [line[min_spaces:] for line in ans]

def indent(lines):
    return ['    '+li for li in lines]


def createButton(obj, data):
    button=QPushButton(data)
    button_id=data.replace("&", "").replace(" ","")
    handler_name = f'b_{button_id}'
    if hasattr(obj, handler_name):
        button.clicked.connect(getattr(obj, handler_name))    
    obj.widgets[button_id]=button
    return button

def createListbox(obj, data):
    listBox=QListWidget()
    handler_name = f'l_{data}'
    if hasattr(obj, handler_name):
        listBox.itemSelectionChanged.connect(getattr(obj, handler_name))  
    obj.widgets[data]=listBox
    return listBox

def createEditText(obj, data):
    if ' ' in data:
        data, defaultText = data.split(' ',1)
        edit = QLineEdit(defaultText)
    else:
        edit = QLineEdit()
    # Connect to handler method if it exists on target_object
    handler_name = f'e_{data}'
    
    if hasattr(obj, handler_name):
        edit.textChanged.connect(getattr(obj, handler_name))
    obj.widgets[data]=edit
    return edit    

def createComboBox(obj, data):
    cbox=QComboBox()
    cbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    handler_name = f'c_{data}'
    if hasattr(obj, handler_name):
        cbox.currentIndexChanged.connect(getattr(obj, handler_name))
    obj.widgets[data]=cbox
    return cbox
    

def createWidget(obj, line):
    assert not line.startswith(' '), "Bad indent in GUI description"
    if line.startswith('"'):
        return QLabel(line.strip('"'))
    wtype, data = line.split('.',1)
    match(wtype):
        case 'b' : return createButton(obj, data)
        case 'l' : return createListbox(obj, data)
        case 'e' : return createEditText(obj, data)
        case 'c' : return createComboBox(obj, data)
        case _ : raise ValueError(f"Unknown widget type in line : '{line}'")

def createBoxLayout(obj, lines):
    line0=lines.pop(0)
    if line0[0]=='|':
        layout=QVBoxLayout()
    elif line0[0]=='-':
        layout=QHBoxLayout()
    else:
        raise ValueError("Layout description must start with | or -")

    title=line0[1:].strip()

    contents=popTabbed(lines)
    while len(contents)>0:
        line=contents.pop(0)
        if line[0] in '|-':
            newlayout=[line]
            newlayout+=indent(popTabbed(contents))                                
            layout2=createBoxLayout(obj, newlayout)
            if isinstance(layout2, QGroupBox):
                layout.addWidget(layout2)
            else:
                layout.addLayout(layout2)
        else:
            w=createWidget(obj, line)
            layout.addWidget(w)

    if title:
        group = QGroupBox(title)
        group.setLayout(layout)
        return group
    
    return layout

def createTabbedGui(obj, lines):
    # Create the tab widget
    tabs = QTabWidget()
    tabDirns={'N':QTabWidget.North,'W':QTabWidget.West,'S':QTabWidget.South,'E':QTabWidget.East}
    tabDirn=QTabWidget.North
    
    while len(lines)>0:
        tabTitle=lines.pop(0).strip('[]')
        if ':' in tabTitle:
            tabTitle,dirn=tabTitle.split(':')
            tabDirn=tabDirns[dirn]        
        layout=createBoxLayout(obj, popTabbed(lines))
        if isinstance(layout,QGroupBox):
            tab=layout
        else:
            tab=QWidget()
            tab.setLayout(layout)
        tabs.addTab(tab, tabTitle)

    tabs.setTabPosition(tabDirn) 
    return tabs

def create_gui(obj, description):
    if not hasattr(obj, "widgets"):
        obj.widgets={}
    lines=[li for li in deTab(description).splitlines() if len(li)>0]
    if lines[0].startswith('['):
        return createTabbedGui(obj,lines)
    layout=createBoxLayout(obj, lines)
    if isinstance(layout, QGroupBox):
        return layout
    W=QWidget(obj)        
    W.setLayout(layout)
    return W

# Example usage for Spyder/IPython environment:

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set minimum size for the window
        self.setMinimumSize(400, 300)
        
        description = '''
            |
                -
                    b.Browse
                    "cds.lib File"
                    e.cdslib
                    b.Refresh
                -
                    |Library
                        l.Library
                    |Cell
                        -
                            "Category:"
                            c.category
                        l.cell
                        -
                            b.New Cell
                    |View
                        l.view
                        -
                            b.Open
                            b.New
                            b.Run
        '''
        
        central_widget = create_gui(self, description)
        if central_widget:  # Make sure we have a valid widget
            self.setCentralWidget(central_widget)
            
        self.widgets['cdslib'].setText('foo')
                
    def b_Button1(self):
        print("Button1 clicked!")
        
    def b_Button2(self):
        print("Button2 clicked!")
        
    def l_Listbox1(self):
        print("Listbox1 selection changed!")
        
    def e_EditText1(self, text):
        print(f"EditText1 changed to: {text}")

def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    window = MyMainWindow()
    window.show()
    
    if not hasattr(__builtins__, '__IPYTHON__'):
        return app.exec()
    else:
        return window, app    

if __name__ == "__main__":
    main()

# To use in IPython/Spyder:
# gui, app = main()
# app.exec()  # If you want to block and run the event loop