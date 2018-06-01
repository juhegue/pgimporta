# -*- coding: utf-8 -*-

import wx


class Popup(wx.PopupTransientWindow):
    def __init__(self, parent, style, txt):
        wx.PopupTransientWindow.__init__(self, parent, style)
        panel = wx.Panel(self)
        panel.SetBackgroundColour("#FAFAD2")

        st = wx.StaticText(panel, wx.ID_ANY, txt)
        font = st.GetFont()
        font.SetStyle(wx.ITALIC)
        st.SetFont(font)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(st, 0, wx.ALL, 5)
        panel.SetSizer(sizer)

        sizer.Fit(panel)
        sizer.Fit(self)
        self.Layout()


def show_popup(parent, event, txt):
    win = Popup(parent, wx.SIMPLE_BORDER, txt)
    btn = event.GetEventObject()
    pos = btn.ClientToScreen((0,0))
    sz = btn.GetSize()
    win.Position(pos, (0, sz[1]))
    win.Popup()

