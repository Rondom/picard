from picard.component import *
from picard.api import IFileOpener
from picard.file import File
from picard.util import encodeFileName
import logging

class MutagenMp3File(File):
    
    def read(self):
        import mutagen.mp3
        mfile = mutagen.mp3.MP3(encodeFileName(self.fileName))
        
        # Local metadata
        if mfile.has_key('TIT2'):
            self.localMetadata.title = unicode(mfile['TIT2']) 
        if mfile.has_key('TPE1'):
            self.localMetadata.artist = unicode(mfile['TPE1'])
        if mfile.has_key('TALB'):
            self.localMetadata.album = unicode(mfile['TALB'])
        
        self.serverMetadata.copy(self.localMetadata)
        
        # Audio properties
        self.audioProperties.length = int(mfile.info.length * 1000)
        self.audioProperties.bitrate = mfile.info.bitrate / 1000.0
        
    def save(self):
        import mutagen.mp3
        mp3File = mutagen.mp3.MP3(encodeFileName(self.fileName))
        mp3File.save()
        

class MutagenMp3Component(Component):
    
    implements(IFileOpener)

    # IFileOpener
    
    supportedFormats = {
        u".mp3": (MutagenMp3File, u"MPEG Layer-3"),
    }
    
    def getSupportedFormats(self):
        return [(key, value[1]) for key, value in self.supportedFormats.items()]

    def canOpenFile(self, fileName):
        for ext in self.supportedFormats.keys():
            if fileName.endswith(ext):
                return True
        return False
        
    def openFile(self, fileName):
        for ext in self.supportedFormats.keys():
            if fileName.endswith(ext):
                file = self.supportedFormats[ext][0](fileName)
                file.read()
                return (file,)
        return None
