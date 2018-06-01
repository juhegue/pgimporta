# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
import platform
import pickle
import struct
import wx
import tempfile

bits = struct.calcsize("P") * 8
is_windows = any(platform.win32_ver())

#x = wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16))
#x.SaveFile("/tmp/p.png", wx.BITMAP_TYPE_PNG)


def escala_bitmap(bitmap, width, height):
    image = wx.ImageFromBitmap(bitmap)
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    return wx.BitmapFromImage(image)


def get_width_font(window, str):
    f = window.GetFont()
    dc = wx.WindowDC(window)
    dc.SetFont(f)
    width, height = dc.GetTextExtent(str)
    return width


def tree_expand_item(tree, item):
    tree.CollapseAll()
    while item.IsOk():
        tree.Expand(item)
        item = tree.GetItemParent(item)


def tree_get_item_text(tree, text, text_padre=None):
    def recorre(tree, text, root):
        item, cookie = tree.GetFirstChild(root)
        while item.IsOk():
            if tree.GetItemText(item) == text:
                return item
            if tree.ItemHasChildren(item):
                item1 = recorre(tree, text, item)
                if item1:
                    return item1

            item, cookie = tree.GetNextChild(root, cookie)
        return None

    root = tree.GetRootItem()
    if root and text_padre:
        padre = recorre(tree, text_padre, root)
        if padre:
            root = padre

    if root:
        return recorre(tree, text, root)
    else:
        return None


def tree_get_item_data(tree, data):
    def recorre(tree, data, root):
        item, cookie = tree.GetFirstChild(root)
        while item.IsOk():
            if tree.GetPyData(item) == data:
                return item
            if tree.ItemHasChildren(item):
                item1 = recorre(tree, data, item)
                if item1:
                    return item1

            item, cookie = tree.GetNextChild(root, cookie)
        return None

    root = tree.GetRootItem()
    if root:
        return recorre(tree, data, root)
    else:
        return None


def tree_collapse(tree, branch):
    item, cookie = tree.GetFirstChild(branch)
    while item.IsOk():
        tree.Collapse(item)
        if tree.ItemHasChildren(item):
            tree_collapse(tree, item)
        item, cookie = tree.GetNextChild(branch, cookie)


def hoy():
    t = time.localtime(time.time())
    st = time.strftime("%d %B %Y @ %H:%M:%S", t)
    return st


def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))


def rgb_to_hex(rgb):
    rgb = eval(rgb)
    r = rgb[0]
    g = rgb[1]
    b = rgb[2]
    return '#%02X%02X%02X' % (r, g, b)


def hex_to_color(value):
    r, g, b = hex_to_rgb(value)
    return wx.Colour(r, g, b,)


def get_frame_title(self):
    frame = wx.GetTopLevelParent(self)
    titulo = frame.GetTitle().split(" ")
    return titulo[0]


def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def read_object(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


def we_are_frozen():
    # All of the modules are built-in to the interpreter, e.g., by py2exe
    return hasattr(sys, "frozen")


def module_path():
    encoding = sys.getfilesystemencoding()
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, encoding))
    return os.path.dirname(unicode(__file__, encoding))


def get_tmpfilename():
    h = datetime.datetime.now()
    fic = "%02d%02d%02d%02d%02d%02d" % (h.year - 2000, h.month, h.day, h.hour, h.minute, h.second)
    return os.path.join(tempfile.gettempdir(), fic)
    # return os.path.join(tempfile.gettempdir(), next(tempfile._get_candidate_names()))


def ahora():
    h = datetime.datetime.now()
    fic = "%02d%02d%02d%02d%02d%02d" % (h.year - 2000, h.month, h.day, h.hour, h.minute, h.second)
    return int(fic)


def versiontuple(v):
    return tuple(map(int, (v.split("."))))
