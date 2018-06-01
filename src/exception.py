# -*- coding: utf-8 -*-

import os
import sys
import platform
import traceback
import wx
import webbrowser
from urllib import quote
from util import hoy, is_windows
from constantes import *

if is_windows:
    import winsound

def EnvironmentInfo(version):
    info = list()
    info.append("#---- Notas ----#")
    info.append("Porfavor informe de cualquier dato adicional del error:")
    info.extend(["", "", ""])
    info.append("#---- System Information ----#")
    info.append("%s Version: %s" % (APLICACION, version) )
    info.append("Operating System: %s" % wx.GetOsDescription())
    if sys.platform == 'darwin':
        info.append("Mac OSX: %s" % platform.mac_ver()[0])
    info.append("Python Version: %s" % sys.version)
    info.append("wxPython Version: %s" % wx.version())
    info.append("wxPython Info: (%s)" % ", ".join(wx.PlatformInfo))
    info.append("Python Encoding: Default=%s  File=%s" % (sys.getdefaultencoding(), sys.getfilesystemencoding()))
    info.append("wxPython Encoding: %s" % wx.GetDefaultPyEncoding())
    info.append("System Architecture: %s %s" % (platform.architecture()[0], platform.machine()))
    info.append("Byte order: %s" % sys.byteorder)
    info.append("Frozen: %s" % str(getattr(sys, 'frozen', 'False')))
    info.append("#---- End System Information ----#")
    return os.linesep.join(info)


class ErrorReporter(object):
    instance = None
    _first = True
    def __init__(self):
        """Initialize the reporter

        **Note:**

        * The ErrorReporter is a singleton.

        """
        # Ensure init only happens once
        if self._first:
            object.__init__(self)
            self._first = False
            self._sessionerr = list()
        else:
            pass

    def __new__(cls, *args, **kargs):
        """Maintain only a single instance of this object

        **Returns:**

        * instance of this class

        """
        if not cls.instance:
            cls.instance = object.__new__(cls, *args, **kargs)
        return cls.instance

    def AddMessage(self, msg):
        """Adds a message to the reporters list of session errors

        **Parameters:**

        * msg: The Error Message to save

        """
        if msg not in self._sessionerr:
            self._sessionerr.append(msg)

    def GetErrorStack(self):
        """Returns all the errors caught during this session

        **Returns:**

        * formatted log message of errors

        """
        return "\n\n".join(self._sessionerr)

    def GetLastError(self):
        """Gets the last error from the current session

        **Returns:**

        * Error Message String

        """
        if len(self._sessionerr):
            return self._sessionerr[-1]



class ErrorDialog(wx.Dialog):
    ABORT = False
    REPORTER_ACTIVE = False
    def __init__(self, message):
        wx.Dialog.__init__(self, None, wx.ID_ANY, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        ErrorDialog.REPORTER_ACTIVE = True

        version = wx.GetApp().get_version

        ErrorReporter().AddMessage(message)

        self.SetTitle("Informe Error/Crash")

        self.err_msg = "%s\n\n%s\n%s\n%s" % (EnvironmentInfo(version), \
                                             "#---- Traceback Information ----#", \
                                             ErrorReporter().GetErrorStack(), \
                                             "#---- End Traceback Information ----#")

        self.textCtrl = wx.TextCtrl(self, value=self.err_msg, style=wx.TE_MULTILINE)  #|wx.TE_READONLY)

        self.ID_SEND = wx.NewId()
        self.abortButton = wx.Button(self, wx.ID_OK, label='Aceptar')
        self.sendButton = wx.Button(self, self.ID_SEND, label="Enviar Error")
        self.sendButton.SetDefault()
        self.closeButton = wx.Button(self, wx.ID_ABORT, label='Finalizar')

        self.DoLayout()

        self.Bind(wx.EVT_BUTTON, self.OnButton)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.CenterOnParent()
        self.ShowModal()

        if is_windows:
            winsound.MessageBeep(winsound.MB_ICONHAND)

    def DoLayout(self):
        mainmsg = wx.StaticText(self, label="Lo siento, a ocurrido un error inesperado.\
                                \nEnvie el siguiente formulario al desarrollador:")

        t_lbl = wx.StaticText(self, label="Error Traceback:")

        t_lbl.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)

        err_bmp = wx.ArtProvider.GetBitmap( wx.ART_ERROR, wx.ART_MESSAGE_BOX)
        err_bmp_ctrl = wx.StaticBitmap(self, -1)
        err_bmp_ctrl.SetBitmap(err_bmp)

        topSizer.Add(err_bmp_ctrl, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 20)
        topSizer.Add(mainmsg, 0, wx.EXPAND|wx.RIGHT, 20)
        mainSizer.Add(topSizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 20)
        mainSizer.Add(t_lbl, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
        mainSizer.Add((0, 2))
        mainSizer.Add(self.textCtrl, 1, wx.EXPAND|wx.LEFT|wx.BOTTOM|wx.RIGHT, 5)
        bottomSizer.Add(self.abortButton, 0, wx.ALL, 5)
        bottomSizer.Add((0, 0), 1, wx.EXPAND)
        bottomSizer.Add(self.sendButton, 0, wx.TOP|wx.BOTTOM, 5)
        bottomSizer.Add((0, 10))
        bottomSizer.Add(self.closeButton, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 5)
        mainSizer.Add(bottomSizer, 0, wx.EXPAND)

        self.SetSize((640, 480))

        self.SetSizer(mainSizer)
        mainSizer.Layout()

    def mailto(self, recipients, subject, body):
        webbrowser.open("mailto:%s?subject=%s&body=%s" % (recipients, quote(subject), quote(body)))
    
    def OnButton(self, evt):
        e_id = evt.GetId()
        if e_id == wx.ID_CLOSE:
            self.Close()
        elif e_id == self.ID_SEND:
            self.mailto(AUTOR_EMAIL, "Informe de Error", self.err_msg)
            self.Close()
        elif e_id == wx.ID_ABORT:
            ErrorDialog.ABORT = True
            wx.FutureCall(500, wx.GetApp().OnExit)
            self.Close()
        else:
            evt.Skip()

    def OnClose(self, evt):
        ErrorDialog.REPORTER_ACTIVE = False
        self.Destroy()
        evt.Skip()


def ExceptionHook(exctype, value, trace):
    exc = traceback.format_exception(exctype, value, trace)
    exc.insert(0, "*** %s ***%s" % (hoy(), os.linesep))
    txt_trace = "".join(exc)

    if not is_windows:
        print txt_trace
        
    if not ErrorDialog.REPORTER_ACTIVE:
        ErrorDialog(unicode(txt_trace, errors='replace'))


