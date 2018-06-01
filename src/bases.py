# -*- coding: utf-8 -*-

import wx
import wx.lib.mixins.listctrl  as  listmix
import wx.lib.sized_controls as sc
from bisect import bisect
import util
import imagenes.imagenes as imagenes


class BaseFrame(wx.Frame):
    def __init__(self, *args, **kargs):
        wx.Frame.__init__(self, *args, **kargs)

    def set_propi_size(self):
        if not self.IsMaximized():
            propi = self.GetTitle()
            # Porque la ventana principal tiene el nombre del pgi y este cambia
            if propi.find(".pgi") > 0 or propi.find("(...)") > 0:
                propi = propi.split("(")[0].strip()

            valor = self.GetSizeTuple()
            if util.is_windows:
                wx.GetApp().set_propiedad(propi, valor)
            else:
                # TODO:: error en ubuntu 15.04 wx 3.0.0.1
                d1 = valor[0]
                d2 = valor[1] - 28
                wx.GetApp().set_propiedad(propi, (d1, d2))

    def set_size(self, defecto=(800, 600)):
        propi = self.GetTitle()
        if propi.find(".pgi") > 0:
            propi = propi.split("(")[0].strip()

        valor = wx.GetApp().get_propiedad(propi)
        if valor:
            self.SetSize(valor)
        else:
            self.SetSize(defecto)


class BaseSplitter(wx.SplitterWindow):
    def __init__(self, parent, nombre, size_defecto=200):
        wx.SplitterWindow.__init__(self, parent, wx.ID_ANY, style=wx.SP_LIVE_UPDATE)
        self.nombre = nombre
        self.size_defecto = size_defecto

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_sash_changed)

    def on_sash_changed(self, event):
        valor = int(event.GetSashPosition())
        propi = util.get_frame_title(self)
        propi += self.nombre
        wx.GetApp().set_propiedad(propi, valor)

    def get_size(self):
        propi = util.get_frame_title(self)
        propi += self.nombre
        valor = wx.GetApp().get_propiedad(propi)

        return valor if valor else self.size_defecto


class BaseSizedDialog(sc.SizedDialog):
    def __init__(self, *args, **kargs):
        sc.SizedDialog.__init__(self, *args, **kargs)

        self.pane = self.GetContentsPane()
        self.pane.SetSizerType("form")

    def botones(self):
        #self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        btnsizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK, label='Aceptar')
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL, label='Cancelar')
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        self.SetButtonSizer(btnsizer)

    def get_pane(self):
        return self.pane

    def fit(self):
        super(BaseSizedDialog, self).Fit()
        self.SetMinSize(self.GetSize())

    def set_focus_ctrl(self, ctrl):
        ctrl.SetFocus()
        if hasattr(ctrl, "SetSelection"):
            ctrl.SetSelection(-1, -1)

    def set_propi_size(self):
        propi = self.GetTitle()
        valor = self.GetSizeTuple()
        if util.is_windows:
            wx.GetApp().set_propiedad(propi, valor)
        else:
            # TODO:: error en ubuntu 15.04 wx 3.0.0.1
            d1 = valor[0]
            d2 = valor[1] - 28
            wx.GetApp().set_propiedad(propi, (d1, d2))

    def set_size(self, size=None):
        propi = self.GetTitle()
        valor = wx.GetApp().get_propiedad(propi)
        if valor:
            self.SetSize(valor)
        elif size:
            self.SetSize(size)


class BaseListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):
    def __init__(self, *args, **kargs):
        wx.ListCtrl.__init__(self, *args, **kargs)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 0)

        self.itemDataMap = None
        self.itemIndexMap = None

        self._attr1 = wx.ListItemAttr()
        self._attr2 = wx.ListItemAttr()
        self.set_background_colour("#FFFFFF", "#E0F8E6")

        self.il = wx.ImageList(16, 16)
        self.idxflecha = self.il.Add(imagenes.flecha.GetBitmap())
        self.idxcuadro = self.il.Add(imagenes.cuadro.GetBitmap())
        self.idxarriba = self.il.Add(imagenes.flechaarriba.GetBitmap())
        self.idxabajo = self.il.Add(imagenes.flechaabajo.GetBitmap())
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        # Posicion row/col actual
        self.row = 0
        self.col = 0

        self.Bind(wx.EVT_LIST_COL_END_DRAG, self._on_col_end_drag)
        self.Bind(wx.EVT_LEFT_DOWN, self.__on_down)
        self.Bind(wx.EVT_RIGHT_DOWN, self.__on_down)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.__on_col_click)

    def _on_col_end_drag(self, evt):
        self.Refresh()
        evt.Skip(True)

    def __on_col_click(self, evt=None):
        """ Para que no ejecute ColumnSorterMixin.__OnColClick si no es virtual
            ya que en este caso no se ha inicializado con (SetColumnCount) ColumnSorterMixin._colSortFlag[]
        """
        if self.IsVirtual():
            evt.Skip(True)
        else:
            evt.Skip(False)

    def __on_down(self, evt=None):
        x, y = evt.GetPosition()
        row, flags = self.HitTest((x, y))

        col_locs = [0]
        loc = 0
        for n in range(self.GetColumnCount()):
            loc = loc + self.GetColumnWidth(n)
            col_locs.append(loc)

        if util.is_windows:
            col = bisect(col_locs, x+self.GetScrollPos(wx.HORIZONTAL)) - 1
        else:
            PixelsPerUnit = wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y)
            col = bisect(col_locs, x + self.GetScrollPos(wx.HORIZONTAL) * PixelsPerUnit) - 1

        self.row = row
        self.col = col
        evt.Skip(True)

    def set_background_colour(self, color1, color2):
        """ Asigna los colores par/impar para las filas

        :param color1: string, formato color hexadecimal  (Ej: #FFFFFF)
        :param color2: string, formato color hexadecimal  (Ej: #FFFFFF)
        """
        self._attr1.SetBackgroundColour(util.hex_to_color(color1))
        self._attr2.SetBackgroundColour(util.hex_to_color(color2))
        
    def set_color_row(self, index):
        """ Asigna el color a la fila (cuando no es wx.LC_VIRTUAL)

        :param index: integer, número de fila
        """
        item = self.GetItem(index)
        if index % 2 == 0:
            item.SetBackgroundColour(self._attr1.GetBackgroundColour())
        else:
            item.SetBackgroundColour(self._attr2.GetBackgroundColour())
        self.SetItem(item)

    def set_propi_columns(self, nom_propi_list):
        """ Guarda el ancho de las columnas

        :param nom_propi_list: string, nombre (a este se le suma el titulo del frame que lo contiene)
        """
        propi = util.get_frame_title(self)
        propi += nom_propi_list
        valor = dict()
        for i in range(0, self.GetColumnCount()):
            nom = self.GetColumn(i).GetText()
            val = self.GetColumnWidth(i)
            valor[nom] = val
        wx.GetApp().set_propiedad(propi, valor)

    def set_size_columns(self, nom_propi_list):
        """ Restaura el ancho de las columnas

        :param nom_propi_list: string, nombre asignado anteriormente
        """
        propi = util.get_frame_title(self)
        propi += nom_propi_list
        valor = wx.GetApp().get_propiedad(propi)
        if valor:
            # menos la última columna, ya que tiene autosize con ListCtrlAutoWidthMixin
            for i in range(0, self.GetColumnCount()-1):
                nom = self.GetColumn(i).GetText()
                if nom in valor:
                    self.SetColumnWidth(i, valor[nom])

    def get_selected_items(self):
        """ Retorna las filas seleccionadas
        
        :return: list, lista de integer 
        """
        selection = []
        index = self.GetFirstSelected()
        selection.append(index)
        while len(selection) <= self.GetSelectedItemCount():
            index = self.GetNextSelected(index)
            selection.append(index)
        return selection

    def clear(self):
        """ Borra todo el ListCtrl
        """
        self.DeleteAllItems()
        self.DeleteAllColumns()
        self.itemDataMap = None
        self.itemIndexMap = None

    def set_columnas(self, columnas):
        """ Asigna los nombres de las columns 

        :param columnas: list de string
        """
        for i, campo in enumerate(columnas):
            w = util.get_width_font(self, campo) + 15
            self.InsertColumn(i, campo, width=w)
        self.SetColumnCount(len(columnas))
        self._doResize()

    # para wx.LC_VIRTUAL
    def set_data(self, data):
        """ Asigna los datos del ListCtrl

        :param data: 
        """
        self.SetItemCount(len(data))
        #para listmix.ColumnSorterMixin
        self.itemDataMap = data
        self.itemIndexMap = data.keys()

    def get_data_row(self, row):
        """ Retorna la lista de valores de la fila 
        """
        index = self.itemIndexMap[row]
        data = self.itemDataMap[index]
        return data[:]

    # funciones para wx.LC_VIRTUAL
    def SortItems(self, sorter=cmp):
        # solo si es virtual ya que sino itemDataMap no esta inicializado
        if self.IsVirtual():
            items = list(self.itemDataMap.keys())
            items.sort(sorter)
            self.itemIndexMap = items

            self.Refresh()

    def GetListCtrl(self):
        return self

    def SetVirtualData(self, item, col, text):
        index = self.itemIndexMap[item]
        self.itemDataMap[index][col] = text

    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        text = self.itemDataMap[index][col]
        return text

    def OnGetItemAttr(self, item):
        if item % 2 == 0:
            return self._attr2
        return self._attr1

    def OnGetItemImage(self, item):
        if item in self.get_selected_items():
            return self.idxflecha
        return self.idxcuadro

    def GetSortImages(self):
        return (self.idxabajo, self.idxarriba)


