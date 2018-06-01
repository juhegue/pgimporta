# -*- coding: utf-8 -*-

import os
import json
import copy
import wx
from wx.lib.wordwrap import wordwrap
import wx.lib.buttons as buttons
from popup import show_popup
import imagenes.imagenes as imagenes
from parse_select import parse_select
from wx.lib.itemspicker import ItemsPicker, \
                               EVT_IP_SELECTION_CHANGED, \
                               IP_SORT_CHOICES, IP_SORT_SELECTED,\
                               IP_REMOVE_FROM_CHOICES
from bases import *
from util import *
from constantes import *
import codigo


def dialogo_abrir_fic(win, wildcard, fichero=""):
    paths = []
    dlg = wx.FileDialog(win, message="Elija un fichero", defaultFile=fichero, wildcard=wildcard, style=wx.OPEN | wx.CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        paths = dlg.GetPaths()
    return paths


def dialogo_grabar_fic(win, extension_defecto, wildcard, fichero=""):
    resul = None
    dlg = wx.FileDialog(win, message="Grabar fichero como...", defaultFile=fichero, wildcard=wildcard, style=wx.SAVE)#defaultDir=os.getcwd(),
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()

        if '__WXMSW__' not in wx.Platform:  # windows retorna la extensión si no se indica en el dialogo
            nom, ext = os.path.splitext(path)
            if len(ext) == 0 or ext == ".":
                path = "%s.%s" % (nom, extension_defecto)
            else:
                path = nom + ext

        if os.path.exists(path):
            txt = 'Ya existe el archivo ' + path + u'.\n¿Desea Reemplazarlo?'
            dlg1 = wx.MessageDialog(win, txt, 'Grabar fichero', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            if dlg1.ShowModal() == wx.ID_YES:
                resul = path
            dlg1.Destroy()
        else:
            resul = path
    dlg.Destroy()

    return resul


class Dimensiona(object):
    def __init__(self, parent, size=None):
        self.parent = parent
        if size is None:
            size = self.parent.GetSize()
        self.set_size(size)
        self.parent.Bind(wx.EVT_SIZE, self.on_size)

    def set_propi_size(self):
        propi = self.parent.GetTitle()
        valor = self.parent.GetSizeTuple()
        if util.is_windows:
            wx.GetApp().set_propiedad(propi, valor)
        else:
            # TODO:: error en ubuntu 15.04 wx 3.0.0.1
            d1 = valor[0]
            d2 = valor[1] - 28
            wx.GetApp().set_propiedad(propi, (d1, d2))

    def set_size(self, size=None):
        propi = self.parent.GetTitle()
        valor = wx.GetApp().get_propiedad(propi)
        if valor:
            self.parent.SetSize(valor)
        elif size:
            self.parent.SetSize(size)

    def on_size(self, event):
        self.set_propi_size()
        event.Skip(True)


class DlgNotas(BaseSizedDialog):
    def __init__(self, parent, id, titulo, notas=""):
        BaseSizedDialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        pane = self.get_pane()

        # row 1
        wx.StaticText(pane, wx.ID_ANY, "Notas")
        self.txt_notas = wx.TextCtrl(pane, wx.ID_ANY, notas, size=(400, 100), style=wx.TE_MULTILINE)
        self.txt_notas.SetSizerProps(expand=True, proportion=True)

        self.botones()
        self.set_focus_ctrl(self.txt_notas)
        self.fit()
        self.d = Dimensiona(self)

    def get_data(self):
        return self.txt_notas.GetValue()


class DlgCondicion(BaseSizedDialog):
    def __init__(self, parent, id, titulo, valor={}):
        BaseSizedDialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        pane = self.get_pane()

        # row 1
        p = wx.Panel(pane, wx.ID_ANY)
        st = wx.StaticText(p, wx.ID_ANY, u"Definición\npython")
        bmp = imagenes.info.GetBitmap()
        btn = buttons.GenBitmapButton(p, wx.ID_ANY, bmp, size=(26, 26))
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(st, 0, wx.ALL)
        box.Add((10, 10), 0, wx.ALL)
        box.Add(btn, 0, wx.ALIGN_CENTER)
        p.SetSizer(box)

        condicion, continua = ["", 0]
        if valor:
            if "condicion" in valor:
                condicion = valor["condicion"]
            if "continua" in valor:
                continua = valor["continua"]

        self.txt_condi = wx.TextCtrl(pane, wx.ID_ANY, condicion, size=(400, 250), style=wx.TE_MULTILINE)
        self.txt_condi.SetSizerProps(expand=True, proportion=True)

        # row 4
        wx.StaticText(pane, wx.ID_ANY, "\nContinua en:")
        lista = ["Siguiente insert", "Siguiente registro "]
        self.rb = wx.RadioBox(pane, wx.ID_ANY, "", wx.DefaultPosition, wx.DefaultSize, lista, 2, wx.RA_SPECIFY_COLS | wx.NO_BORDER)
        self.rb.SetSelection(continua)
        self.rb.SetSizerProps(expand=True)

        self.botones()
        self.set_focus_ctrl(self.txt_condi)
        self.fit()
        self.d = Dimensiona(self)

        self.Bind(wx.EVT_BUTTON, self.on_ayuda, btn)

    def get_data(self):
        return {"condicion": self.txt_condi.GetValue(), "continua": self.rb.GetSelection()}

    def on_ayuda(self, event):
        txt = "Se tiene acceso a los campos anteponiendo "
        txt += "el prefijo '@' y '@csv.' a los del csv, estos "
        txt += "se deben de poner entre comillas. "
        txt += "Y a la variable global _global y a la "
        txt += "clase DbPostgres con _db.\n"
        txt += "No se realiza el insert si retorna 'True', "
        txt += "continua en el siguiente insert o siguiente "
        txt += "registro según lo definido.."
        txt = wordwrap(txt, 450, wx.ClientDC(self))
        show_popup(self, event, txt)


class DlgValorFijo(BaseSizedDialog):
    def __init__(self, parent, id, titulo, data):
        BaseSizedDialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        nombre = data["nombre"] if data and "nombre" in data else ""
        valor = data["valor"] if data and "valor" in data else ""
        notas = data["notas"] if data and "notas" in data else ""

        pane = self.get_pane()

        # row 1
        wx.StaticText(pane, wx.ID_ANY, "Nombre")
        self.txt_nombre = wx.TextCtrl(pane, wx.ID_ANY, nombre, size=(250, -1))
        self.txt_nombre.SetSizerProps(expand=True)

        # row 2
        wx.StaticText(pane, wx.ID_ANY, "Valor")
        self.txt_valor = wx.TextCtrl(pane, wx.ID_ANY, valor, size=(250, -1))
        self.txt_valor.SetSizerProps(expand=True)

        # row 3
        wx.StaticText(pane, wx.ID_ANY, "Notas")
        self.txt_notas = wx.TextCtrl(pane, wx.ID_ANY, notas, style=wx.TE_MULTILINE)
        self.txt_notas.SetSizerProps(expand=True, proportion=True)  # expand = exapande horizontal, proportion = expande vertical

        self.botones()
        self.set_focus_ctrl(self.txt_nombre)
        self.fit()
        self.d = Dimensiona(self)

    def get_data(self):
        data = dict()
        data["nombre"] = self.txt_nombre.GetValue().strip().encode('ascii', 'ignore')
        data["notas"] = self.txt_notas.GetValue()
        valor = self.txt_valor.GetValue().strip()
        data["valor"] = valor
        return data


class DlgDefCampo(wx.Dialog):
    def __init__(self, parent, id, titulo, data, ayuda, nota=True, ejecuta=False, aceptar=True):
        wx.Dialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        self.ayuda = ayuda

        nombre = data["nombre"] if data and "nombre" in data else ""
        valor = data["valor"] if data and "valor" in data else ""
        notas = data["notas"] if data and "notas" in data else ""

        st1 = wx.StaticText(self, wx.ID_ANY, "Nombre")
        self.txt_nombre = wx.TextCtrl(self, wx.ID_ANY, nombre)

        st2 = wx.Panel(self, wx.ID_ANY)
        st = wx.StaticText(st2, wx.ID_ANY, u"Definición\npython")
        bmp = imagenes.info.GetBitmap()
        btn = buttons.GenBitmapButton(st2, wx.ID_ANY, bmp, size=(26, 26))
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(st, 0, wx.ALL)
        box.Add((10, 10), 0, wx.ALL)
        box.Add(btn, 0, wx.ALIGN_CENTER)
        st2.SetSizer(box)
        self.Bind(wx.EVT_BUTTON, self.on_ayuda, btn)

        self.txt_valor = wx.TextCtrl(self, wx.ID_ANY, valor, style=wx.TE_MULTILINE, size=(-1, 100))

        st3 = wx.StaticText(self, wx.ID_ANY, "Notas")
        self.txt_notas = wx.TextCtrl(self, wx.ID_ANY, notas, style=wx.TE_MULTILINE, size=(-1, 75))

        gbs = wx.GridBagSizer(5, 5)
        gbs.Add(st1, (0, 0), flag=wx.ALL, border=2)
        gbs.Add(self.txt_nombre, (0, 1), flag=wx.EXPAND | wx.ALL, border=2)

        gbs.Add(st2, (1, 0), flag=wx.ALL, border=2)
        gbs.Add(self.txt_valor, (1, 1), flag=wx.EXPAND | wx.ALL, border=2)
        gbs.AddGrowableCol(1)
        gbs.AddGrowableRow(1)

        gbs.Add(st3, (2, 0), flag=wx.ALL, border=2)
        gbs.Add(self.txt_notas, (2, 1), flag=wx.EXPAND | wx.ALL, border=2)

        if not nota:
            st3.Hide()
            self.txt_notas.Hide()

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(gbs, 1, wx.EXPAND | wx.ALL, 10)

        btnsizer = wx.StdDialogButtonSizer()

        if ejecuta:
            btn = wx.Button(self, wx.ID_HELP, "Ejecutar")
            btn.SetDefault()
            btnsizer.AddButton(btn)
            self.Bind(wx.EVT_BUTTON, self.on_ejecuta, btn)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        b=btn

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        box1 = wx.BoxSizer(wx.HORIZONTAL)
        box1.Add((0, 0), 1, wx.EXPAND)
        box1.Add(btnsizer, 0, wx.ALL)

        box.Add(box1, 0, wx.EXPAND, 5)
        box.Add((10,10), 0, wx.EXPAND, 5)

        self.SetSizer(box)
        self.Fit()
        self.SetMinSize((300, 350))
        self.d = Dimensiona(self, (600, 500))
        b.Enable(aceptar)

    def on_ejecuta(self, event):
        valor = self.txt_valor.GetValue().strip()
        codigo.inicia()
        data, err = codigo.codigo(valor, copy.deepcopy(self.parent.data), self.parent.db)
        if err:
            wx.MessageBox(err, APLICACION, wx.ICON_ERROR, self)
        else:
            if self.parent.data != data:
                for k in data.copy().iterkeys():
                    if k.find(CODIGO_INICIAL) == 0:
                        del data[k]
                dlg = wx.MessageDialog(self, 'Se ha modificado el pgi. ¿Desea grabarlo?', APLICACION,
                                       wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                if dlg.ShowModal() == wx.ID_YES:
                    while True:
                        f = dialogo_grabar_fic(self, "pgi", "Archivos pgi (*.pgi)|*.pgi|Todos los archivos (*.*)|*", "")
                        if f:
                            if f == self.parent.fichero_pgi:
                                wx.MessageBox("No se puede sobreescribir el actual, elija otro nombre", APLICACION, wx.ICON_ERROR, self)
                                continue
                            try:
                                with open(f, 'w') as f:
                                    json.dump(data, f, indent=4, sort_keys=True)
                            except IOError, e:
                                wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)
                        break

    def on_ayuda(self, event):
        show_popup(self, event, self.ayuda)

    def get_data(self):
        data = dict()
        data["nombre"] = self.txt_nombre.GetValue().strip().encode('ascii', 'ignore')
        data["notas"] = self.txt_notas.GetValue()
        valor = self.txt_valor.GetValue().strip()
        if not valor:
            valor = "None"
        data["valor"] = valor
        return data


class DlgValorCampoSql(BaseSizedDialog):
    def __init__(self, parent, id, titulo, valor):
        BaseSizedDialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        pane = self.get_pane()

        # row 1
        wx.StaticText(pane, wx.ID_ANY, "Valor")
        self.txt_valor = wx.TextCtrl(pane, wx.ID_ANY, valor, size=(250, -1))
        self.txt_valor.SetSizerProps(expand=True)

        self.botones()
        self.set_focus_ctrl(self.txt_valor)
        self.fit()
        self.d = Dimensiona(self)

    def get_data(self):
        return self.txt_valor.GetValue().strip()


class DlgSql(BaseSizedDialog):
    def __init__(self, parent, id, titulo, data, cb_modificar, insert=None):
        BaseSizedDialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.parent = parent
        self.cb_modificar = cb_modificar

        nombre = data["nombre"] if data and "nombre" in data else ""
        sql = data["sql"] if data and "sql" in data else ""
        self.tablas = data["tablas"] if data and "tablas" in data else None
        notas = data["notas"] if data and "notas" in data else ""

        pane = self.get_pane()

        # row 1
        wx.StaticText(pane, wx.ID_ANY, "Nombre")
        self.txt_nombre = wx.TextCtrl(pane, wx.ID_ANY, nombre, size=(250, -1))
        self.txt_nombre.SetSizerProps(expand=True)

        # row 2
        p = wx.Panel(pane, wx.ID_ANY)
        st = wx.StaticText(p, wx.ID_ANY, "Sql")
        bmp = imagenes.info.GetBitmap()
        btn = buttons.GenBitmapButton(p, wx.ID_ANY, bmp, size=(26, 26))
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(st, 0, wx.ALL)
        box.Add((10, 10), 0, wx.ALL)
        box.Add(btn, 0, wx.ALIGN_CENTER)
        p.SetSizer(box)

        self.txt_sql = wx.TextCtrl(pane, wx.ID_ANY, sql, size=(400, 80), style=wx.TE_MULTILINE)
        self.txt_sql.SetSizerProps(expand=True, proportion=True)

        # row 3
        p = wx.Panel(pane, wx.ID_ANY)
        st = wx.StaticText(p, wx.ID_ANY, "Defecto")
        bmp = imagenes.refrescar.GetBitmap()
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn_refresca = wx.BitmapButton(p, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn_refresca.SetToolTipString("Refrescar campos")
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add((10, 10), wx.ALL)
        box.Add(st, 0, wx.ALL)
        box.Add((10, 10), wx.ALL)
        box.Add(btn_refresca, 0, wx.ALL)
        p.SetSizer(box)

        self.list = BaseEditListCtrl(pane, wx.ID_ANY, style=wx.LC_REPORT, size=(400, 100))
        self.asigna_campos([("", "")])
        self.list.SetSizerProps(expand=True)
        if data and "campos" in data:
            self.set_defecto_campos(data["campos"], sql)

        wx.StaticText(pane, wx.ID_ANY, "Notas")
        self.txt_notas = wx.TextCtrl(pane, wx.ID_ANY, notas, style=wx.TE_MULTILINE)
        self.txt_notas.SetSizerProps(expand=True, proportion=True)

        # row 4
        wx.StaticText(pane, wx.ID_ANY, "\nContinuar")
        lista = ["Siempre", "Si se cumple", "Si no se cumple   "]
        self.rb = wx.RadioBox( pane, wx.ID_ANY, "", wx.DefaultPosition, wx.DefaultSize, lista, 3, wx.RA_SPECIFY_COLS | wx.NO_BORDER)
        self.rb.SetSizerProps(expand=True)
        if data and "continuar" in data:
            self.rb.SetSelection(data["continuar"])

        # row 5
        bmp = imagenes.info.GetBitmap()
        btn_ayuda = buttons.GenBitmapButton(pane, wx.ID_ANY, bmp, size=(26, 26))
        if cb_modificar:
            self.chk_modi = wx.CheckBox(pane, wx.ID_ANY, "Modificar el registro seleccionado en lugar de insertar nuevo")
            if data and "modificar" in data:
                self.chk_modi.SetValue(data["modificar"])

            opciones = insert if insert else list()
            wx.StaticText(pane, wx.ID_ANY)
            p1 = wx.Panel(pane, wx.ID_ANY)
            self.chk_antes = wx.CheckBox(p1, wx.ID_ANY, "Ejecutar justo antes del insert:")
            self.cb_insert = wx.ComboBox(p1, wx.ID_ANY, "", choices=opciones, style=wx.CB_DROPDOWN)
            box1 = wx.BoxSizer(wx.HORIZONTAL)
            box1.Add((4, 4), 0, wx.ALL)
            box1.Add(self.chk_antes, 0, wx.ALL)
            box1.Add((10, 10), 0, wx.ALL)
            box1.Add(self.cb_insert, 0, wx.ALL)
            p1.SetSizer(box1)
            if data and "ejecuta_antes" in data:
                self.chk_antes.SetValue(data["ejecuta_antes"])
                if data and "insert_antes" in data and self.chk_antes.GetValue():
                    self.cb_insert.SetValue(data["insert_antes"])

            self.on_chk_modi(None)
            self.on_chk_antes(None)
        else:
            wx.StaticText(pane, wx.ID_ANY)

        self.botones()
        self.set_focus_ctrl(self.txt_nombre)
        self.fit()
        self.d = Dimensiona(self)

        if self.tablas:
            self.list.set_size_columns("".join(self.tablas))

        self.Bind(wx.EVT_BUTTON, self.on_refresca_campos, btn_refresca)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.on_col_end_drag, self.list)
        self.Bind(wx.EVT_BUTTON, self.on_ayuda, btn_ayuda)
        if cb_modificar:
            self.Bind(wx.EVT_CHECKBOX, self.on_chk_modi, self.chk_modi)
            self.Bind(wx.EVT_CHECKBOX, self.on_chk_antes, self.chk_antes)

        self.Bind(wx.EVT_BUTTON, self.on_ayuda_sql, btn)

    def on_chk_modi(self, event):
        if self.chk_modi.GetValue():
            self.chk_antes.SetValue(False)
            self.cb_insert.SetValue("")
            self.chk_antes.Disable()
            self.cb_insert.Disable()
        else:
            self.chk_antes.Enable()
            self.cb_insert.Enable()

    def on_chk_antes(self, event):
        if self.chk_antes.GetValue():
            self.chk_modi.SetValue(False)
            self.chk_modi.Disable()
        else:
            self.chk_modi.Enable()

    def on_ayuda_sql(self, event):
        txt = "Se tiene acceso a los campos anteponiendo "
        txt += "el prefijo '@' y '@csv.' a los del csv, estos "
        txt += "se deben de poner entre comillas."
        txt = wordwrap(txt, 450, wx.ClientDC(self))
        show_popup(self, event, txt)

    def on_ayuda(self, event):
        if self.cb_modificar:
            txt = u"La sentencia SQL indicada se ejecuta por cada registro " \
                  u"del CSV, antes de realizar insert/update del 'Destino' " \
                  u"Si se marca 'Si se cumple'  y el resultado  de la SQL " \
                  u"no retorna ninguna fila se salta al siguiente registro.\n" \
                  u"Si se marca 'Si no se cumple' y el resultado de la SQL " \
                  u"retorna alguna fila se salta al  siguiente r egistro.\n" \
                  u"Si se marca 'Modificar registro ...'  la select debe " \
                  u"contener una sola tabla con el nombre igual al 'Destino' " \
                  u"y se actualiza esta con los campos devueltos de la select " \
                  u"en lugar de insertar el registro."
        else:
            txt = u"La sentencia SQL indicada se ejecuta al inicio.\n" \
                  u"Si se marca 'Si se cumple'  y el resultado  de la SQL " \
                  u"no retorna ninguna fila finaliza la importación.\n" \
                  u"Si se marca 'Si no se cumple' y el resultado de la SQL " \
                  u"retorna alguna fila finaliza la importación."
        txt = wordwrap(txt, 450, wx.ClientDC(self))
        show_popup(self, event, txt)

    def on_col_end_drag(self, event):
        if self.tablas:
            self.list.set_propi_columns("".join(self.tablas))

    def asigna_campos(self, campos):
        self.list.DeleteAllItems()
        self.list.DeleteAllColumns()
        for i, campo in enumerate(campos):
            self.list.InsertColumn(i, campo[0])
            if i == 0:
                self.list.InsertStringItem(i, campo[1])
            else:
                self.list.SetStringItem(0, i, campo[1])

    def on_refresca_campos(self, event):
        campos_valor = self.get_defecto_campos()
        sql = self.txt_sql.GetValue()
        self.set_defecto_campos(campos_valor, sql)

    def set_defecto_campos(self, campos_valor, sql):
        self.tablas, campos, sql = parse_select(self.parent.db, sql)
        if self.parent.db.error:
            wx.MessageBox(self.parent.db.error, self.parent.app.GetAppName(), wx.ICON_ERROR, self)
            campo_valor = [("", "")]
        else:
            campo_valor = []
            for c in campos:
                if c in campos_valor:
                    campo_valor.append((c, campos_valor[c]))
                else:
                    campo_valor.append((c, "None"))
        self.asigna_campos(campo_valor)

    def get_defecto_campos(self):
        data = dict()
        for i in range(0, self.list.GetColumnCount()):
            col = self.list.GetColumn(i).GetText()
            val = self.list.GetItem(0, i).GetText()
            data[col] = val
        return data

    def get_data(self):
        self.on_refresca_campos(None)

        data = dict()
        data["nombre"] = self.txt_nombre.GetValue().strip()
        data["sql"] = self.txt_sql.GetValue().strip()
        data["campos"] = self.get_defecto_campos()
        data["continuar"] = self.rb.GetSelection()
        data["tablas"] = self.tablas
        data["notas"] = self.txt_notas.GetValue()
        if self.cb_modificar:
            data["modificar"] = self.chk_modi.GetValue()
            data["ejecuta_antes"] = self.chk_antes.GetValue()
            data["insert_antes"] = self.cb_insert.GetValue()
        return data


class DlgLisTablas(BaseSizedDialog):
    def __init__(self, parent, id, titulo, db, data=None):
        BaseSizedDialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE)# | wx.RESIZE_BORDER)

        self.db = db

        pane = self.get_pane()

        # row 1
        p = wx.Panel(pane, wx.ID_ANY)
        btn_todas = wx.Button(p, wx.ID_ANY, "Todas", (0, 20), (100, 35))
        btn_ninguna = wx.Button(p, wx.ID_ANY, "Ninguna", (0, 55), (100, 35))
        btn_pkey = wx.Button(p, wx.ID_ANY, "Primary\nKey", (0, 90), (100, 70))
        self.st_marcadas = wx.StaticText(p, wx.ID_ANY)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(btn_todas, 0, wx.ALL)
        box.Add(btn_ninguna, 0, wx.ALL)
        box.Add(btn_pkey, 0, wx.ALL)
        box.Add(self.st_marcadas, 0, wx.ALL)
        p.SetSizer(box)

        tablas = list()
        for t, n in db.get_registros_tablas():
            nn = "{:,}".format(int(n)).replace(",", ".")
            tablas.append("%s  : %s" % (t, nn))

        self.lb = wx.CheckListBox(pane, wx.ID_ANY, size=wx.DefaultSize, choices=sorted(tablas))
        self.lb.SetSizerProps(expand=True)

        # row 2
        wx.StaticText(pane)
        p = wx.Panel(pane, wx.ID_ANY)
        box = wx.BoxSizer(wx.HORIZONTAL)
        btn_des = wx.Button(p, wx.ID_ANY, "Desmarcar tablas con registros superiores a:")
        self.spin = wx.SpinCtrl(p, wx.ID_ANY, "dddd", (30, 20), size=(120, -1))
        self.spin.SetRange(1, 999999999)
        self.spin.SetValue(1000)
        box.Add(btn_des, 0, wx.ALL)
        box.Add(self.spin, 0, wx.ALL | wx.ALIGN_CENTER)
        p.SetSizer(box)

        # row 3
        btn_fic = wx.Button(pane, wx.ID_ANY, "Fichero...")
        self.txt_fic = wx.TextCtrl(pane, wx.ID_ANY)
        self.txt_fic.SetSizerProps(expand=True)

        if data:
            if "fichero" in data:
                self.txt_fic.SetValue(data["fichero"])

            if "tablas" in data:
                for i, item in enumerate(self.lb.GetItems()):
                    t = item.split(":")[0].strip()
                    if t in data["tablas"]:
                        self.lb.Check(i, True)
                    else:
                        self.lb.Check(i, False)
            if "nregistros" in data:
                self.spin.SetValue(int(data["nregistros"]))

        self.seleccionadas()
        self.botones()
        self.set_focus_ctrl(self.lb)
        self.fit()

        btn_todas.Bind(wx.EVT_BUTTON, self.on_btn_todas)
        btn_ninguna.Bind(wx.EVT_BUTTON, self.on_btn_ninguna)
        btn_pkey.Bind(wx.EVT_BUTTON, self.on_btn_pkey)
        btn_fic.Bind(wx.EVT_BUTTON, self.on_btn_fic)
        btn_des.Bind(wx.EVT_BUTTON, self.on_btn_des)
        self.lb.Bind(wx.EVT_CHECKLISTBOX, self.on_checklistbox)

    def on_checklistbox(self, evt):
        self.seleccionadas()

    def seleccionadas(self):
        reg = len(self.lb.CheckedStrings)
        txt = "\nMarcadas:\n  %s" % reg
        self.st_marcadas.SetLabel(txt)

    def on_btn_todas(self, event):
        for i in range(0, self.lb.GetCount()):
            self.lb.Check(i, True)
        self.seleccionadas()

    def on_btn_ninguna(self, event):
        for i in range(0, self.lb.GetCount()):
            self.lb.Check(i, False)
        self.seleccionadas()

    def on_btn_pkey(self, event):
        # ESTO ES MUY LENTO
        # for i, item in enumerate(self.lb.GetItems()):
        #     if self.db.get_primary_key(item):
        #         self.lb.Check(i, True)
        #     else:
        #         self.lb.Check(i, False)
        tabla_sin = self.db.get_tablas_sin_primary_key()
        for i, item in enumerate(self.lb.GetItems()):
            t = item.split(":")[0].strip()
            self.lb.Check(i, t not in tabla_sin)
        self.seleccionadas()

    def on_btn_des(self, event):
        max = self.spin.GetValue()
        for i, item in enumerate(self.lb.GetItems()):
            reg = int(item.split(":")[1].replace(".", ""))
            if reg > max:
                self.lb.Check(i, False)
        self.seleccionadas()

    def on_btn_fic(self, event):
        fichero = self.txt_fic.Value
        fichero = dialogo_grabar_fic(self, "pgz", "Archivos pgz (*.pgz)|*.pgz|Todos los archivos (*.*)|*", fichero)
        if fichero:
            self.txt_fic.Value = fichero

    def get_data(self):
        data = dict()
        data["nregistros"] = self.spin.Value
        data["fichero"] = self.txt_fic.Value
        data["tablas"] = list()
        for i, item in enumerate(self.lb.CheckedStrings):
            data["tablas"].append(item.split(":")[0].strip())
        return data


# class DlgError(BaseSizedDialog):
#     def __init__(self, parent, id, titulo, data):
#         BaseSizedDialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
#
#         pane = self.get_pane()
#
#         # row 1
#         txt = wx.TextCtrl(pane, wx.ID_ANY, data, size=(600, 400), style=wx.TE_MULTILINE)
#         txt.SetSizerProps(expand=True)
#
#         self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK))
#         txt.SetFocus()
#
#         self.fit()
LOG_DETALLE = False
LOG_SQL = False


class DlgImportar(wx.Dialog):

    def __init__(self, *args, **kw):
        super(DlgImportar, self).__init__(*args, **kw)

        self.data = [None, 0, 0]
        self.inicia()
        self.SetSize((400, 250))

    def inicia(self):
        p = wx.Panel(self)

        bmp = wx.ArtProvider_GetBitmap(wx.ART_TIP, wx.ART_OTHER, (16, 16))
        stb = wx.StaticBitmap(p, -1, bmp, (16, 16))
        stt = wx.StaticText(p, label="Elija probar si no desea actualizar la BD.")
        font = stt.GetFont()
        font.SetStyle(wx.ITALIC)
        stt.SetFont(font)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(stb, border=4, flag=wx.ALIGN_CENTER|wx.ALL)
        hbox.Add(stt)

        self.chk_log = wx.CheckBox(p, wx.ID_ANY, u"Log detallado")
        self.chk_log.SetValue(LOG_DETALLE)
        self.chk_sql = wx.CheckBox(p, wx.ID_ANY, u"Generar SQL")
        self.chk_sql.SetValue(LOG_SQL)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, border=10)
        vbox.Add(self.chk_log, flag=wx.ALIGN_LEFT|wx.ALL, border=10)
        vbox.Add(self.chk_sql, flag=wx.ALIGN_LEFT|wx.ALL, border=10)

        sb = wx.StaticBox(p)
        sbs = wx.StaticBoxSizer(sb, orient=wx.HORIZONTAL)
        sbs.Add(vbox, flag=wx.ALIGN_CENTER)

        p.SetSizer(sbs)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_probar = wx.Button(self, label='Probar')
        self.btn_importar = wx.Button(self, label='Importar')
        self.btn_cancelar = wx.Button(self, label='Cancelar')

        hbox.Add(self.btn_probar, flag=wx.RIGHT, border=20)
        hbox.Add(self.btn_importar, border=20)
        hbox.Add(self.btn_cancelar, flag=wx.LEFT, border=20)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(p, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        vbox.Add(hbox, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        self.SetSizer(vbox)
        self.btn_cancelar.SetFocus()

        self.btn_probar.Bind(wx.EVT_BUTTON, self.on_close)
        self.btn_importar.Bind(wx.EVT_BUTTON, self.on_close)
        self.btn_cancelar.Bind(wx.EVT_BUTTON, self.on_close)

    def on_close(self, event):
        global LOG_DETALLE
        global LOG_SQL
        LOG_DETALLE = self.chk_log.Value
        LOG_SQL = self.chk_sql.Value
        label = event.GetEventObject().GetLabel().lower()
        self.data[0] = None if label == "cancelar" else label
        self.data[1] = 1 if self.chk_log.Value else 0
        self.data[2] = 1 if self.chk_sql.Value else 0
        self.Close()

    def get_data(self):
        return self.data


class DlgExportaCSV(wx.Dialog):
    def __init__(self, parent, id, titulo, campos, seleccionados):
        wx.Dialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE)# | wx.RESIZE_BORDER)

        self.data = dict()

        no_seleccionados = list()
        for i, c in enumerate(campos[:]):
            if c not in seleccionados:
                no_seleccionados.append(c)

        p = wx.Panel(self, wx.ID_ANY)
        self.ip = ItemsPicker(p, wx.ID_ANY, no_seleccionados, 'Campos:', 'Seleccionados:', ipStyle=IP_REMOVE_FROM_CHOICES)
        self.ip.SetSelections(seleccionados)
        self.ip._source.SetMinSize((250, 300))

        self.chk_nombres = wx.CheckBox(p, wx.ID_ANY, u"Nombre de campos en la 1º línea")

        btn_fic = wx.Button(p, wx.ID_ANY, "Fichero...")
        self.txt_fic = wx.TextCtrl(p, value="")

        self.btn_cancelar = wx.Button(p, label='Cancelar')
        self.btn_aceptar = wx.Button(p, label='Aceptar')

        box1 = wx.BoxSizer()
        box1.Add(btn_fic, 0, wx.ALL, border=10)
        box1.Add(self.txt_fic, 1, wx.ALIGN_CENTER)
        box1.Add((10, 0), 0, wx.ALL)

        box2 = wx.BoxSizer()
        box2.Add((0, 0), 1, wx.EXPAND)
        box2.Add(self.btn_cancelar, 0, wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        box2.Add(self.btn_aceptar, 0,  wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_CENTER, 10)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.ip, 0, wx.ALL)
        box.Add(self.chk_nombres, 0, wx.ALL, border=10)
        box.Add(box1, 1, wx.EXPAND)
        box.Add(box2, 1, wx.EXPAND)
        p.SetSizer(box)

        box.Fit(self)
        self.btn_cancelar.SetFocus()

        self.btn_aceptar.Bind(wx.EVT_BUTTON, self.on_close)
        self.btn_cancelar.Bind(wx.EVT_BUTTON, self.on_close)
        btn_fic.Bind(wx.EVT_BUTTON, self.on_btn_fic)

    def on_close(self, event):
        if event.EventObject == self.btn_aceptar:
            self.data["ok"] = True

        elif event.EventObject == self.btn_cancelar:
            self.data["ok"] = False

        self.data["campos"] = self.ip.GetSelections()
        self.data["fichero"] = self.txt_fic.Value
        self.data["nombres1"] = self.chk_nombres.Value

        self.Close()

    def on_btn_fic(self, event):
        fichero = self.txt_fic.Value
        fichero = dialogo_grabar_fic(self, "csv", "Archivos csv (*.csv)|*.csv|Todos los archivos (*.*)|*", fichero)
        if fichero:
            self.txt_fic.Value = fichero


# https://wxpython.org/Phoenix/docs/html/sizers_overview.html
