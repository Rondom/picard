# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from PyQt4 import QtCore, QtGui

import os.path
import sys

from picard.file import File
from picard.util import decodeFileName, encodeFileName
from picard.ui.coverartbox import CoverArtBox
from picard.ui.metadatabox import MetadataBox
from picard.ui.itemviews import FileTreeView, AlbumTreeView

class MainWindow(QtGui.QMainWindow):
    
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi()
        
    def setupUi(self):
        self.setWindowTitle(_("MusicBrainz Picard"))
        icon = QtGui.QIcon()
        icon.addFile(":/images/Picard16.png")
        icon.addFile(":/images/Picard32.png")
        self.setWindowIcon(icon)

        self.createActions()
        self.createMenus()
        self.createStatusBar()
        self.createToolBar()

        centralWidget = QtGui.QWidget(self)
        self.setCentralWidget(centralWidget) 

        self.splitter = QtGui.QSplitter(centralWidget)

        self.fileTreeView = FileTreeView(self, self.splitter)
        self.connect(self.fileTreeView, QtCore.SIGNAL("itemSelectionChanged()"), self.updateFileTreeSelection)
        self.connect(self.fileTreeView, QtCore.SIGNAL("addFiles"), QtCore.SIGNAL("addFiles"))
        self.connect(self.fileTreeView, QtCore.SIGNAL("addDirectory"), QtCore.SIGNAL("addDirectory"))
        
        self.albumTreeView = AlbumTreeView(self, self.splitter)
        self.connect(self.albumTreeView, QtCore.SIGNAL("itemSelectionChanged()"), self.updateAlbumTreeSelection)
        self.connect(self.albumTreeView, QtCore.SIGNAL("addFiles"), QtCore.SIGNAL("addFiles"))
        self.connect(self.albumTreeView, QtCore.SIGNAL("addDirectory"), QtCore.SIGNAL("addDirectory"))
        
        self.splitter.addWidget(self.fileTreeView)
        self.splitter.addWidget(self.albumTreeView)

        self.localMetadataBox = MetadataBox(self, _("Local Metadata"))
        self.localMetadataBox.setDisabled(True)
        self.serverMetadataBox = MetadataBox(self, _("Server Metadata"))
        self.serverMetadataBox.setDisabled(True)
        
        self.coverArtBox = CoverArtBox(self)
        if not self.showCoverArtAct.isChecked():
            self.coverArtBox.hide()                    
        
        bottomLayout = QtGui.QHBoxLayout()
        bottomLayout.addWidget(self.localMetadataBox, 1)
        bottomLayout.addWidget(self.serverMetadataBox, 1)
        bottomLayout.addWidget(self.coverArtBox, 0)        
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.splitter, 1)
        mainLayout.addLayout(bottomLayout, 0)
        
        centralWidget.setLayout(mainLayout)
        
        self.restoreWindowState()
        
    def closeEvent(self, event):
        self.saveWindowState()
        event.accept()        
        
    def saveWindowState(self):
        self.config.persist.set("windowState", self.saveState())
        isMaximized = int(self.windowState()) & QtCore.Qt.WindowMaximized != 0
        if isMaximized:
            # FIXME: this doesn't include the window frame
            geom = self.normalGeometry()
            self.config.persist.set("windowPosition", geom.topLeft())
            self.config.persist.set("windowSize", geom.size())
        else:
            self.config.persist.set("windowPosition", self.pos())
            self.config.persist.set("windowSize", self.size())
        self.config.persist.set("windowMaximized", isMaximized)
        self.config.persist.set("viewCoverArt", self.showCoverArtAct.isChecked())
        self.fileTreeView.saveState()
        self.albumTreeView.saveState()

    def restoreWindowState(self):
        self.restoreState(self.config.persist.get("windowState").toByteArray())
        pos = self.config.persist.get("windowPosition").toPoint()
        self.move(pos)
        size = self.config.persist.get("windowSize").toSize()
        self.resize(size)
        if self.config.persist.getBool("windowMaximized"):
            self.setWindowState(QtCore.Qt.WindowMaximized)
        
    def createStatusBar(self):
        # TR: The initial status bar message
        self.statusBar().showMessage(_("Ready"))         
        
    def createActions(self):
        self.optionsAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarOptions.png"), "&Options...", self)
        #self.openSettingsAct.setShortcut("Ctrl+O")
        self.connect(self.optionsAct, QtCore.SIGNAL("triggered()"), self.showOptions)
        
        self.helpAct = QtGui.QAction(_("&Help..."), self)
        # TR: Keyboard shortcut for "Help"
        self.helpAct.setShortcut(QtGui.QKeySequence(_("Ctrl+H")))
        #self.connect(self.helpAct, QtCore.SIGNAL("triggered()"), self.showHelp)
        
        self.aboutAct = QtGui.QAction(_("&About..."), self)
        #self.connect(self.aboutAct, QtCore.SIGNAL("triggered()"), self.showAbout)
        
        self.addFilesAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarAddFiles.png"), _("&Add Files..."), self)
        self.addFilesAct.setStatusTip(_("Add files to the tagger"))
        # TR: Keyboard shortcut for "Add Files..."
        self.addFilesAct.setShortcut(QtGui.QKeySequence(_("Ctrl+O")))
        self.connect(self.addFilesAct, QtCore.SIGNAL("triggered()"), self.addFiles)
        
        self.addDirectoryAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarAddDir.png"), _("A&dd Directory..."), self)
        self.addDirectoryAct.setStatusTip(_("Add a directory to the tagger"))
        # TR: Keyboard shortcut for "Add Directory..."
        self.addDirectoryAct.setShortcut(QtGui.QKeySequence(_("Ctrl+D")))
        self.connect(self.addDirectoryAct, QtCore.SIGNAL("triggered()"), self.addDirectory)
        
        self.saveAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarSave.png"), _("&Save Selected Files"), self)
        # TR: Keyboard shortcut for "Save files"
        self.saveAct.setShortcut(QtGui.QKeySequence(_("Ctrl+S")))
        self.saveAct.setEnabled(False)
        self.connect(self.saveAct, QtCore.SIGNAL("triggered()"), self.save)
        
        self.submitAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarSubmit.png"), _("S&ubmit PUIDs to MusicBrainz"), self)
        self.submitAct.setEnabled(False)
        self.connect(self.submitAct, QtCore.SIGNAL("triggered()"), self.submit)
        
        self.exitAct = QtGui.QAction(_("E&xit"), self)
        self.exitAct.setShortcut(QtGui.QKeySequence(_("Ctrl+Q")))
        self.connect(self.exitAct, QtCore.SIGNAL("triggered()"), self.close)

        self.removeAct = QtGui.QAction(QtGui.QIcon(":/images/remove.png"), _("&Remove"), self)
        self.removeAct.setShortcut(QtGui.QKeySequence(_("Del")))
        self.removeAct.setEnabled(False)
        self.connect(self.removeAct, QtCore.SIGNAL("triggered()"), self.remove)

        self.showFileBrowserAct = QtGui.QAction(_("File &Browser"), self)
        self.showFileBrowserAct.setCheckable(True)
        #if self.config.persi.value("persist/viewFileBrowser").toBool():
        #    self.showFileBrowserAct.setChecked(True)
 #       self.connect(self.showFileBrowserAct, QtCore.SIGNAL("triggered()"), self.showFileBrowser)
        
        self.showCoverArtAct = QtGui.QAction(_("&Cover Art"), self)
        self.showCoverArtAct.setCheckable(True)
        if self.config.persist.getBool("viewCoverArt"):
            self.showCoverArtAct.setChecked(True)
        self.connect(self.showCoverArtAct, QtCore.SIGNAL("triggered()"), self.showCoverArt)

        self.searchAct = QtGui.QAction(QtGui.QIcon(":/images/search.png"), _("Search"), self)
        self.connect(self.searchAct, QtCore.SIGNAL("triggered()"), self.search)

        self.listenAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarListen.png"), _("Listen"), self)
        self.listenAct.setEnabled(False)
        self.connect(self.listenAct, QtCore.SIGNAL("triggered()"), self.listen)

        self.cdLookupAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarLookup.png"), _("&Lookup CD"), self)
        self.cdLookupAct.setEnabled(False)
        self.cdLookupAct.setShortcut(QtGui.QKeySequence(_("Ctrl+L")))
        
        self.analyzeAct = QtGui.QAction(QtGui.QIcon(":/images/analyze.png"), _("Anal&yze"), self)
        self.analyzeAct.setEnabled(False)
        self.analyzeAct.setShortcut(QtGui.QKeySequence(_("Ctrl+Y")))
        
        self.clusterAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarCluster.png"), _("Cluster"), self)
        self.clusterAct.setEnabled(False)
        self.clusterAct.setShortcut(QtGui.QKeySequence(_("Ctrl+U")))
        
    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu(_("&File"))
        self.fileMenu.addAction(self.addFilesAct)
        self.fileMenu.addAction(self.addDirectoryAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.submitAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        
        self.editMenu = self.menuBar().addMenu(_("&Edit"))
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.optionsAct)
        
        self.viewMenu = self.menuBar().addMenu(_("&View"))
        self.viewMenu.addAction(self.showFileBrowserAct)
        self.viewMenu.addAction(self.showCoverArtAct)
        
        self.menuBar().addSeparator()
        
        self.helpMenu = self.menuBar().addMenu(_("&Help"))
        self.helpMenu.addAction(self.helpAct)         
        self.helpMenu.addAction(self.aboutAct)

    def createToolBar(self):
        self.mainToolBar = self.addToolBar(self.tr("File"))
        self.mainToolBar.setObjectName("fileToolbar")
        self.mainToolBar.addAction(self.addFilesAct)
        self.mainToolBar.addAction(self.addDirectoryAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.saveAct)
        self.mainToolBar.addAction(self.submitAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.cdLookupAct)
        self.mainToolBar.addAction(self.analyzeAct)
        self.mainToolBar.addAction(self.clusterAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.removeAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.optionsAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.listenAct)

        self.searchToolBar = self.addToolBar(_("Search"))
        self.searchToolBar.setObjectName("searchToolbar")
        
        searchPanel = QtGui.QWidget(self.searchToolBar)
        hbox = QtGui.QHBoxLayout(searchPanel) 
        
        self.searchEdit = QtGui.QLineEdit(searchPanel)
        self.connect(self.searchEdit, QtCore.SIGNAL("returnPressed()"), self.search)
        hbox.addWidget(self.searchEdit, 0)
        
        self.searchCombo = QtGui.QComboBox(searchPanel)
        self.searchCombo.addItem(_("Album"), QtCore.QVariant("album"))
        self.searchCombo.addItem(_("Artist"), QtCore.QVariant("artist"))
        self.searchCombo.addItem(_("Track"), QtCore.QVariant("track"))
        hbox.addWidget(self.searchCombo, 0)
            
        #button = QtGui.QPushButton(_("&Search"), searchPanel)
        #self.connect(button, QtCore.SIGNAL("clicked()"), self.search)
        #hbox.addWidget(button, 0)
        
        self.searchToolBar.addWidget(searchPanel)
        self.searchToolBar.addAction(self.searchAct)        
        
    def setStatusBarMessage(self, message):
        """Set the status bar message."""
        self.statusBar().showMessage(message)         

    def search(self):
        """Search for album, artist or track on MusicBrainz."""
        text = unicode(self.searchEdit.text())
        type = unicode(self.searchCombo.itemData(self.searchCombo.currentIndex()).toString())
        self.log.debug("Search, '%s', %s", text, type)
        self.emit(QtCore.SIGNAL("search"), text, type)

    def addFiles(self):
        """Add files to the tagger."""
        currentDirectory = self.config.persist.getString("currentDirectory", "")
        formats = []
        extensions = []
        for format in self.tagger.getSupportedFormats():
            ext = u"*%s" % format[0]
            formats.append(u"%s (%s)" % (format[1], ext))
            extensions.append(ext)
        formats.insert(0, _(u"All Supported Formats") + u" (%s)" % u" ".join(extensions))
        files = QtGui.QFileDialog.getOpenFileNames(self, "", currentDirectory, u";;".join(formats))
        if files:
            files = [unicode(f) for f in files]
            self.config.persist.set("currentDirectory", os.path.dirname(files[0]))
            self.emit(QtCore.SIGNAL("addFiles"), files)
        
    def addDirectory(self):
        """Add directory to the tagger."""
        currentDirectory = self.config.persist.getString("currentDirectory", "")
        directory = QtGui.QFileDialog.getExistingDirectory(self, "", currentDirectory)
        if directory:
            directory = unicode(directory)
            self.config.persist.set("currentDirectory", directory)
            self.emit(QtCore.SIGNAL("addDirectory"), directory)

    def showOptions(self):
        dlg = OptionsDialog(self)
        dlg.exec_()
            
    def save(self):
        files = []
        for obj in self.selectedObjects:
            if isinstance(obj, File):
                files.append(obj)
                
        if files:
            self.tagger.saveFiles(files)
        
    def listen(self):
        pass
        
    def submit(self):
        pass
        
    def updateFileTreeSelection(self):
        objs = self.fileTreeView.selectedObjects()
        
        
    def updateAlbumTreeSelection(self):
        objs = self.fileTreeView.selectedObjects()
        
    def updateSelection(self, objects):
        self.selectedObjects = objects
        
        canRemove = False
        canSave = False
        for obj in objects:
            if isinstance(obj, File):
                canRemove = True
                canSave = True
        self.removeAct.setEnabled(canRemove)
        self.saveAct.setEnabled(canSave)
        
        localMetadata = None
        serverMetadata = None
        statusBar = u""
        if len(objects) == 1:
            obj = objects[0]
            if isinstance(obj, File):
                localMetadata = obj.localMetadata
                serverMetadata = obj.serverMetadata
                statusBar = obj.fileName
                
        if localMetadata:
            self.localMetadataBox.setArtist(localMetadata["ARTIST"])
            self.localMetadataBox.setAlbum(localMetadata["ALBUM"])
            self.localMetadataBox.setTitle(localMetadata["TITLE"])
            self.localMetadataBox.setDisabled(False)
        else:
            self.localMetadataBox.clear()
            self.localMetadataBox.setDisabled(True)
            
        if serverMetadata:
            self.serverMetadataBox.setArtist(serverMetadata["ARTIST"])
            self.serverMetadataBox.setAlbum(serverMetadata["ALBUM"])
            self.serverMetadataBox.setTitle(serverMetadata["TITLE"])
            self.serverMetadataBox.setDisabled(False)
        else:
            self.serverMetadataBox.clear()
            self.serverMetadataBox.setDisabled(True)
            
        self.setStatusBarMessage(statusBar)

    def remove(self):
        files = []
        for obj in self.selectedObjects:
            if isinstance(obj, File):
                files.append(obj)
                
        if files:
            self.tagger.fileManager.removeFiles(files)

    def showCoverArt(self):
        """Show/hide the cover art box."""
        if self.showCoverArtAct.isChecked():
            self.coverArtBox.show()
        else:
            self.coverArtBox.hide()