class BaseEditListCtrl(BaseListCtrl, listmix.TextEditMixin):
    def __init__(self, *args, **kargs):
        BaseListCtrl.__init__(self, *args, **kargs)
        listmix.TextEditMixin.__init__(self)

        self.__restaura_list_row = True
        self.__nueva_row = None
        self.__copia_val_row = None
        self.__callback_enter = None

        self.editor.Bind(wx.EVT_CHAR, self.__on_char_editor)
        self.editor.Bind(wx.EVT_KILL_FOCUS, self.__kill_focus_editor)
        self.editor.Bind(wx.EVT_SET_FOCUS, self.__set_focus_editor)
        self.editor.Bind(wx.EVT_TEXT_ENTER, self.__text_enter_list)

        self.Bind(wx.EVT_LIST_COL_CLICK, self.__on_col_click)
        # self.Bind(wx.EVT_CHAR, self.__on_char_list)

    def set_callback_enter(self, funcion):
        self.__callback_enter = funcion

    def __on_col_click(self, event):
        evt = wx.KeyEvent(wx.wxEVT_CHAR)
        evt.m_keyCode = wx.WXK_ESCAPE
        self.editor.GetEventHandler().ProcessEvent(evt)
        event.Skip(True)

    # def __on_char_list(self, event):
    #     keycode = event.GetKeyCode()
    #     if keycode == wx.WXK_F2:
    #         # pos_y = ??   No se como calcular la posicion Y, GetPosition() solo esta en los eventos del raton
    #         # evt = wx.MouseEvent(wx.wxEVT_LEFT_DOWN)
    #         # evt.SetPosition(wx.Point(0, pos_y))
    #         # self.ProcessEvent(evt)
    #         # event.Skip(False)
    #         event.Skip(True)

    def __on_char_editor(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_TAB and event.ShiftDown():
            if self.curCol == 0:
                event.Skip(False)
            else:
                self.__restaura_list_row = False
                event.Skip(True)

        elif keycode == wx.WXK_TAB:
            if self.curCol == self.GetColumnCount()-1:
                event.Skip(False)
            else:
                self.__restaura_list_row = False
                event.Skip(True)

        elif keycode == wx.WXK_ESCAPE:
            # wx.FutureCall(100, self.restaura_fila, self.curRow)
            event.Skip(True)

        elif keycode == wx.WXK_DOWN:
            event.Skip(False)

        elif keycode == wx.WXK_UP:
            event.Skip(False)

        else:
            event.Skip()

    def __set_focus_editor(self, event):
        if self.IsVirtual():
            if not self.__copia_val_row or self.__copia_val_row[0] != self.curRow:
                copia = self.get_data_row(self.curRow)
                self.__copia_val_row = [self.curRow, copia]
            self.__restaura_list_row = True
        event.Skip(True)

    def __kill_focus_editor(self, event):
        if self.IsVirtual():
            if self.__restaura_list_row:
                wx.FutureCall(100, self.__restaura_fila, self.curRow)
        event.Skip(True)

    def __restaura_fila(self, row):
        if self.__copia_val_row:
            for i in range(0, self.GetColumnCount()):
                txt = self.__copia_val_row[1][i]
                self.SetVirtualData(row, i, txt)

            self.RefreshItem(row)

    def __text_enter_list(self, event):
        #self.SetVirtualData(self.curRow, self.curCol, event.String)
        self.__restaura_list_row = False
        self.CloseEditor()

        if self.__callback_enter:
            actual = self.get_data_row(self.curRow)
            resul = self.__callback_enter(actual)
            if resul is True:       # es correcto
                event.Skip(True)

            elif resul is False:    # error abre el editor
                self.OpenEditor(self.curCol, self.curRow)
                event.Skip(False)

            elif resul is None:     # error y no abre el editor
                self.__restaura_list_row = True
                self.__restaura_fila(self.curRow)
                event.Skip(False)
        else:
            event.Skip(True)

        self.__copia_val_row = None

    def del_row(self, row):
        """ Borra la fila
        """
        self.__copia_val_row = None

        index = self.itemIndexMap[row]
        data = self.itemDataMap.copy()
        del data[index]
        self.set_data(data)

    def set_last_row(self, valores):
        """ Asigna valores a la última fila
        """
        self.__copia_val_row = None

        # Por si se ha realizado alguna ordenación
        self.itemIndexMap = self.itemDataMap.keys()

        k = self.itemIndexMap[len(self.itemIndexMap)-1]
        self.itemDataMap[k] = valores[:]

    def append_row(self, valores):
        """ Añade fila
        """
        self.__copia_val_row = None

        indice = 0
        for v in self.itemIndexMap:
            if v > indice:
                indice = v

        data = self.itemDataMap.copy()
        data[indice + 1] = valores[:]
        self.set_data(data)
