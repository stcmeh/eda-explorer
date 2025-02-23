# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2025, Spyder Bot
#
# Licensed under the terms of the Not open source
# ----------------------------------------------------------------------------
"""
EDA Explorer Main Widget.
"""


# Third party imports
from qtpy.QtWidgets import QHBoxLayout,  QListWidgetItem
from qtpy.QtGui import QColor, QBrush
from qtpy.QtCore import Qt


# Spyder imports
from spyder.api.config.decorators import on_conf_change
from spyder.api.translations import get_translation

from spyder.api.widgets.main_widget import PluginMainWidget

from .guiCreator import create_gui
from .cadStuff import parse_cdslib, full, oalcv, isXschem, getXschemCells, getXschemCellViews
import os

# Localization
_ = get_translation("eda_explorer.spyder")


class EDAExplorerActions:
    ExampleAction = "example_action"


class EDAExplorerToolBarSections:
    ExampleSection = "example_section"


class EDAExplorerOptionsMenuSections:
    ExampleSection = "example_section"


class EDAExplorerWidget(PluginMainWidget):

    # PluginMainWidget class constants

    # Signals

    def __init__(self, name=None, plugin=None, parent=None):
        super().__init__(name, plugin, parent)



    # --- PluginMainWidget API
    # ------------------------------------------------------------------------
    def get_title(self):
        return _("EDA Explorer")

    def get_focus_widget(self):
        pass

    def setup(self):
        # Create an example action
       description = '''
           |
               -
                   b.Browse
                   "cds.lib File"
                   e.cdslib
                   b.Refresh
               -
                   |Library
                       l.libraries
                   |Cell
                       -
                           "Category:"
                           c.category
                       l.cells
                       -
                           b.New Cell
                   |View
                       l.views
                       -
                           b.Open
                           b.New
                           b.Run
       '''
      
       central_widget = create_gui(self, description)

       # Add example label to layout
       layout = QHBoxLayout()
       layout.addWidget(central_widget)
       self.setLayout(layout)
       
       self.lib=None
       self.cell=None
       self.view=None
       
       if 'PROJHOME' in os.environ:
           self.widgets['cdslib'].setText(full('$PROJHOME/cds.lib'))
           self.b_Refresh()        
       for w in self._parent.widgetlist:
           # item=QListWidgetItem(str(w.__class__))
           # self.widgets['cells'].addItem(item)
           if 'Editor' in str(w.__class__):
               self.editor=w
           if 'Console' in str(w.__class__):
               self.console=w
       self.widgets['views'].itemDoubleClicked.connect(self.b_Open)
          
            
    

    def update_actions(self):
        pass

    @on_conf_change
    def on_section_conf_change(self, section):
        pass

    # --- Public API
    # ------------------------------------------------------------------------
    def b_Refresh(self):
        self.saveState={}
        if self.lib is not None:
            self.saveState['lib']=self.lib
        if self.cell is not None:
            self.saveState['cell']=self.cell
        if self.view is not None:
            self.saveState['view']=self.view
        self.lib=None
                
        self.cdslibPath=self.widgets['cdslib'].text()
        self.cdslib=parse_cdslib(self.cdslibPath)
        
        for w in ['libraries', 'cells', 'views']:
            self.widgets[w].blockSignals(True)
            self.widgets[w].clear()
            self.widgets[w].blockSignals(False)
        
        self.lib,self.cell,self.view=(None,None,None)
        
        for lib in sorted(self.cdslib.keys()):
            libPath=self.cdslib[lib]
            pathok=os.path.isdir(libPath)
            item = QListWidgetItem(lib)
            if not pathok:
                item.setForeground(QBrush(QColor('red')))
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            elif isXschem(lib):
                item.setForeground(QBrush(QColor('cornflowerblue')))
            self.widgets['libraries'].addItem(item)
            
        if 'lib' in self.saveState:
            lib=self.saveState.pop('lib')
            if not lib:
                return
            items = self.widgets['libraries'].findItems(lib, Qt.MatchExactly)
            if items:
                self.widgets['libraries'].setCurrentItem(items[0])  # This will trigger itemSelectionChanged

    def l_libraries(self):
        self.cell=None
        self.widgets['cells'].clear()
        self.widgets['views'].clear()
        selected_item = self.widgets['libraries'].currentItem()
        if not selected_item:
            self.lib = None
            return
        
        self.lib = selected_item.text()
        self.libDir = self.cdslib[self.lib]
        if not os.path.isdir(self.libDir):
            return
        
        if isXschem(self.lib):
            cells=getXschemCells(self.lib)
        else:
            cells=sorted([d for d in os.listdir(self.libDir) if os.path.isdir(os.path.join(self.libDir, d)) and not d.startswith('.')])
        
        for cell in cells:
            item=QListWidgetItem(cell)
            self.widgets['cells'].addItem(item)
        
        if 'cell' in self.saveState:
            cell=self.saveState.pop('cell')
            if not cell:
                return
            items=self.widgets['cells'].findItems(cell, Qt.MatchExactly)
            if items:
                self.widgets['cells'].setCurrentItem(items[0])
        
    def l_cells(self):
        self.view=None
        self.widgets['views'].clear()
        selected_item = self.widgets['cells'].currentItem()
        if not selected_item:
            self.cell = None
            return
        self.cell = selected_item.text()
        self.cellDir = os.path.join(self.libDir, self.cell)
        
        
        if isXschem(self.lib):
            self.viewD=getXschemCellViews(self.lib, self.cell)
            views=sorted(self.viewD.keys())
        else:
            self.viewD={d:dpath for d in os.listdir(self.cellDir) if os.path.isdir(dpath:=os.path.join(self.cellDir, d)) and not d.startswith('.')}
            # views=sorted([d for d in os.listdir(self.cellDir) if os.path.isdir(os.path.join(self.cellDir, d)) and not d.startswith('.')])
        views=sorted(self.viewD.keys())
        for view in views:
            item=QListWidgetItem(view)
            self.widgets['views'].addItem(item)
            
        if 'view' in self.saveState:
            view=self.saveState.pop('view')
            if not view:
                return
            items=self.widgets['views'].findItems(view, Qt.MatchExactly)
            if items:
                self.widgets['views'].setCurrentItem(items[0])
        
    def l_views(self):
        selected_item = self.widgets['views'].currentItem()
        if not selected_item:
            self.view = None
            return        
        self.view = selected_item.text()
        self.viewDir = os.path.join(self.cellDir, self.view)        
        
    def b_Open(self):
        lcv=oalcv(f'{self.lib}/{self.cell}/{self.view}')
        if lcv.exists():
            self.editor.load([lcv.viewfile])
    
    def b_Run(self):
        lcv=oalcv(f'{self.lib}/{self.cell}/{self.view}')
        if lcv.exists():
            self.console.run_script(lcv.viewfile,os.getcwd())
    
