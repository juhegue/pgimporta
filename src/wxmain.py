# -*- coding: utf-8 -*-

import os
import sys
import shutil
import pickle
import json
import tempfile
import traceback
import webbrowser

import wx
from wx.lib.wordwrap import wordwrap
import wx.lib.agw.infobar as IB

import imagenes.imagenes as imagenes
import codigo
import util
from csvunicode import UnicodeReader, UnicodeWriter
from dbpostgres import DbPostgres
from frmsql import FrmSql
from frmcompara import FrmCompara
from importa import Importa
from exp_comp import exporta_tabla, compara_tabla
from util_zip import Zip
from dialogos import *
from constantes import *
from exception import ExceptionHook
from bases import *
from dlg_filtros import Filtros
from pgi import Pgi


reload(sys)
#  sys.setdefaultencoding(sys.getfilesystemencoding())
sys.setdefaultencoding("UTF-8")
del sys.setdefaultencoding


class Cursor:
    def __init__(self):
        self.pila = []

    def pon_reloj(self):
        c = self.GetCursor()
        self.pila.append(c)
        self.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))

    def quita_reloj(self):
        c = self.pila.pop()
        self.SetCursor(c)


class Frame(BaseFrame, Cursor):
    encode_anterior = "utf-8"

    def __init__(self, app):
        BaseFrame.__init__(self, None, wx.ID_ANY, app.GetAppName(), size=(800, 600))
        Cursor.__init__(self)

        self.app = app
        self.fichero_pgi = ""
        self.tree_org_item = self.tree_des_item = self.tree_des_cam_item = None   # item seleccionado
        self.list_csv_campo_select = None    # campo seleccionado
        self.data = app.get_propiedad("Datos")
        self.dlg_grabar_db_datos = app.get_propiedad("DlgGrabarDB")
        self.buffer_tablas = None
        self.buffer_campos = None

        if not self.data:
            self.data = dict()

        if not self.dlg_grabar_db_datos:
            self.dlg_grabar_db_datos = []

        self.db = DbPostgres()

        self.SetIcon(imagenes.importar.GetIcon())

        self.imglst = wx.ImageList(16, 16, True)
        self.idxcam = self.imglst.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16)))
        self.idxpropi = self.imglst.Add(wx.ArtProvider_GetBitmap(wx.ART_LIST_VIEW, wx.ART_OTHER, (16, 16)))
        # self.idxasig = self.imglst.Add(wx.ArtProvider_GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_OTHER, (16, 16)))
        # self.idxmarca = self.imglst.Add(wx.ArtProvider_GetBitmap(wx.ART_TICK_MARK, wx.ART_OTHER, (16, 16)))
        self.idxasig = self.imglst.Add(imagenes.asigna.GetBitmap())
        self.idxmarca = self.imglst.Add(imagenes.marcaa.GetBitmap())
        self.idxkey = self.imglst.Add(imagenes.key.GetBitmap())
        self.idxlibro = self.imglst.Add(imagenes.libro.GetBitmap())
        self.idxlibroa = self.imglst.Add(imagenes.libro_azul.GetBitmap())
        self.idxlibrov = self.imglst.Add(imagenes.libro_verde.GetBitmap())
        self.idxlibrok = self.imglst.Add(imagenes.libro_azul_key.GetBitmap())
        self.idxlibrok2 = self.imglst.Add(imagenes.libro_azul_key2.GetBitmap())
        self.idxpazul = self.imglst.Add(imagenes.pazul.GetBitmap())
        self.idxprojo = self.imglst.Add(imagenes.projo.GetBitmap())
        self.idxpverde = self.imglst.Add(imagenes.pverde.GetBitmap())
        self.idxproc = self.imglst.Add(imagenes.process.GetBitmap())
        self.idxsmile = self.imglst.Add(imagenes.smiles.GetBitmap())
        self.idxmis = self.imglst.Add(imagenes.miscellaneous.GetBitmap())
        self.idxsql = self.imglst.Add(imagenes.sql.GetBitmap())
        self.idxpython = self.imglst.Add(imagenes.python.GetBitmap())
        self.idxcsv = self.imglst.Add(imagenes.csv.GetBitmap())
        #self.idxdb1 = self.imglst.Add(imagenes.db1.GetBitmap())
        #self.idxdb2 = self.imglst.Add(imagenes.db2.GetBitmap())
        #self.idxdb3 = self.imglst.Add(imagenes.db3.GetBitmap())
        #self.refrescar = self.imglst.Add(imagenes.refrescar.GetBitmap())

        if util.is_windows:
            app.RedirectStdio()

        sb = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        sfont = sb.GetFont()
        sfont.SetWeight(wx.BOLD)
        sb.SetFont(sfont)
        sb.SetStatusWidths([-3, -1])
        self.info("...")

        self.crea_menu()
        self.crea_tool_bar()
        w0, w1, w2 = self.crea_contenedor()
        self.crea_notebook(w0)
        self.crea_panel_origen(w1)
        self.crea_panel_destino(w2)

        self.set_size()

        self.Bind(wx.EVT_CLOSE, self.on_close_window)
        self.Bind(wx.EVT_SIZE, self.on_size)

        #wx.FutureCall(1000, self.on_load)
        wx.CallAfter(self.on_load)

    def on_load(self):
        if self.data:
            self.pon_reloj()
            busy = wx.BusyInfo("Cargando...", self)
            wx.Yield()
            try:
                self.set_data(self.data)
            except:
                self.on_nuevo(None)
            del busy
            self.quita_reloj()

        self.text_host.SetFocus()
        self.text_host.SetSelection(-1, -1)

    def on_csv_modifica(self, event):
        self.get_data()
        fichero = self.data[FICHERO_CSV]["fichero"]
        delimitador = self.data[FICHERO_CSV]["delimitador"]
        nombres1 = self.data[FICHERO_CSV]["nombres1"]
        lineas = self.data[FICHERO_CSV]["lineas"]
        encode = self.data[FICHERO_CSV]["encode"]

        error = False
        try:
            unicode("probando encode...", encoding=encode, errors="ignore")
        except LookupError, e:
            encode = self.encode_anterior
            self.data[FICHERO_CSV]["encode"] = encode
            error = str(e)

        self.carga_fichero_csv(fichero, delimitador, nombres1, lineas, encode)

        if error:
            wx.MessageBox("%s.\n\nSe ha restaurado a: %s" % (error, encode), APLICACION, wx.ICON_ERROR)

    def on_sel_tree_org_changed(self, event):
        self.tree_org_item = event.GetItem()
        txt = self.tree_org.GetPyData(self.tree_org_item)
        self.info(str(txt))

    def on_sel_tree_des_changed(self, event):
        self.tree_des_item = event.GetItem()
        txt = self.tree_des.GetPyData(self.tree_des_item)
        self.info(str(txt))

    def on_sel_tree_des_cam_changed(self, event):
        self.tree_des_cam_item = event.GetItem()
        txt = self.tree_des_cam.GetPyData(self.tree_des_cam_item)
        self.info(str(txt))

    def on_right_org(self, event):
        if not hasattr(self, "orgID1"):
            self.orgID1 = wx.NewId()
            self.orgID2 = wx.NewId()
            self.orgID3 = wx.NewId()
            self.orgID4 = wx.NewId()
            self.orgID5 = wx.NewId()
            self.orgID6 = wx.NewId()
            self.orgID7 = wx.NewId()
            self.orgID8 = wx.NewId()
            self.orgID9 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_refresh_org, id=self.orgID1)
            self.Bind(wx.EVT_MENU, self.on_add_valor_fijo, id=self.orgID2)
            self.Bind(wx.EVT_MENU, self.on_add_sql_inicial, id=self.orgID3)
            self.Bind(wx.EVT_MENU, self.on_add_sql_registro, id=self.orgID4)
            self.Bind(wx.EVT_MENU, self.on_editar_org, id=self.orgID5)
            self.Bind(wx.EVT_MENU, self.on_eliminar_org, id=self.orgID6)
            self.Bind(wx.EVT_MENU, self.on_add_cam_registro, id=self.orgID7)
            self.Bind(wx.EVT_MENU, self.on_add_codigo_inicial, id=self.orgID8)
            self.Bind(wx.EVT_MENU, self.on_add_codigo_final, id=self.orgID9)

        item = self.tree_org.GetSelection()
        root = self.tree_org.GetRootItem()
        nom_item = nom_padre = nom_abuelo = None
        if item.IsOk():
            nom_item = self.tree_org.GetItemText(item)
            padre = self.tree_des_cam.GetItemParent(item)
            if padre.IsOk():
                nom_padre = self.tree_org.GetItemText(padre)
                abuelo = self.tree_des_cam.GetItemParent(padre)
                if abuelo.IsOk():
                    nom_abuelo = self.tree_org.GetItemText(abuelo)

        menu = wx.Menu()

        item1 = wx.MenuItem(menu, self.orgID1, u"Refrescar")
        item8 = wx.MenuItem(menu, self.orgID8, u"Añadir Código Inicial")
        item2 = wx.MenuItem(menu, self.orgID2, u"Añadir Valor Fijo")
        item3 = wx.MenuItem(menu, self.orgID3, u"Añadir Sql Inicial")
        item4 = wx.MenuItem(menu, self.orgID4, u"Añadir Sql por Registro")
        item7 = wx.MenuItem(menu, self.orgID7, u"Añadir Campo por Registro")
        item9 = wx.MenuItem(menu, self.orgID9, u"Añadir Código Final")
        item5 = wx.MenuItem(menu, self.orgID5, u"Editar")
        item6 = wx.MenuItem(menu, self.orgID6, u"Eliminar")
        menu.AppendItem(item1)
        menu.AppendSeparator()
        menu.AppendItem(item8)
        menu.AppendItem(item2)
        menu.AppendItem(item3)
        menu.AppendItem(item4)
        menu.AppendItem(item7)
        menu.AppendItem(item9)
        menu.AppendSeparator()
        menu.AppendItem(item5)
        menu.AppendSeparator()
        menu.AppendItem(item6)

        if not item.IsOk():
            item6.Enable(False)

        if nom_padre != VALOR_FIJO and nom_padre != SQL_INI and nom_padre != SQL_REG\
                and nom_abuelo != SQL_INI and nom_abuelo != SQL_REG:
            item5.Enable(False)

        if item != root and nom_item != VALOR_FIJO and nom_item != SQL_INI and nom_item != SQL_REG and\
                        nom_item != FICHERO_CSV and nom_padre != VALOR_FIJO and nom_padre != SQL_INI and\
                        nom_padre != SQL_REG:
            item6.Enable(False)

        if nom_abuelo == "Origen" and (nom_padre == CAMPO_REG or nom_padre == CODIGO_INICIAL
                                       or nom_padre == CODIGO_FINAL):
            item5.Enable(True)
            item6.Enable(True)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_refresh_org(self, event):
        self.carga_origen()
        self.tree_org.CollapseAll()
        root = self.tree_org.GetRootItem()
        if root:
            self.tree_org.Expand(root)
            self.tree_org_item = root
        else:
            self.tree_org_item = None
            self.info("None")

    def on_add_codigo_inicial(self, event):
        self.dialogo_codigo(titulo=CODIGO_INICIAL)

    def on_add_codigo_final(self, event):
        self.dialogo_codigo(titulo=CODIGO_FINAL)

    def on_add_valor_fijo(self, event):
        self.dialogo_fijo()

    def on_add_sql_inicial(self, event):
        self.dialogo_inicial()

    def on_add_sql_registro(self, event):
        self.dialogo_registro()

    def on_add_cam_registro(self, event):
        self.dialogo_campo_reg()

    def on_editar_org(self, event):
        item = self.tree_org.GetSelection()
        if item.IsOk():
            key = self.tree_org.GetPyData(item).split(":")
            parent = self.tree_org.GetItemParent(item)
            txt = self.tree_org.GetItemText(parent)
            if txt == VALOR_FIJO:
                for k, v in self.data.iteritems():
                    if k.find(VALOR_FIJO) == 0 and v["nombre"] == key[2]:
                        data = self.data[k]
                        self.dialogo_fijo(data, k)
                        break
            elif txt == SQL_INI:
                for k, v in self.data.iteritems():
                    if k.find(SQL_INI) == 0 and v["nombre"] == key[2]:
                        data = self.data[k]
                        self.dialogo_inicial(data, k)
                        break
            elif txt == SQL_REG:
                for k, v in self.data.iteritems():
                    if k.find(SQL_REG) == 0 and v["nombre"] == key[2]:
                        data = self.data[k]
                        self.dialogo_registro(data, k)
                        break
            elif txt == CAMPO_REG:
                for k, v in self.data.iteritems():
                    if k.find(CAMPO_REG) == 0 and v["nombre"] == key[2]:
                        data = self.data[k]
                        self.dialogo_campo_reg(data, k)
                        break
            elif txt == CODIGO_INICIAL:
                for k, v in self.data.iteritems():
                    if k.find(CODIGO_INICIAL) == 0 and v["nombre"] == key[2]:
                        data = self.data[k]
                        self.dialogo_codigo(data, k, titulo=CODIGO_INICIAL)
                        break
            elif txt == CODIGO_FINAL:
                for k, v in self.data.iteritems():
                    if k.find(CODIGO_FINAL) == 0 and v["nombre"] == key[2]:
                        data = self.data[k]
                        self.dialogo_codigo(data, k, titulo=CODIGO_FINAL)
                        break
            else:
                for k, v in self.data.iteritems():
                    if k.find(SQL_INI) == 0 and v["nombre"] == key[2]:
                        data = self.data[k]
                        campo = key[3].split(".")[1]
                        self.dialogo_campo(data, campo, item)
                        break
                    if k.find(SQL_REG) == 0 and v["nombre"] == key[2]:
                        data = self.data[k]
                        campo = key[3].split(".")[1]
                        self.dialogo_campo(data, campo, item)
                        break

    def on_eliminar_org(self, event):
        item = self.tree_org.GetSelection()
        if item.IsOk():
            marca = None
            keys_borra = []
            key = self.tree_org.GetPyData(item).split(":")
            if key[0] == "0":
                for k in self.data.iterkeys():
                    if k.find(VALOR_FIJO) == 0 or k.find(SQL_INI) == 0 or k.find(SQL_REG) == 0 \
                            or k.find(FICHERO_CSV) == 0 or k.find(CAMPO_REG) == 0 :
                        keys_borra.append(k)
            elif key[0] == "1":
                for k in self.data.iterkeys():
                    if k.find(key[1]) == 0:
                        keys_borra.append(k)
                marca = "0:root"
            elif key[0] == "2":
                for k, v in self.data.iteritems():
                    if key[1] == VALOR_FIJO:
                        if k.find(key[1]) == 0 and v["nombre"] == key[2]:
                            keys_borra.append(k)
                            marca = "1:" + key[1]
                    else:
                        if k.find(key[1]) == 0 and v["nombre"] == key[2]:
                            keys_borra.append(k)
                            marca = "1:" + key[1]

            for k in keys_borra:
                del self.data[k]

            self.carga_origen()
            if marca:
                item = util.tree_get_item_data(self.tree_org, marca)
                if not item:
                    item = self.tree_org.GetRootItem()
                if item:
                    util.tree_expand_item(self.tree_org, item)
                    self.tree_org.SelectItem(item)

    def on_dclick_org(self, event):
        pt = event.GetPosition()
        item_org, flags = self.tree_org.HitTest(pt)
        if not item_org.IsOk():
            return

        # cuando esta vacio da error
        try:
            key_org = self.tree_org.GetPyData(item_org)
        except:
            return

        if self.tree_des_cam_item and key_org:
            key_des = self.tree_org.GetPyData(self.tree_des_cam_item)
            if key_des:
                key_org = key_org.split(":")
                key_des = key_des.split(":")
                if key_org[0] == "2":
                    if key_des[0] == "2":
                        if key_org[1] != SQL_INI and key_org[1] != SQL_REG and key_org[1] != CODIGO_INICIAL \
                                and key_org[1] != CODIGO_FINAL:
                            self.asigna(key_org[2], key_des[1], key_des[2])
                            event.Skip(False)
                            return
                elif key_org[0] == "3":
                    if key_des[0] == "2":
                        self.asigna(key_org[3], key_des[1], key_des[2])
                        event.Skip(False)
                        return
        event.Skip(True)

    def on_keydown_org(self, event):
        self.tree2clipboard(event, self.tree_org)
        event.Skip(True)

    def tree_org_cambia(self, modo):
        item = self.tree_org.GetSelection()
        if item.IsOk():
            data = self.tree_org.GetPyData(item)
            val = data.split(":")
            if val[0] == "2" and val[1] != FICHERO_CSV and val[1] != ID_INSERT:
                key_org = None
                for k, v in self.data.iteritems():
                    if k.find(val[1]) == 0 and v["nombre"] == val[2]:
                        key_org = k
                if key_org:
                    key = None
                    for k, v in sorted(self.data.iteritems()):
                        if k.find(val[1]) == 0:
                            if modo:
                                if key and key_org == k:
                                    tmp = self.data[key_org]
                                    self.data[key_org] = self.data[key]
                                    self.data[key] = tmp
                                    break
                                key = k
                            else:
                                if key:
                                    tmp = self.data[key_org]
                                    self.data[key_org] = self.data[k]
                                    self.data[k] = tmp
                                    break
                                if key_org == k:
                                    key = k
                    self.carga_origen()
                    #root = self.tree_org.GetRootItem()
                    #util.tree_expand_item(self.tree_org, root)
                    #util.tree_expand_item(self.tree_org, root)
                    item = util.tree_get_item_data(self.tree_org, data)
                    self.tree_org.SelectItem(item)
                    #self.tree_org.EnsureVisible(item)

    def on_tree_org_arriba(self, event):
        self.tree_org_cambia(True)

    def on_tree_org_abajo(self, event):
        self.tree_org_cambia(False)

    def on_dclick_des(self, event):
        pt = event.GetPosition()
        item_des, flags = self.tree_des_cam.HitTest(pt)
        if not item_des.IsOk():
            return
        # cuando esta vacio da error
        try:
            key_des = self.tree_des_cam.GetPyData(item_des)
        except:
            return

        if self.tree_org_item and key_des:
            key_org = self.tree_org.GetPyData(self.tree_org_item)
            if key_org:
                key_org = key_org.split(":")
                key_des = key_des.split(":")
                if key_des[0] == "2":
                    if key_org[0] == "2" and key_org[1] != SQL_REG and key_org[1] != SQL_INI\
                            and key_org[1] != CODIGO_INICIAL and key_org[1] != CODIGO_FINAL:
                        self.asigna(key_org[2], key_des[1], key_des[2])
                        event.Skip(False)
                        return
                    if key_org[0] == "3":
                        self.asigna(key_org[3], key_des[1], key_des[2])
                        event.Skip(False)
                        return
        event.Skip(True)

    def on_dkey_des(self, event):
        #if event.GetKeyCode() == wx.WXK_F2:
        #    print "F2"
        #elif event.GetKeyCode() == wx.WXK_INSERT:
        #    print "INsert"
        if event.GetKeyCode() == wx.WXK_DELETE:
            item = self.tree_des_cam.GetSelection()
            if item.IsOk():
                txt = self.tree_des_cam.GetItemText(item)
                if txt.find("=") >= 0:
                    self.on_desasigna_campo(event)
                else:
                    self.on_elimina_tabla(event)
        else:
            event.Skip()

    def on_keydown_des(self, event):
        self.tree2clipboard(event, self.tree_des_cam)
        event.Skip(True)

    def on_collapsed_des(self, event):
        item = event.GetItem()
        util.tree_collapse(self.tree_des_cam, item)

    def tree_des_cambia(self, modo):
        item = self.tree_des_cam.GetSelection()
        if item.IsOk():
            data = self.tree_des_cam.GetPyData(item)
            val = data.split(":")
            if val[0] == "1":
                key_org = None
                for k, v in self.data.iteritems():
                    if k.find(ID_INSERT) == 0 and v[0] == val[1]:
                        key_org = k
                if key_org:
                    key = None
                    for k, v in sorted(self.data.iteritems()):
                        if k.find(ID_INSERT) == 0:
                            if modo:
                                if key and key_org == k:
                                    tmp = self.data[key_org]
                                    self.data[key_org] = self.data[key]
                                    self.data[key] = tmp
                                    break
                                key = k
                            else:
                                if key:
                                    tmp = self.data[key_org]
                                    self.data[key_org] = self.data[k]
                                    self.data[k] = tmp
                                    break
                                if key_org == k:
                                    key = k
                    self.carga_destino()
                    #root = self.tree_des_cam.GetRootItem()
                    #util.tree_expand_item(self.tree_des_cam, root)
                    item = util.tree_get_item_data(self.tree_des_cam, data)
                    self.tree_des_cam.SelectItem(item)
                    #self.tree_des_cam.EnsureVisible(item)

    def on_tree_des_cam_arriba(self, event):
        self.tree_des_cambia(True)

    def on_tree_des_cam_abajo(self, event):
        self.tree_des_cambia(False)

    def on_tree_des_cam_refrescar(self, event):
        self.pon_reloj()
        busy = wx.BusyInfo("Cargando...", self)
        wx.Yield()
        for k, v in self.data.copy().iteritems():
            if k.find(ID_INSERT) == 0:
                tabla = v[0]
                campos = v[1]
                ids = v[2]
                dic_campos = dict()
                for campo in campos:
                    nom = campo[0][0]
                    dic_campos[nom] = campo

                nom_campos = list()
                for c in self.db.get_campos(tabla[3:]):
                    nom = c[0]
                    nom_campos.append(nom)
                    if nom not in dic_campos:
                        # print "%s nuevo %s" % (k, nom)
                        dic_campos[nom] = [c, None]

                for key in dic_campos.copy().iterkeys():
                    if key not in nom_campos:
                        # print "%s borra %s" % (k, key)
                        del dic_campos[key]

                campos = list()
                for valor in dic_campos.itervalues():
                    campos.append(valor)
                self.data[k] = [tabla, campos, ids]
        del busy
        self.quita_reloj()
        self.carga_destino()

        item = self.tree_des_cam.GetRootItem()
        if item:
            self.tree_des_cam.Expand(item)

    def on_right_db(self, event):
        if not hasattr(self, "dbID1"):
            self.dbID1 = wx.NewId()
            self.dbID2 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_refresh_db, id=self.dbID1)
            self.Bind(wx.EVT_MENU, self.on_sql, id=self.dbID2)

        menu = wx.Menu()
        item1 = wx.MenuItem(menu, self.dbID1, "Refrescar tablas")
        item2 = wx.MenuItem(menu, self.dbID2, "Visor Sql")
        menu.AppendItem(item1)
        menu.AppendSeparator()
        menu.AppendItem(item2)
        self.PopupMenu(menu)
        menu.Destroy()

    def on_right_des(self, event):
        if not hasattr(self, "camposID1"):
            self.camposID1 = wx.NewId()
            self.camposID2 = wx.NewId()
            self.camposID3 = wx.NewId()
            self.camposID4 = wx.NewId()
            self.camposID5 = wx.NewId()
            self.camposID6 = wx.NewId()
            self.camposID7 = wx.NewId()
            self.camposID8 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_desasigna_campo, id=self.camposID1)
            self.Bind(wx.EVT_MENU, self.on_elimina_tabla, id=self.camposID2)
            self.Bind(wx.EVT_MENU, self.on_refresca_campos_tabla, id=self.camposID3)
            self.Bind(wx.EVT_MENU, self.on_notas_tabla, id=self.camposID4)
            self.Bind(wx.EVT_MENU, self.on_condicion_tabla, id=self.camposID5)
            self.Bind(wx.EVT_MENU, self.on_elimina_condicion_tabla, id=self.camposID6)
            self.Bind(wx.EVT_MENU, self.on_copiar_tabla, id=self.camposID7)
            self.Bind(wx.EVT_MENU, self.on_pegar_tabla, id=self.camposID8)

        item = self.tree_des_cam.GetSelection()
        if item.IsOk():
            txt = self.tree_des_cam.GetItemText(item)
            root = self.tree_des_cam.GetRootItem()
            padre = self.tree_des_cam.GetItemParent(item)
            data = self.tree_des_cam.GetPyData(item)

            menu = wx.Menu()
            item3 = wx.MenuItem(menu, self.camposID3, "Refrescar campos")
            item7 = wx.MenuItem(menu, self.camposID7, "Copiar")
            item8 = wx.MenuItem(menu, self.camposID8, "Pegar")
            item1 = wx.MenuItem(menu, self.camposID1, "Desasignar campo")
            item5 = wx.MenuItem(menu, self.camposID5, u"Condición")
            item6 = wx.MenuItem(menu, self.camposID6, u"Elimina Condición")
            if root == item:
                item2 = wx.MenuItem(menu, self.camposID2, "Eliminar tablas")
            else:
                item2 = wx.MenuItem(menu, self.camposID2, "Eliminar tabla")
            item4 = wx.MenuItem(menu, self.camposID4, "Notas")
            menu.AppendItem(item3)
            menu.AppendSeparator()
            menu.AppendItem(item7)
            menu.AppendItem(item8)
            menu.AppendSeparator()
            menu.AppendItem(item1)
            menu.AppendSeparator()
            menu.AppendItem(item5)
            menu.AppendItem(item6)
            menu.AppendSeparator()
            menu.AppendItem(item2)
            menu.AppendSeparator()
            menu.AppendItem(item4)

            tabla = data.split(":")[1]
            if CONDICION_TABLA not in self.data or tabla not in self.data[CONDICION_TABLA]:
                item6.Enable(False)

            if root == padre or root == item:
                if root == item:
                    item5.Enable(False)
                    item6.Enable(False)
                    item7.Enable(False)
                    item8.Enable(False)
                item1.Enable(False)
            else:
                item2.Enable(False)
                item5.Enable(False)
                item6.Enable(False)
                item7.Enable(False)
                item8.Enable(False)
                if txt.find("=") < 0:
                    item1.Enable(False)

            if root == item:
                item4.Enable(False)

            a, b, c = self.clipboard_get_tabla()
            if not a or not b or not c:
                item8.Enable(False)

            self.PopupMenu(menu)
            menu.Destroy()

    def on_desasigna_campo(self, event):
        item = self.tree_des_cam.GetSelection()
        key = self.tree_des_cam.GetPyData(item).split(":")
        self.tree_des_cam.SetItemText(item, key[2])
        self.tree_des_cam.SetItemImage(item, self.idxcam, wx.TreeItemIcon_Normal)
        for k, v in self.data.iteritems():
            if k.find(ID_INSERT) == 0 and v[0] == key[1]:
                for i in range(0, len(self.data[k][1])):
                    if self.data[k][1][i][0][0] == key[2]:
                        self.data[k][1][i][1] = None

        item = self.tree_org.GetSelection()
        data = self.tree_org.GetPyData(item) if item.IsOk() else None
        self.carga_origen()
        if data:
            item = util.tree_get_item_data(self.tree_org, data)
            if item and item.IsOk():
                self.tree_org.SelectItem(item)
            else:
                root = self.tree_org.GetRootItem()
                util.tree_expand_item(self.tree_org, root)
        #  util.tree_expand_item(self.tree_org, util.tree_get_item_text(self.tree_org, FICHERO_CSV))
        #  item = util.tree_get_item_text(self.tree_org, FICHERO_CSV)
        #  self.tree_org.SelectItem(item)
        #root = self.tree_org.GetRootItem()
        #util.tree_expand_item(self.tree_org, root)

    def on_elimina_tabla(self, event):
        item = self.tree_des_cam.GetSelection()
        if item.IsOk():
            keys_borra = []
            key = self.tree_des_cam.GetPyData(item).split(":")
            if key[0] == "0":
                for k, v in self.data.iteritems():
                    if k.find(ID_INSERT) == 0:
                        keys_borra.append(k)
            elif key[0] == "1":
                for k, v in self.data.iteritems():
                    if k.find(ID_INSERT) == 0 and v[0] == key[1]:
                        keys_borra.append(k)

            for k in keys_borra:
                v = self.data[k]
                if NOTAS_TABLA in self.data and v[0] in self.data[NOTAS_TABLA]:
                    del self.data[NOTAS_TABLA][v[0]]
                if CONDICION_TABLA in self.data and v[0] in self.data[CONDICION_TABLA]:
                    del self.data[CONDICION_TABLA][v[0]]
                del self.data[k]

            self.carga_destino()
            root = self.tree_des_cam.GetRootItem()
            if root:
                util.tree_expand_item(self.tree_des_cam, root)

            self.carga_origen()
            item = util.tree_get_item_data(self.tree_org, "1:" + ID_INSERT)
            if item:
                util.tree_expand_item(self.tree_org, item)
            else:
                root = self.tree_org.GetRootItem()
                if root:
                    util.tree_expand_item(self.tree_org, root)

    def on_refresca_campos_tabla(self, event):
        for k, v in self.data.copy().iteritems():
            if k.find(ID_INSERT) == 0:
                tabla, campos, pkey = v
                dic_campos = dict()
                for nombre, tipo, longitud in self.db.get_campos(tabla[3:]):
                    dic_campos[nombre] = [[nombre, tipo, longitud], None]

                for campo, defecto in campos:
                    nombre, tipo, longitud = campo
                    if nombre in dic_campos:
                        dic_campos[nombre] = [campo, defecto]

                campos = list()
                for c in dic_campos.values():
                    campos.append(c)

                self.data[k] = [tabla, campos, pkey]

        self.carga_destino()
        root = self.tree_des_cam.GetRootItem()
        if root:
            util.tree_expand_item(self.tree_des_cam, root)

    def on_notas_tabla(self, event):
        item = self.tree_des_cam.GetSelection()
        if item.IsOk():
            key = self.tree_des_cam.GetPyData(item).split(":")
            for k, v in self.data.iteritems():
                if k.find(ID_INSERT) == 0 and v[0] == key[1]:
                    tabla = v[0]
                    if NOTAS_TABLA not in self.data:
                        self.data[NOTAS_TABLA] = dict()
                    notas = self.data[NOTAS_TABLA][tabla] if tabla in self.data[NOTAS_TABLA] else ""
                    dlg = DlgNotas(self, wx.ID_ANY, "Notas", notas)
                    dlg.CenterOnParent()
                    val = dlg.ShowModal()
                    if val == wx.ID_OK:
                        notas = dlg.get_data()
                        self.data[NOTAS_TABLA][tabla] = notas
                    dlg.Destroy()
                    break

    def on_condicion_tabla(self, event):
        item = self.tree_des_cam.GetSelection()
        if item.IsOk():
            key = self.tree_des_cam.GetPyData(item).split(":")
            for k, v in self.data.iteritems():
                if k.find(ID_INSERT) == 0 and v[0] == key[1]:
                    tabla = v[0]
                    if CONDICION_TABLA not in self.data:
                        self.data[CONDICION_TABLA] = dict()
                    valor = self.data[CONDICION_TABLA][tabla] if tabla in self.data[CONDICION_TABLA] else ""
                    dlg = DlgCondicion(self, wx.ID_ANY, u"Condición", valor)
                    while True:
                        dlg.CenterOnParent()
                        val = dlg.ShowModal()
                        if val == wx.ID_OK:
                            valor = dlg.get_data()
                            if valor:
                                err = codigo.check_funcion(valor["condicion"], self.db)
                                if err:
                                    wx.MessageBox(err, APLICACION, wx.ICON_ERROR, self)
                                    continue
                                self.tree_des_cam.SetItemImage(item, self.idxlibrov, wx.TreeItemIcon_Normal)
                                self.data[CONDICION_TABLA][tabla] = valor
                            else:
                                self.tree_des_cam.SetItemImage(item, self.idxlibroa, wx.TreeItemIcon_Normal)
                                if tabla in self.data[CONDICION_TABLA]:
                                    del self.data[CONDICION_TABLA][tabla]
                        break
                    dlg.Destroy()
                    break

    def on_elimina_condicion_tabla(self, event):
        item = self.tree_des_cam.GetSelection()
        if item.IsOk():
            key = self.tree_des_cam.GetPyData(item).split(":")
            del self.data[CONDICION_TABLA][key[1]]
            self.tree_des_cam.SetItemImage(item, self.idxlibroa, wx.TreeItemIcon_Normal)

    def on_copiar_tabla(self, event):
        item = self.tree_des_cam.GetSelection()
        if item.IsOk():
            key = self.tree_des_cam.GetPyData(item).split(":")
            for k, v in self.data.iteritems():
                if k.find(ID_INSERT) == 0 and v[0] == key[1]:
                    clipdata = wx.TextDataObject()
                    clipdata.SetText(json.dumps({k: v}, indent=4, sort_keys=True))
                    wx.TheClipboard.Open()
                    wx.TheClipboard.SetData(clipdata)
                    wx.TheClipboard.Close()

    def on_pegar_tabla(self, event):
        tabla, campos, ids = self.clipboard_get_tabla()
        tabla = tabla[3:]

        tabla = self.n_registros_tabla(tabla)

        n = self.n_registros(ID_INSERT)
        self.data["%s%s" % (ID_INSERT, n)] = [tabla, campos, ids]

        self.carga_origen()
        util.tree_expand_item(self.tree_org, util.tree_get_item_text(self.tree_org, ID_INSERT))
        item = util.tree_get_item_text(self.tree_org, ID_INSERT)
        self.tree_org.SelectItem(item)

        self.carga_destino()
        util.tree_expand_item(self.tree_des_cam, util.tree_get_item_text(self.tree_des_cam, tabla))
        item = util.tree_get_item_text(self.tree_des_cam, tabla)
        self.tree_des_cam.SelectItem(item)

    @staticmethod
    def clipboard_get_tabla():
        try:
            if not wx.TheClipboard.IsOpened():
                do = wx.TextDataObject()
                wx.TheClipboard.Open()
                success = wx.TheClipboard.GetData(do)
                wx.TheClipboard.Close()
                if success:
                    txt = do.GetText()
                    tmp = json.loads(txt)
                    for k, v in tmp.iteritems():
                        if k.find(ID_INSERT) == 0:
                            return v[0], v[1], v[2]
        except:
            pass
        return None, None, None

    def on_refresh_db(self, event):
        host = self.text_host.Value
        puerto = self.spin_puerto.Value
        usuario = self.text_usuario.Value
        clave = self.text_clave.Value
        database = self.cb_database.GetValue()

        self.carga_tablas(host, puerto, usuario, clave, database)

    def on_dclick_db(self, event):
        pt = event.GetPosition()
        item, flags = self.tree_des.HitTest(pt)
        if not item.IsOk():
            return

        if item and item != self.tree_des.GetRootItem():
            self.pon_reloj()
            busy = wx.BusyInfo("Cargando...", self)
            wx.Yield()
            tabla = self.tree_des.GetItemText(item)
            campos = []
            for c in self.db.get_campos(tabla):
                campos.append([c, None])

            pkey = []
            for k in self.db.get_primary_key(tabla):
                pkey.append(k[0])

            tabla = self.n_registros_tabla(tabla)

            n = self.n_registros(ID_INSERT)
            self.data["%s%s" % (ID_INSERT, n)] = [tabla, campos, pkey]

            self.carga_origen()
            util.tree_expand_item(self.tree_org, util.tree_get_item_text(self.tree_org, ID_INSERT))
            item = util.tree_get_item_text(self.tree_org, ID_INSERT)
            self.tree_org.SelectItem(item)

            self.carga_destino()
            util.tree_expand_item(self.tree_des_cam, util.tree_get_item_text(self.tree_des_cam, tabla))
            item = util.tree_get_item_text(self.tree_des_cam, tabla)
            self.tree_des_cam.SelectItem(item)
            del busy
            self.quita_reloj()

    def on_keydown_db(self, event):
        self.tree2clipboard(event, self.tree_des)
        event.Skip(True)

    def on_cb_database(self, event):
        self.data = self.get_data()
        self.on_refresh_db(event)

    def on_txt_notas(self, event):
        self.data[NOTAS] = self.txt_notas.Value

    def on_btn_csv_fic(self, event):
        data = self.get_data()
        fichero = data[FICHERO_CSV]["fichero"]
        fichero = dialogo_abrir_fic(self, "Archivos csv (*.csv)|*.csv|Todos los archivos (*.*)|*", fichero)
        if fichero:
            self.text_fichero_csv.Value = fichero[0]
            delimitador = data[FICHERO_CSV]["delimitador"]
            nombres1 = data[FICHERO_CSV]["nombres1"]
            lineas = self.data[FICHERO_CSV]["lineas"]
            encode = self.data[FICHERO_CSV]["encode"]
            self.carga_fichero_csv(fichero[0], delimitador, nombres1, lineas, encode)

    def on_btn_conectar(self, event):
        data = self.get_data()
        host = data[CONEXION]["host"]
        puerto = data[CONEXION]["puerto"]
        usuario = data[CONEXION]["usuario"]
        clave = data[CONEXION]["clave"]
        database = data[CONEXION]["database"].strip()

        carga = self.carga_databases(host, puerto, usuario, clave, database)
        wx.Yield()

        if not database and self.cb_database.Count > 0:
            database = self.cb_database.GetItems()[0]
            self.cb_database.SetValue(database)
            self.data[CONEXION]["database"] = database

        if carga:
            wx.Yield()
            self.carga_tablas(host, puerto, usuario, clave, database)

    def on_col_end_drag(self, event):
        nombre = "csv"
        if FICHERO_CSV in self.data and "fichero" in self.data[FICHERO_CSV]:
            nombre = os.path.basename(self.data[FICHERO_CSV]["fichero"])
            nombre, extension = os.path.splitext(nombre)
        self.list_csv.set_propi_columns(nombre)

    def on_list_csv_col_right_click(self, event):
        if not hasattr(self, "camposdefID1"):
            self.camposdefID1 = wx.NewId()
            self.camposdefID2 = wx.NewId()
            self.camposdefID3 = wx.NewId()
            self.camposdefID4 = wx.NewId()
            self.camposdefID5 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_list_csv_add_campo, id=self.camposdefID1)
            self.Bind(wx.EVT_MENU, self.on_list_csv_editar_campo, id=self.camposdefID2)
            self.Bind(wx.EVT_MENU, self.on_list_csv_borrar_campo, id=self.camposdefID3)
            self.Bind(wx.EVT_MENU, self.on_list_csv_exportar, id=self.camposdefID4)
            self.Bind(wx.EVT_MENU, self.on_list_csv_filtros, id=self.camposdefID5)

        self.list_csv_campo_select = None

        try:
            # si marca fuera de las columnas da error
            item = self.list_csv.GetColumn(self.list_csv.col)

            if item.GetText() >= 2:
                self.list_csv_campo_select = item.GetText()[1:-1]  # sin parentesis
        except:
            return

        menu = wx.Menu()
        item1 = wx.MenuItem(menu, self.camposdefID1, u"Añadir campo")
        item2 = wx.MenuItem(menu, self.camposdefID2, "Editar campo")
        item3 = wx.MenuItem(menu, self.camposdefID3, "Borrar campo")
        item4 = wx.MenuItem(menu, self.camposdefID4, "Exportar csv")
        item5 = wx.MenuItem(menu, self.camposdefID5, "Filtros")
        menu.AppendItem(item1)
        menu.AppendItem(item2)
        menu.AppendItem(item3)
        menu.AppendSeparator()
        menu.AppendItem(item5)
        menu.AppendSeparator()
        menu.AppendItem(item4)

        item2.Enable(False)
        item3.Enable(False)
        for k, v in self.data.iteritems():
            if k.find(CAMPO_DEF) == 0:
                if self.list_csv_campo_select in v.values():
                    item2.Enable(True)
                    item3.Enable(True)
                    break
        if self.list_csv.GetColumnCount() <= 0:
            item4.Enable(False)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_list_csv_add_campo(self, event):
        self.dialogo_campo_def()

    def on_list_csv_filtros(self, event):
        dlg = Filtros(self, wx.ID_ANY, u"Asignación de filtros a campos", self.data)
        dlg.CenterOnParent()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self.data[FILTROS], self.data[CAMPO_FILTROS] = dlg.get_data()
        dlg.Destroy()

    def on_list_csv_editar_campo(self, event):
        for k, v in self.data.iteritems():
            if k.find(CAMPO_DEF) == 0:
                if self.list_csv_campo_select in v.values():
                    self.dialogo_campo_def(v, k)
                    break

    def on_list_csv_borrar_campo(self, event):
        for k, v in self.data.iteritems():
            if k.find(CAMPO_DEF) == 0:
                if self.list_csv_campo_select in v.values():
                    txt = '¿Desea borrar el campo: "%s"?' % v['nombre']
                    dlg1 = wx.MessageDialog(self, txt, 'Borrar campo', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                    if dlg1.ShowModal() == wx.ID_YES:
                        del self.data[k]
                        break
                    else:
                        return
        self.get_data()
        fichero = self.data[FICHERO_CSV]["fichero"]
        delimitador = self.data[FICHERO_CSV]["delimitador"]
        nombres1 = self.data[FICHERO_CSV]["nombres1"]
        lineas = self.data[FICHERO_CSV]["lineas"]
        encode = self.data[FICHERO_CSV]["encode"]
        self.carga_fichero_csv(fichero, delimitador, nombres1, lineas, encode)

    def on_list_csv_exportar(self, event):
        pgi = Pgi(self.data)
        campos = pgi.get_campos_csv()
        seleccionados = pgi.get_campos_csv_usados()
        dlg = DlgExportaCSV(self, wx.ID_ANY, u"Selección de campos a exportar", campos, sorted(seleccionados))
        dlg.CenterOnParent()
        dlg.ShowModal()
        if dlg.data and dlg.data["ok"] and dlg.data["campos"] and dlg.data["fichero"]:
            self.exporta_csv(dlg.data["fichero"], dlg.data["campos"], dlg.data["nombres1"])
        dlg.Destroy()

    def on_menu_open(self, event):
        activo = True
        self.menu_bar.Enable(self.menu_id5, activo)

    def on_nuevo(self, event):
        self.fichero_pgi = ""
        self.data = dict()
        self.text_fichero_csv.Clear()
        self.cb_database.SetItems([""])
        self.list_csv.DeleteAllItems()
        self.list_csv.DeleteAllColumns()
        self.tree_des.DeleteAllItems()
        self.carga_origen()
        self.carga_destino()
        self.db.close()
        self.SetTitle("%s (%s)" % (APLICACION, "..."))
        self.txt_notas.SetValue("")

    def on_abrir(self, event):
        fichero = dialogo_abrir_fic(self, "Archivos pgi (*.pgi)|*.pgi|Todos los archivos (*.*)|*", self.fichero_pgi)
        if fichero:
            self.abrir(fichero[0])

    def on_grabar(self, event):
        if self.fichero_pgi:
            self.grabar(self.fichero_pgi)
        else:
            f = dialogo_grabar_fic(self, "pgi", "Archivos pgi (*.pgi)|*.pgi|Todos los archivos (*.*)|*", "")
            if f:
                self.grabar(f)

    def on_grabar_como(self, event):
        f = dialogo_grabar_fic(self, "pgi", "Archivos pgi (*.pgi)|*.pgi|Todos los archivos (*.*)|*", self.fichero_pgi)
        if f:
            self.grabar(f)

    def on_importar(self, event):
        try:
            fichero = self.data[FICHERO_CSV]["fichero"]
            if not fichero:
                wx.MessageBox("Debe de informar el fichero csv.", APLICACION, wx.ICON_ERROR)
                return
            maximo = open(fichero).read().count('\n')
        except KeyError, e:
            return
        except IOError, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)
            return

        dlg = DlgImportar(None, title='Importar')
        dlg.ShowModal()
        modo, log, sql = dlg.get_data()
        dlg.Destroy()

        if modo == "probar":
            commit = False
            titulo = u"Probando importación de datos"
        elif modo == "importar":
            commit = True
            titulo = "Importando datos"
        else:
            return

        dlg = wx.ProgressDialog(titulo, titulo, maximum=maximo, parent=self,
                                style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME |
                                wx.PD_ESTIMATED_TIME| wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)

        dlg.SetIcon(imagenes.importar.GetIcon())

        def actualiza(dlg, contador, mensaje=None):
            #wx.MilliSleep(250)
            if contador % 100: wx.Yield()
            if mensaje:
                return dlg.Update(contador, mensaje)
            else:
                return dlg.Update(contador)

        tmp_log = util.ahora()
        tmp_sql = tmp_log + 1
        tmp_log = os.path.join(tempfile.gettempdir(), "%d.txt" % tmp_log)
        tmp_sql = os.path.join(tempfile.gettempdir(), "%d.txt" % tmp_sql)

        imp = Importa(tmp_log, tmp_sql, log, sql)
        imp.ejecuta(self.data, commit, actualiza, dlg, maximo)
        if imp.error:
            wx.MessageBox(imp.error, APLICACION, wx.ICON_ERROR)
            dlg.Destroy()
        else:
            dlg.Update(maximo)
            dlg.Destroy()

        dlg = wx.MessageDialog(self, u"¿ Mostrar log de las tablas afectadas ?", u"Importación finalizada", wx.YES_NO | wx.ICON_QUESTION)
        resul = dlg.ShowModal() == wx.ID_YES
        dlg.Destroy()
        if resul:
            webbrowser.open(tmp_log, new=0, autoraise=True)

        if sql:
            dlg = wx.MessageDialog(self, u"¿ Mostrar sql realizadas ?", u"Importación finalizada", wx.YES_NO | wx.ICON_QUESTION)
            resul = dlg.ShowModal() == wx.ID_YES
            dlg.Destroy()
            if resul:
                webbrowser.open(tmp_sql, new=0, autoraise=True)

    def on_sql(self, event):
        self.pon_reloj()
        item = self.tree_des_item
        sql = ""
        if item and item != self.tree_des.GetRootItem():
            tabla = self.tree_des.GetPyData(item)
            if tabla:
                tabla = tabla.split(":")[1]
                orden = ""
                ind = []
                for k in self.db.get_primary_key(tabla):
                    ind.append('"%s"' % k[0])

                if ind:
                    orden = "ORDER BY %s" % ",".join(ind)

                sql = "SELECT * FROM %s %s LIMIT 100" % (tabla, orden)

        frm = FrmSql(self, wx.ID_ANY, sql)
        frm.CenterOnParent()
        frm.Show()
        frm.SetFocus()
        self.quita_reloj()

    def frm_sql_size(self, ancho, alto):
        self.frm_sql_ancho = ancho
        self.frm_sql_alto = alto

    def frm_compara_size(self, ancho, alto):
        self.frm_compara_ancho = ancho
        self.frm_compara_alto = alto

    def on_salir(self, event):
        self.db.close()
        self.Close()

    def on_grabar_db(self, event):
        if not self.db.esta_conectada:
            return

        dlg = DlgLisTablas(self, wx.ID_ANY, u"Selección de tablas a grabar", self.db, self.dlg_grabar_db_datos)
        dlg.CenterOnParent()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self.dlg_grabar_db_datos = dlg.get_data()
        dlg.Destroy()

        if val == wx.ID_OK:
            fichero = self.dlg_grabar_db_datos["fichero"]
            tablas = self.dlg_grabar_db_datos["tablas"]
            if tablas and fichero:
                self.grabar_db(self.db, tablas, fichero)
            else:
                if not fichero and tablas:
                    wx.MessageBox("No ha informado el fichero destino. Cancelado...", APLICACION, wx.ICON_ERROR, self)
                if not tablas:
                    wx.MessageBox("No ha marcardo ninguna tabla. Cancelado...", APLICACION, wx.ICON_ERROR, self)

    def on_comparar_db(self, event):
        if not self.db.esta_conectada:
            return

        fichero = dialogo_abrir_fic(self, "Archivos pgz (*.pgz)|*.pgz|Todos los archivos (*.*)|*")
        if fichero:
            self.comparar_db(self.db, fichero[0])

    def on_acerca(self, event):
        info = wx.AboutDialogInfo()
        info.Name = APLICACION
        info.Version = NVERSION
        info.Copyright = COPYRIGHT
        info.Description = wordwrap("\n" + DESCRIPCION + "\nCreado: " + CREADO +\
                                    "\nÚltima modificación: " + ULT_MODI +\
                                    "\n\n(" + self.app.fic_config + ")\n", 350, wx.ClientDC(self))
        info.WebSite = (URL_COMPANY, NOM_COMPANY)
        info.Developers = [AUTOR]
        info.License = wordwrap(LICENCIA, 500, wx.ClientDC(self))
        wx.AboutBox(info)

    def on_ayuda(self, event):
        fic = os.path.join(util.module_path(), "ejemplos", "pgimporta.pdf")
        webbrowser.open(fic)

    def on_close_window(self, event):
        self.app.set_propiedad("Datos", self.data)
        self.app.set_propiedad("DlgGrabarDB", self.dlg_grabar_db_datos)
        event.Skip(True)

    def on_size(self, event):
        valor = self.GetSizeTuple()
        if valor[0] < 200 or valor[1] < 200:
            return

        self.set_propi_size()
        event.Skip(True)

    @staticmethod
    def tree2clipboard(event, tree):
        key = event.KeyCode
        if event.ControlDown() and key in (ord('C'), ord('C')):
            item = tree.GetSelection()
            if item.IsOk():
                data = tree.GetItemText(item).strip()
                clipdata = wx.TextDataObject()
                clipdata.SetText(data)
                wx.TheClipboard.Open()
                wx.TheClipboard.SetData(clipdata)
                wx.TheClipboard.Close()

    def carga_databases(self, host, puerto, usuario, clave, database=""):
        self.pon_reloj()
        if self.db.conecta(host, puerto, usuario, clave):
            self.cb_database.SetItems(self.db.databases)
            self.cb_database.SetStringSelection(database)
            self.quita_reloj()
            self.infobar_db.Dismiss()
            return True
        else:
            self.quita_reloj()
            #wx.MessageBox(self.db.error, APLICACION, wx.ICON_ERROR)
            self.infobar_db.ShowMessage(self.db.error, wx.ICON_ERROR)
            return False

    def carga_tablas0(self, tablas, filtro=None):
        font = self.tree_des.GetFont()
        # Por el bug de windows
        if not util.is_windows or util.bits == 64:
            font.SetWeight(wx.BOLD)

        self.tree_des.Freeze()
        self.tree_des.DeleteAllItems()
        root = self.tree_des.AddRoot("DB " + self.db.database)
        self.tree_des.SetPyData(root, "0:root")
        self.tree_des.SetItemFont(root, font)

        self.tree_des.SetItemImage(root, self.idxlibro, wx.TreeItemIcon_Normal)

        for t, primary in tablas:
            if filtro and filtro.lower() not in t.lower():
                continue
            hijo = self.tree_des.AppendItem(root, t)
            self.tree_des.SetItemImage(hijo, self.idxlibrok, wx.TreeItemIcon_Normal)
            self.tree_des.SetPyData(hijo, "1:%s" % t)

        self.tree_des.Thaw()
        return root

    def carga_tablas(self, host, puerto, usuario, clave, database):
        self.pon_reloj()
        if self.db.conecta(host, puerto, usuario, clave, database):
            self.buffer_tablas = self.db.get_tablas_y_primary_key()
            root = self.carga_tablas0(self.buffer_tablas)
            self.tree_des.Expand(root)
            self.quita_reloj()
            self.infobar_db.Dismiss()
        else:
            self.quita_reloj()
            #wx.MessageBox(self.db.error, APLICACION, wx.ICON_ERROR)
            self.infobar_db.ShowMessage(self.db.error, wx.ICON_ERROR)

    def carga_origen(self, filtro=None):
        font = self.tree_org.GetFont()
        #Por el bug de windows
        if not util.is_windows or util.bits == 64:
            font.SetWeight(wx.BOLD)
        self.tree_org.Freeze()
        self.tree_org.DeleteAllItems()
        if self.data:
            def carga(tipo):
                item = None
                for k, v in sorted(self.data.iteritems()):
                    if k.find(tipo) == 0:
                        if tipo == FICHERO_CSV and not v["campos"]:
                            continue

                        if not item:
                            root = self.tree_org.GetRootItem()
                            if not root:
                                root = self.tree_org.AddRoot("Origen")
                                self.tree_org.SetPyData(root, "0:root")
                                self.tree_org.SetItemFont(root, font)
                                self.tree_org.SetItemImage(root, self.idxproc, wx.TreeItemIcon_Normal)

                            item = self.tree_org.AppendItem(root, tipo)
                            key = "1:%s" % tipo
                            self.tree_org.SetPyData(item, key)
                            self.tree_org.SetItemImage(item, self.idxmis, wx.TreeItemIcon_Normal)
                            self.tree_org.SetItemFont(item, font)

                        if tipo == CODIGO_INICIAL or tipo == CODIGO_FINAL:
                            nombre = v["nombre"]
                            valor = v["valor"].replace("\n", " ")

                            if filtro and filtro.lower() not in nombre.lower():
                                continue

                            asignado = None # self.get_campo_asignado_destino("@%s" % nombre)[1]
                            if asignado:
                                hijo = self.tree_org.AppendItem(item, "%s (%s) " % (nombre, asignado))
                            else:
                                hijo = self.tree_org.AppendItem(item, nombre)
                            key = "2:%s:%s" % (tipo, nombre)
                            self.tree_org.SetPyData(hijo, key)
                            self.tree_org.SetItemImage(hijo, self.idxpython, wx.TreeItemIcon_Normal)
                            # self.tree_org.SetItemImage(hijo, self.idxmarca, wx.TreeItemIcon_Selected)
                            # hijo1 = self.tree_org.AppendItem(hijo, valor)
                            # self.tree_org.SetItemImage(hijo1, self.idxpython, wx.TreeItemIcon_Normal)

                        elif tipo == VALOR_FIJO:
                            nombre = v["nombre"]
                            valor = v["valor"]

                            if filtro and filtro.lower() not in nombre.lower():
                                continue

                            asignado = None # self.get_campo_asignado_destino("@%s" % nombre)[1]
                            if asignado:
                                hijo = self.tree_org.AppendItem(item, "%s (%s) " % (nombre, asignado))
                            else:
                                hijo = self.tree_org.AppendItem(item, nombre)
                            key = "2:%s:%s" % (tipo, nombre)
                            self.tree_org.SetPyData(hijo, key)
                            self.tree_org.SetItemImage(hijo, self.idxcam, wx.TreeItemIcon_Normal)
                            self.tree_org.SetItemImage(hijo, self.idxmarca, wx.TreeItemIcon_Selected)
                            hijo1 = self.tree_org.AppendItem(hijo, valor)
                            self.tree_org.SetItemImage(hijo1, self.idxpropi, wx.TreeItemIcon_Normal)

                        elif tipo == SQL_INI or tipo == SQL_REG:
                            sql = v["sql"]
                            campos = v["campos"]
                            nombre = v["nombre"]

                            if filtro and filtro.lower() not in nombre.lower():
                                continue

                            item1 = self.tree_org.AppendItem(item, nombre)
                            key = "2:%s:%s:%s" % (tipo, nombre, sql)
                            self.tree_org.SetPyData(item1, key)
                            self.tree_org.SetItemImage(item1, self.idxsql, wx.TreeItemIcon_Normal)
                            for k1, v1 in sorted(campos.iteritems()):
                                hijo = self.tree_org.AppendItem(item1, k1)
                                key = "3:%s:%s:%s.%s" % (tipo, nombre, nombre, k1)
                                self.tree_org.SetPyData(hijo, key)
                                self.tree_org.SetItemImage(hijo, self.idxcam, wx.TreeItemIcon_Normal)
                                self.tree_org.SetItemImage(hijo, self.idxmarca, wx.TreeItemIcon_Selected)
                                hijo1 = self.tree_org.AppendItem(hijo, v1)
                                self.tree_org.SetItemImage(hijo1, self.idxpropi, wx.TreeItemIcon_Normal)

                        elif tipo == CAMPO_REG:
                            nombre = v["nombre"]
                            valor = v["valor"].replace("\n", " ")

                            if filtro and filtro.lower() not in nombre.lower():
                                continue

                            asignado = None # self.get_campo_asignado_destino("@%s" % nombre)[1]
                            if asignado:
                                hijo = self.tree_org.AppendItem(item, "%s (%s) " % (nombre, asignado))
                            else:
                                hijo = self.tree_org.AppendItem(item, nombre)
                            key = "2:%s:%s" % (tipo, nombre)
                            self.tree_org.SetPyData(hijo, key)
                            self.tree_org.SetItemImage(hijo, self.idxpython, wx.TreeItemIcon_Normal)
                            self.tree_org.SetItemImage(hijo, self.idxmarca, wx.TreeItemIcon_Selected)
                            # hijo1 = self.tree_org.AppendItem(hijo, valor)
                            # self.tree_org.SetItemImage(hijo1, self.idxpython, wx.TreeItemIcon_Normal)

                        elif tipo == FICHERO_CSV:
                            campos = v["campos"]
                            for c in campos:
                                if filtro and filtro.lower() not in c.lower():
                                    continue

                                asignado = self.get_campo_asignado_destino("@csv.%s" % c)[0]
                                if asignado:
                                    hijo = self.tree_org.AppendItem(item, "%s (%s)" % (c, asignado) )
                                    self.tree_org.SetItemImage(hijo, self.idxasig, wx.TreeItemIcon_Normal)
                                else:
                                    hijo = self.tree_org.AppendItem(item, c)
                                    self.tree_org.SetItemImage(hijo, self.idxcam, wx.TreeItemIcon_Normal)

                                key = "2:%s:csv.%s" % (tipo, c)
                                self.tree_org.SetPyData(hijo, key)
                                self.tree_org.SetItemImage(hijo, self.idxmarca, wx.TreeItemIcon_Selected)

                            for k1, v1 in sorted(self.data.iteritems()):
                                if k1.find(CAMPO_DEF) == 0:
                                    c = v1["nombre"]
                                    if filtro and filtro.lower() not in c.lower():
                                        continue

                                    asignado = self.get_campo_asignado_destino("@csv.%s" % c)[0]
                                    if asignado:
                                        hijo = self.tree_org.AppendItem(item, "%s (%s)" % (c, asignado) )
                                        self.tree_org.SetItemImage(hijo, self.idxasig, wx.TreeItemIcon_Normal)
                                    else:
                                        hijo = self.tree_org.AppendItem(item, c)
                                        self.tree_org.SetItemImage(hijo, self.idxcam, wx.TreeItemIcon_Normal)

                                    key = "2:%s:csv.%s" % (tipo, c)
                                    self.tree_org.SetPyData(hijo, key)
                                    self.tree_org.SetItemImage(hijo, self.idxmarca, wx.TreeItemIcon_Selected)

                        elif tipo == ID_INSERT:
                            tabla = v[0]

                            if filtro and filtro.lower() not in tabla.lower():
                                continue

                            campos = v[1]
                            pkey = v[2]
                            if pkey:
                                hijo = self.tree_org.AppendItem(item, tabla)
                                key = "2:%s:%s.%s" % (tipo, tabla, ",".join(pkey))
                                self.tree_org.SetPyData(hijo, key)
                                self.tree_org.SetItemImage(hijo, self.idxkey, wx.TreeItemIcon_Normal)
                                self.tree_org.SetItemImage(hijo, self.idxmarca, wx.TreeItemIcon_Selected)
                                self.tree_org.SetItemImage(hijo, self.idxmarca, wx.TreeItemIcon_Expanded)
            carga(CODIGO_INICIAL)
            carga(VALOR_FIJO)
            carga(SQL_INI)
            carga(FICHERO_CSV)
            carga(SQL_REG)
            carga(CAMPO_REG)
            carga(ID_INSERT)
            carga(CODIGO_FINAL)
        self.tree_org.Thaw()

    def get_campo_asignado_destino(self, campo):
        valor = ""
        cuantos = 0
        for k, v in self.data.iteritems():
            if k.find(ID_INSERT) == 0:
                tabla = v[0]
                campos = v[1]
                for c in campos:
                    cam_tabla = c[0][0]
                    cam_origen = c[1]
                    if cam_origen == campo:
                        cuantos += 1
                        if valor:
                            valor += ", %s.%s" % (tabla, cam_tabla)
                        else:
                            valor = "%s.%s" % (tabla, cam_tabla)
        return valor, cuantos

    def carga_destino0(self, tabla_campos, filtro=None):
        font = self.tree_des_cam.GetFont()
        #Por el bug de windows
        if not util.is_windows or util.bits == 64:
            font.SetWeight(wx.BOLD)
        self.tree_des_cam.Freeze()
        self.tree_des_cam.DeleteAllItems()
        for k, v in sorted(self.data.iteritems()):
            if k.find(ID_INSERT) == 0:
                tabla = v[0]
                campos = v[1]
                root = self.tree_des_cam.GetRootItem()
                if not root:
                    root = self.tree_des_cam.AddRoot("Destino")
                    self.tree_des_cam.SetPyData(root, "0:root")
                    self.tree_des_cam.SetItemFont(root, font)
                    self.tree_des_cam.SetItemImage(root, self.idxproc, wx.TreeItemIcon_Normal)

                pkey = self.buffer_campos[tabla]

                hijo = self.tree_des_cam.AppendItem(root, tabla)

                if CONDICION_TABLA in self.data and tabla in self.data[CONDICION_TABLA]:
                    self.tree_des_cam.SetItemImage(hijo, self.idxlibrov, wx.TreeItemIcon_Normal)
                    self.tree_des_cam.SetPyData(hijo, "1:%s" % tabla)
                else:
                    if not pkey:
                        self.tree_des_cam.SetItemImage(hijo, self.idxlibroa, wx.TreeItemIcon_Normal)
                        self.tree_des_cam.SetPyData(hijo, "1:%s" % tabla)
                    elif len(pkey) == 1:
                        self.tree_des_cam.SetItemImage(hijo, self.idxlibrok, wx.TreeItemIcon_Normal)
                        self.tree_des.SetPyData(hijo, "1:%s:%s" % (tabla, ":".join(pkey)))
                    else:
                        self.tree_des_cam.SetItemImage(hijo, self.idxlibrok2, wx.TreeItemIcon_Normal)
                        self.tree_des.SetPyData(hijo, "1:%s:%s" % (tabla, ":".join(pkey)))

                self.tree_des_cam.SetItemFont(hijo, font)
                for c in sorted(campos):

                    if c[1]:
                        if filtro and (filtro.lower() not in c[0][0].lower()) and (filtro.lower() not in c[1].lower()) :
                            continue
                        hijo1 = self.tree_des_cam.AppendItem(hijo, "%s = %s" % (c[0][0], c[1]))
                        self.tree_des_cam.SetItemImage(hijo1, self.idxasig, wx.TreeItemIcon_Normal)
                    else:
                        if filtro and filtro.lower() not in c[0][0].lower():
                            continue
                        hijo1 = self.tree_des_cam.AppendItem(hijo, c[0][0])
                        if c[0][0] in pkey:
                            self.tree_des_cam.SetItemImage(hijo1, self.idxkey, wx.TreeItemIcon_Normal)
                        else:
                            self.tree_des_cam.SetItemImage(hijo1, self.idxcam, wx.TreeItemIcon_Normal)
                    self.tree_des_cam.SetPyData(hijo1, "2:%s:%s" % (tabla, c[0][0]))
                    self.tree_des_cam.SetItemImage(hijo1, self.idxmarca, wx.TreeItemIcon_Selected)
                    if c[0][2]:
                        hijo1 = self.tree_des_cam.AppendItem(hijo1, "%s [%s]" % (c[0][1], c[0][2]))
                    else:
                        hijo1 = self.tree_des_cam.AppendItem(hijo1, "%s" % c[0][1])
                    self.tree_des_cam.SetItemImage(hijo1, self.idxpropi, wx.TreeItemIcon_Normal)
        self.tree_des_cam.Thaw()

    def carga_destino(self):
        self.buffer_campos = dict()
        for k, v in sorted(self.data.iteritems()):
            if k.find(ID_INSERT) == 0:
                tabla = v[0]
                pkey = []
                # Comentado para mejorar la velocidad, solo vale par cambiar el icono de la tabla destino
                # for k in self.db.get_primary_key(tabla[3:]):
                #    pkey.append(k[0])
                self.buffer_campos[tabla] = pkey

        self.carga_destino0(self.buffer_campos)

    def carga_fichero_csv(self, fichero, delimitador, nombres_1linea, lineas, encode):
        if not fichero:
            return

        def ordena(obj1, obj2):
            return cmp(obj1[0], obj2[0])

        def nom_campo(campo, n):
            if campo:
                tmp = ""
                for c in campo:
                    if c not in "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                        tmp += "_"
                    else:
                        tmp += c
                if tmp[0] in "1234567890":
                    tmp = "_" + tmp
            else:
                tmp = "campo%s" % n
            return tmp.replace("__", "_")

        self.infobar_cb.Dismiss()

        self.list_csv.Freeze()
        self.list_csv.DeleteAllItems()
        self.list_csv.DeleteAllColumns()

        cam_def = []
        for k, v in self.data.iteritems():
            if k.find(CAMPO_DEF) == 0:
                cam_def.append([v["nombre"], v["valor"]])

        cam_def.sort(cmp=ordena)

        try:
            i = 0
            with open(fichero, 'rb') as f:
                n = 0
                campos = []
                for i, cam in enumerate(UnicodeReader(f, encoding=encode, delimiter=str(delimitador), quotechar='"')):
                    for n in range(0, len(cam)):
                        if nombres_1linea:
                            # columna = cam[n].replace(" ", "_").replace("\t", "").replace("'", "").replace('"', "").replace('.', "_")
                            columna = nom_campo(cam[n], n)
                            columna = columna.encode('ascii', 'ignore')
                        else:
                            columna = "campo%s" % n
                        campos.append(columna)
                        w = util.get_width_font(self.list_csv, columna) + 15
                        self.list_csv.InsertColumn(n, columna, width=w)

                    for c in cam_def:
                        w = util.get_width_font(self.list_csv, "(%s)" % c[0]) + 15
                        self.list_csv.InsertColumn(n+1, "(%s)" % c[0], width=w)
                        n += 1

                    break
                self.data[FICHERO_CSV]["campos"] = campos
                # añade una columna vacia
                self.list_csv.InsertColumn(n + 1, "", width=30)

            if cam_def:
                funciones, err = codigo.crea_modulo(cam_def, self.data[FICHERO_CSV])
                if err:
                    raise Exception(err)

            with open(fichero, 'rb') as f:
                lon = ind = 0
                for i, cam in enumerate(UnicodeReader(f, encoding=encode, delimiter=str(delimitador), quotechar='"')):
                    if ind >= lineas:
                        break

                    if i == 0:
                        lon = len(cam)
                        if nombres_1linea:
                            continue

                    if not len(cam):
                        continue

                    for n in range(0, lon):
                        if n == 0:
                            self.list_csv.InsertStringItem(ind, cam[n])
                        else:
                            self.list_csv.SetStringItem(ind, n, cam[n])

                    for c in cam_def:
                        try:
                            valor = funciones[c[0]](cam)
                        except:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            valor = 'ERROR=>%s:%s' % (exc_type.__name__, exc_value)

                        if type(valor) != unicode:
                            valor = str(valor)

                        self.list_csv.SetStringItem(ind, n+1, valor)
                        n += 1
                    if lon > 0:
                        self.list_csv.set_color_row(ind)
                    ind += 1

            nombre = "csv"
            if fichero:
                nombre = os.path.basename(fichero)
                nombre, extension = os.path.splitext(nombre)
            self.list_csv.set_size_columns(nombre)

            self.data[FICHERO_CSV]["fichero"] = fichero
            self.carga_origen()
          #  util.tree_expand_item(self.tree_org, util.tree_get_item_text(self.tree_org, FICHERO_CSV))
          #  item = util.tree_get_item_text(self.tree_org, FICHERO_CSV)
          #  self.tree_org.SelectItem(item)
            root = self.tree_org.GetRootItem()
            util.tree_expand_item(self.tree_org, root)

            self.encode_anterior = encode

        except IOError, e:
            self.infobar_cb.ShowMessage(str(e), wx.ICON_ERROR)

        except TypeError, e:
            self.infobar_cb.ShowMessage(str(e), wx.ICON_ERROR)

        except UnicodeDecodeError, e:
            self.infobar_cb.ShowMessage(str(e), wx.ICON_ERROR)

        except IndexError, e:
            self.infobar_cb.ShowMessage("[%s] %s" % (i, str(e)), wx.ICON_ERROR)

        except Exception, e:
            self.infobar_cb.ShowMessage("[%s] %s" % (i, str(e)), wx.ICON_ERROR)

        finally:
            self.list_csv.Thaw()

    def crea_panel_destino(self, win):
        splitter = BaseSplitter(win, "destino")

        p1 = wx.Panel(splitter, style=wx.BORDER_THEME)
        tree_izq = wx.TreeCtrl(p1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HAS_BUTTONS)
        tree_izq.SetImageList(self.imglst)
        filter_izq = wx.SearchCtrl(p1, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
       # filter_izq.SetDescriptiveText("Buscar tabla")  lo quito, no sale el texto en negrita
        filter_izq.ShowCancelButton(True)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(tree_izq, 1, wx.EXPAND)
        box.Add(filter_izq, 0, wx.EXPAND)
        p1.SetSizer(box)

        p2 = wx.Panel(splitter, style=wx.BORDER_THEME)
        bmp = imagenes.flechaup.GetBitmap()
        btn1 = buttons.GenBitmapButton(p2, wx.ID_ANY, bmp, size=(26, 26))
        bmp = imagenes.flechadown.GetBitmap()
        btn2 = buttons.GenBitmapButton(p2, wx.ID_ANY, bmp, size=(26, 26))
        bmp = imagenes.refrescar.GetBitmap()
        btn3 = buttons.GenBitmapButton(p2, wx.ID_ANY, bmp, size=(26, 26))
        btn3.SetToolTipString(u"Refrescar campos según la BD actual")

        boxh = wx.BoxSizer(wx.HORIZONTAL)
        boxh.Add(btn1, 0, wx.ALL)
        boxh.Add(btn2, 0, wx.ALL)
        boxh.Add((10, 10), wx.ALL)
        boxh.Add(btn3, 0, wx.ALL)

        box = wx.BoxSizer(wx.VERTICAL)
        tree_der = wx.TreeCtrl(p2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HAS_BUTTONS)
        tree_der.SetImageList(self.imglst)
        filter_der = wx.SearchCtrl(p2, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
       # filter_der.SetDescriptiveText("Buscar campo")
        filter_der.ShowCancelButton(True)

        box.Add(boxh, 0, wx.ALL)
        box.Add(tree_der, 1, wx.EXPAND)
        box.Add(filter_der, 0, wx.EXPAND)
        p2.SetSizer(box)

        splitter.SetMinimumPaneSize(50)
        splitter.SplitVertically(p1, p2, splitter.get_size())

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(splitter, 1, wx.EXPAND)
        win.SetSizer(box)

        self.tree_des = tree_izq
        self.tree_des_cam = tree_der
        self.filtro_des = filter_izq
        self.filtro_des_cam = filter_der

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_tree_des_changed, self.tree_des)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_tree_des_cam_changed, self.tree_des_cam)
        filter_izq.Bind(wx.EVT_TEXT, self.on_filter_izq)
        filter_izq.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, lambda e: filter_izq.SetValue(''))
        filter_der.Bind(wx.EVT_TEXT, self.on_filter_der)
        filter_der.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, lambda e: filter_der.SetValue(''))

        self.tree_des.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick_db)
        self.tree_des.Bind(wx.EVT_RIGHT_DOWN, self.on_right_db)
        self.tree_des.Bind(wx.EVT_KEY_DOWN, self.on_keydown_db)
        self.tree_des_cam.Bind(wx.EVT_RIGHT_DOWN, self.on_right_des)
        self.tree_des_cam.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick_des)
        self.tree_des_cam.Bind(wx.EVT_KEY_DOWN, self.on_dkey_des)
        self.tree_des_cam.Bind(wx.EVT_KEY_DOWN, self.on_keydown_des)
        self.tree_des_cam.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.on_collapsed_des)

        btn1.Bind(wx.EVT_BUTTON, self.on_tree_des_cam_arriba)
        btn2.Bind(wx.EVT_BUTTON, self.on_tree_des_cam_abajo)
        btn3.Bind(wx.EVT_BUTTON, self.on_tree_des_cam_refrescar)

    def on_filter_izq(self, evt):
        if not self.buffer_tablas:
            return

        self.carga_tablas0(self.buffer_tablas, self.filtro_des.GetValue())
        self.tree_des.ExpandAll()

    def on_filter_der(self, evt):
        if not self.buffer_campos:
            return

        self.carga_destino0(self.buffer_campos, self.filtro_des_cam.GetValue())
        self.tree_des_cam.CollapseAll()
        item = self.tree_des_cam.GetRootItem()
        if item:
            self.tree_des_cam.Expand(item)
            for k, v in self.data.iteritems():
                if k.find(ID_INSERT) == 0:
                    key = "1:%s" % v[0]
                    item = tree_get_item_data(self.tree_des_cam, key)
                    if item:
                        self.tree_des_cam.Expand(item)

    def crea_panel_origen(self, win):
        bmp = imagenes.flechaup.GetBitmap()
        btn1 = buttons.GenBitmapButton(win, wx.ID_ANY, bmp, size=(26, 26))
        bmp = imagenes.flechadown.GetBitmap()
        btn2 = buttons.GenBitmapButton(win, wx.ID_ANY, bmp, size=(26, 26))
        boxh = wx.BoxSizer(wx.HORIZONTAL)
        boxh.Add(btn1, 0, wx.ALL)
        boxh.Add(btn2, 0, wx.ALL)

        tree_izq = wx.TreeCtrl(win, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HAS_BUTTONS)
        tree_izq.SetImageList(self.imglst)
        filter = wx.SearchCtrl(win, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        # filter.SetDescriptiveText("Buscar nombre")
        filter.ShowCancelButton(True)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(boxh, 0, wx.ALL)
        box.Add(tree_izq, 1, wx.EXPAND)
        box.Add(filter, 0, wx.EXPAND)
        win.SetSizer(box)

        self.tree_org = tree_izq
        self.filtro_org = filter

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_tree_org_changed, self.tree_org)
        filter.Bind(wx.EVT_TEXT, self.on_filter_org)
        filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, lambda e: filter.SetValue(''))

        self.tree_org.Bind(wx.EVT_RIGHT_DOWN, self.on_right_org)
        self.tree_org.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick_org)
        self.tree_org.Bind(wx.EVT_KEY_DOWN, self.on_keydown_org)
        self.tree_org.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.on_collapsed_org)

        btn1.Bind(wx.EVT_BUTTON, self.on_tree_org_arriba)
        btn2.Bind(wx.EVT_BUTTON, self.on_tree_org_abajo)

    def on_collapsed_org(self, evt):
        item = evt.GetItem()
        util.tree_collapse(self.tree_org, item)

    def on_filter_org(self, evt):
        self.carga_origen(self.filtro_org.GetValue())
        self.tree_org.CollapseAll()
        item = self.tree_org.GetRootItem()
        if item:
            self.tree_org.Expand(item)
            for valor in [VALOR_FIJO, SQL_INI, FICHERO_CSV, SQL_REG, ID_INSERT, CAMPO_REG]:
                key = "1:%s" % valor
                item = tree_get_item_data(self.tree_org, key)
                if item:
                    self.tree_org.Expand(item)

    def crea_notebook(self, win):
        box = wx.BoxSizer(wx.VERTICAL)
        self.infobar_cb = IB.InfoBar(win)
        self.infobar_db = IB.InfoBar(win)
        self.notebook = wx.Notebook(win, wx.ID_ANY, style=wx.BK_DEFAULT)
        box.Add(self.infobar_db, 0, wx.EXPAND)
        box.Add(self.infobar_cb, 0, wx.EXPAND)
        box.Add(self.notebook, 1, wx.EXPAND)
        win.SetSizer(box)

        p1 = wx.Panel(self.notebook, wx.ID_ANY)
        self.crea_notebook_pag_conexion(p1)

        p2 = wx.Panel(self.notebook, wx.ID_ANY)
        self.crea_notebook_pag_csv(p2)

        self.notebook.AddPage(p1, u"Conexión ", True)
        self.notebook.AddPage(p2, u"CSV ", True)

        self.notebook.ChangeSelection(0)

    def crea_notebook_pag_conexion(self, win):
        gbs = wx.GridBagSizer(5, 10)

        self.text_host = wx.TextCtrl(win, value="localhost")
        self.spin_puerto = wx.SpinCtrl(win, wx.ID_ANY, "", (30, 20), size=(120, -1))
        self.spin_puerto.SetRange(1, 99999)
        self.spin_puerto.SetValue(5432)
        self.text_usuario = wx.TextCtrl(win, value="odoo", )
        self.text_clave = wx.TextCtrl(win, value="", style=wx.TE_PASSWORD)
        ancho, alto = self.text_clave.GetSize()
        btn_conectar = wx.Button(win, wx.ID_ANY, "Conectar", size=(100, alto))
        self.cb_database = wx.ComboBox(win, wx.ID_ANY, "", choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT | wx.CB_READONLY)

        self.txt_notas = wx.TextCtrl(win, wx.ID_ANY, style=wx.TE_MULTILINE)

        gbs.Add(wx.StaticText(win, wx.ID_ANY, "Host"), (0, 0), flag=wx.ALIGN_CENTER | wx.ALL, border=2)
        gbs.Add(wx.StaticText(win, wx.ID_ANY, "Puerto"), (0, 1), flag=wx.ALIGN_CENTER | wx.ALL, border=2)
        gbs.Add(wx.StaticText(win, wx.ID_ANY, "Usuario"), (0, 2), flag=wx.ALIGN_CENTER | wx.ALL, border=2)
        gbs.Add(wx.StaticText(win, wx.ID_ANY, "Clave"), (0, 3), flag=wx.ALIGN_CENTER | wx.ALL, border=2)
        gbs.Add(wx.StaticText(win, wx.ID_ANY, "Database"), (0, 5), flag=wx.ALIGN_CENTER | wx.ALL, border=2)

        gbs.Add(self.text_host, (1, 0), flag=wx.EXPAND)
        gbs.Add(self.spin_puerto, (1, 1))
        gbs.Add(self.text_usuario, (1, 2), flag=wx.EXPAND)
        gbs.Add(self.text_clave, (1, 3), flag=wx.EXPAND)
        gbs.Add(btn_conectar, (1, 4))
        gbs.Add(self.cb_database, (1, 5), flag=wx.EXPAND)

        gbs.AddGrowableCol(0)
        gbs.AddGrowableCol(2)
        gbs.AddGrowableCol(3)
        gbs.AddGrowableCol(5)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(gbs, 0, wx.EXPAND)
        box.Add(wx.StaticText(win, wx.ID_ANY, "Notas"), 0, wx.ALIGN_CENTER)
        box.Add(self.txt_notas, 1, wx.EXPAND)

        win.SetSizer(box)

        self.Bind(wx.EVT_BUTTON, self.on_btn_conectar, btn_conectar)
        self.Bind(wx.EVT_COMBOBOX, self.on_cb_database, self.cb_database)
        self.Bind(wx.EVT_TEXT, self.on_txt_notas, self.txt_notas)

    def crea_notebook_pag_csv(self, win):
        encode = ["utf-8", "cp1252", "cp437"]#, "cp850", "cp858", "cp1140", "cp1250", "cp65001","latin1", "latin2", "mac_latin2"]

        btn_csv_fic = wx.Button(win, wx.ID_ANY, "...", size=(30, 32))
        self.text_fichero_csv = wx.TextCtrl(win, value="")
        self.cb_csv_encode = wx.ComboBox(win, wx.ID_ANY, "utf-8", size=(106,30), choices=encode, style=wx.CB_DROPDOWN)
        self.cb_csv_delimita = wx.ComboBox(win, wx.ID_ANY, ",", choices=[",", ";", ".", "tab", "esp"], style=wx.CB_DROPDOWN)
        self.sc_csv_lin = wx.SpinCtrl(win, wx.ID_ANY, "50", size=(80, -1))
        self.sc_csv_lin.SetRange(1, 99999)

        self.chk_csv_nombres = wx.CheckBox(win, wx.ID_ANY, u"Nombre de campos en la 1º línea")
        self.btn_csv_add_cam = wx.Button(win, wx.ID_ANY, u"Añadir campo", size=(140,30))
        self.btn_csv_filtros = wx.Button(win, wx.ID_ANY, u"Filtros", size=(140,30))

        bmp = imagenes.refrescar.GetBitmap()
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn = wx.BitmapButton(win, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn.SetToolTipString("Refrescar")

        self.list_csv = BaseListCtrl(win, wx.ID_ANY, style=wx.LC_REPORT)

        gbs = wx.GridBagSizer(5, 10)
        gbs.Add(wx.StaticText(win, wx.ID_ANY, "Fichero"), (0, 0), span=(1, 2), flag=wx.ALIGN_CENTER | wx.ALL, border=2)
        gbs.Add(wx.StaticText(win, wx.ID_ANY, u"Codificación"), (0, 2), flag=wx.ALIGN_CENTER | wx.ALL, border=2)
        gbs.Add(wx.StaticText(win, wx.ID_ANY, "Delimitador"), (0, 3), flag=wx.ALIGN_CENTER | wx.ALL, border=2)
        gbs.Add(wx.StaticText(win, wx.ID_ANY, "Visualizar"), (0, 4), flag=wx.ALIGN_CENTER | wx.ALL, border=2)

        gbs.Add(btn_csv_fic, (1, 0))
        gbs.Add(self.text_fichero_csv, (1, 1), flag=wx.EXPAND)
        gbs.Add(self.cb_csv_encode, (1, 2), flag=wx.ALIGN_CENTER)
        gbs.Add(self.cb_csv_delimita, (1, 3), flag=wx.ALIGN_CENTER | wx.ALL)
        gbs.Add(self.sc_csv_lin, (1, 4), flag=wx.ALIGN_CENTER | wx.ALL)

        gbs.Add(self.chk_csv_nombres, (2, 0), span=(1, 2))
        gbs.Add(self.btn_csv_add_cam, (2, 2))
        gbs.Add(self.btn_csv_filtros, (2, 3))
        gbs.Add(btn, (2, 4), flag=wx.ALIGN_CENTER | wx.ALL)

        gbs.AddGrowableCol(1)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(gbs, 0, wx.EXPAND)
        box.Add(self.list_csv, 1, wx.EXPAND)

        win.SetSizer(box)

        self.Bind(wx.EVT_BUTTON, self.on_btn_csv_fic, btn_csv_fic)
        self.Bind(wx.EVT_COMBOBOX, self.on_csv_modifica, self.cb_csv_delimita)
        self.Bind(wx.EVT_COMBOBOX, self.on_csv_modifica, self.cb_csv_encode)
        self.Bind(wx.EVT_SPINCTRL, self.on_csv_modifica, self.sc_csv_lin)
        self.Bind(wx.EVT_BUTTON, self.on_csv_modifica, btn)
        self.Bind(wx.EVT_BUTTON, self.on_list_csv_add_campo, self.btn_csv_add_cam)
        self.Bind(wx.EVT_BUTTON, self.on_list_csv_filtros, self.btn_csv_filtros)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.on_list_csv_col_right_click, self.list_csv)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.on_col_end_drag, self.list_csv)
        self.Bind(wx.EVT_TEXT, self.on_csv_modifica, self.sc_csv_lin)
        self.Bind(wx.EVT_CHECKBOX, self.on_csv_modifica, self.chk_csv_nombres)
        # for wxMSW
        self.list_csv.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.on_list_csv_col_right_click)
        # for wxGTK
        self.list_csv.Bind(wx.EVT_RIGHT_UP, self.on_list_csv_col_right_click)

    def crea_contenedor(self):
        splitter_v = BaseSplitter(self, "vertical")
        w0 = wx.Panel(splitter_v, style=wx.BORDER_THEME)

        splitter_h = BaseSplitter(splitter_v, "horizontal")
        w1 = wx.Panel(splitter_h, style=wx.BORDER_THEME)

        w2 = wx.Panel(splitter_h, style=wx.BORDER_THEME)

        splitter_h.SetMinimumPaneSize(50)
        splitter_h.SplitVertically(w1, w2, splitter_h.get_size())

        splitter_v.SetMinimumPaneSize(50)
        splitter_v.SplitHorizontally(w0, splitter_h, splitter_v.get_size())

        return w0, w1, w2

    def crea_tool_bar(self):
        tb_id1 = wx.NewId()
        tb_id2 = wx.NewId()
        tb_id3 = wx.NewId()
        tb_id4 = wx.NewId()
        tb_id5 = wx.NewId()
        tb_id6 = wx.NewId()
        tb_id7 = wx.NewId()
        tb_id8 = wx.NewId()
        tb_id9 = wx.NewId()
        tb_id10 = wx.NewId()

        tsize = (24,24)
        self.tb = self.CreateToolBar(style=wx.TB_HORIZONTAL|wx.TB_FLAT)
        self.tb.SetToolBitmapSize(tsize)

        self.tb.AddSeparator()
        bmp1 = wx.ArtProvider_GetBitmap(wx.ART_NEW, wx.ART_OTHER, (16, 16))
        self.tb.AddLabelTool(tb_id1, "Nuevo", bmp1, shortHelp="Nuevo", longHelp=u"Nuevo template")
        bmp2 = wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16, 16))
        self.tb.AddLabelTool(tb_id2, "Abrir", bmp2, shortHelp="Abrir", longHelp=u"Abrir template")
        bmp3 = wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE, wx.ART_OTHER, (16, 16))
        self.tb.AddLabelTool(tb_id3, "Grabar", bmp3, shortHelp="Grabar", longHelp=u"Grabar template")
        bmp4 = wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_OTHER, (16, 16))
        self.tb.AddLabelTool(tb_id4, "Grabar como", bmp4, shortHelp="Grabar como", longHelp=u"Grabar template como")
        self.tb.AddSeparator()
        bmp5 = wx.ArtProvider_GetBitmap(wx.ART_REDO, wx.ART_OTHER, (16, 16))
        self.tb.AddLabelTool(tb_id5, "Importar", bmp5, shortHelp="Importar", longHelp=u"Importar datos")
        self.tb.AddSeparator()
        bmp6 = wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER, (16, 16))
        self.tb.AddLabelTool(tb_id6, "Sql", bmp6, shortHelp="Visor Sql", longHelp=u"Muestra sql")
        self.tb.AddSeparator()
        bmp7 = util.escala_bitmap(imagenes.db2.GetBitmap(), 16, 16)
        self.tb.AddLabelTool(tb_id7, "Grabar DB", bmp7, shortHelp="Grabar DB", longHelp=u"Grabar estado actual de la BD")
        bmp8 = util.escala_bitmap(imagenes.db3.GetBitmap(), 16, 16)
        self.tb.AddLabelTool(tb_id8, "Chquear DB", bmp8, shortHelp="Comparar DB", longHelp=u"Comparar la BD actual con la grabada anteriormente")
        bmp9 = util.escala_bitmap(imagenes.db1.GetBitmap(), 16, 16)
        self.tb.AddLabelTool(tb_id9, u"Cargar comparación", bmp9, shortHelp=u"Cargar comparación", longHelp=u"Cargar comparación")
        #
        bmp10 = util.escala_bitmap(imagenes.smiles.GetBitmap(), 16, 16)
        self.tb.AddLabelTool(tb_id10, "Desconectar DB", bmp10, shortHelp="Desconectar DB", longHelp=u"Desconectar de la BD")

        self.tb.Realize()

        self.Bind(wx.EVT_MENU, self.on_nuevo, id=tb_id1)
        self.Bind(wx.EVT_MENU, self.on_abrir, id=tb_id2)
        self.Bind(wx.EVT_MENU, self.on_grabar, id=tb_id3)
        self.Bind(wx.EVT_MENU, self.on_grabar_como, id=tb_id4)
        self.Bind(wx.EVT_MENU, self.on_importar, id=tb_id5)
        self.Bind(wx.EVT_MENU, self.on_sql, id=tb_id6)
        self.Bind(wx.EVT_MENU, self.on_grabar_db, id=tb_id7)
        self.Bind(wx.EVT_MENU, self.on_comparar_db, id=tb_id8)
        self.Bind(wx.EVT_MENU, self.on_carga_compara, id=tb_id9)
        self.Bind(wx.EVT_MENU, self.on_desconectar, id=tb_id10)

    def crea_menu(self):
        menu_id1 = wx.NewId()
        menu_id2 = wx.NewId()
        menu_id3 = wx.NewId()
        menu_id4 = wx.NewId()
        self.menu_id5 = wx.NewId()
        menu_id6 = wx.NewId()
        menu_id7 = wx.NewId()
        menu_id8 = wx.NewId()
        menu_id9 = wx.NewId()
        menu_id10 = wx.NewId()
        menu_id11 = wx.NewId()
        menu_id12 = wx.NewId()

        self.menu_bar = wx.MenuBar()
        self.SetMenuBar(self.menu_bar)

        menu1 = wx.Menu()
        self.menu_bar.Append(menu1, "&Fichero")

        item1 = wx.MenuItem(menu1, menu_id1, "&Nuevo", u"Nuevo template")
        bmp1 = wx.ArtProvider_GetBitmap(wx.ART_NEW, wx.ART_OTHER, (16,16))
        item1.SetBitmap(bmp1)
        menu1.AppendItem(item1)

        item2 = wx.MenuItem(menu1, menu_id2, "&Abrir", u"Abrir template")
        bmp2 = wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16,16))
        item2.SetBitmap(bmp2)
        menu1.AppendItem(item2)

        item3 = wx.MenuItem(menu1, menu_id3, "&Grabar", u"Grabar template")
        bmp3 = wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE, wx.ART_OTHER, (16,16))
        item3.SetBitmap(bmp3)
        menu1.AppendItem(item3)

        item4 = wx.MenuItem(menu1, menu_id4, "&Grabar Como...", u"Grabar template como...")
        bmp4 = wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_OTHER, (16,16))
        item4.SetBitmap(bmp4)
        menu1.AppendItem(item4)

        menu1.AppendSeparator()
#--
        submenu = wx.Menu()

        item5 = wx.MenuItem(submenu, self.menu_id5, "&Importar", u"Realizar la importación")
        bmp5 = wx.ArtProvider_GetBitmap(wx.ART_REDO, wx.ART_OTHER, (16,16))
        item5.SetBitmap(bmp5)
        submenu.AppendItem(item5)

        submenu.AppendSeparator()

        item6 = wx.MenuItem(submenu, menu_id6, "&Grabar BD", u"Grabar estado actual de la BD")
        bmp6 = util.escala_bitmap(imagenes.db2.GetBitmap(), 16, 16)
        item6.SetBitmap(bmp6)
        submenu.AppendItem(item6)

        item8 = wx.MenuItem(submenu, menu_id8, "&Comparar BD", u"Comparar la BD actual con la grabada anteriormente")
        bmp8 = util.escala_bitmap(imagenes.db3.GetBitmap(), 16, 16)
        item8.SetBitmap(bmp8)
        submenu.AppendItem(item8)

        menu1.AppendMenu(menu_id11, "&Base de Datos", submenu)
#--
        menu1.AppendSeparator()

        item7 = wx.MenuItem(submenu, menu_id7, "Exportar csv", u"Exportar csv en codificación")
        bmp7 = util.escala_bitmap(imagenes.csv.GetBitmap(), 16, 16)
        item7.SetBitmap(bmp7)
        menu1.AppendItem(item7)

        menu1.AppendSeparator()

        item9 = wx.MenuItem(menu1, menu_id9, "&Salir", u"Cierra la ventana")
        bmp9 = wx.ArtProvider_GetBitmap(wx.ART_QUIT, wx.ART_OTHER, (16,16))
        item9.SetBitmap(bmp9)
        menu1.AppendItem(item9)

        menu2 = wx.Menu()
        self.menu_bar.Append(menu2, "&Ayuda")

        item12 = wx.MenuItem(menu2, menu_id12, "&Ayuda", '')
        menu2.AppendItem(item12)
        menu2.AppendSeparator()
        item10 = wx.MenuItem(menu2, menu_id10, "Acerca de " + APLICACION, '')
        menu2.AppendItem(item10)

        #Eventos del menu
        self.Bind(wx.EVT_MENU_OPEN, self.on_menu_open)
        self.Bind(wx.EVT_MENU, self.on_nuevo, id=menu_id1)
        self.Bind(wx.EVT_MENU, self.on_abrir, id=menu_id2)
        self.Bind(wx.EVT_MENU, self.on_grabar, id=menu_id3)
        self.Bind(wx.EVT_MENU, self.on_grabar_como, id=menu_id4)
        self.Bind(wx.EVT_MENU, self.on_importar, id=self.menu_id5)
        self.Bind(wx.EVT_MENU, self.on_grabar_db, id=menu_id6)
        self.Bind(wx.EVT_MENU, self.on_comparar_db, id=menu_id8)
        self.Bind(wx.EVT_MENU, self.on_list_csv_exportar, id=menu_id7)
        self.Bind(wx.EVT_MENU, self.on_salir, id=menu_id9)
        self.Bind(wx.EVT_MENU, self.on_acerca, id=menu_id10)
        self.Bind(wx.EVT_MENU, self.on_ayuda, id=menu_id12)

    def existe_nombre_data(self, nombre):
        pgi = Pgi(self.data)
        nombres = pgi.get_nombres()
        if nombre in nombres:
            if nombre.find("csv.") == 0:
                nombre = nombre[4:]
            wx.MessageBox("El nombre ya existe: [%s]" % nombre, self.app.GetAppName(), wx.ICON_ERROR)
            return True
        return False

    def dialogo_codigo(self, data=None, key_data=None, titulo=None):
        ayuda = u"Se tiene acceso al diccionario con los "
        ayuda += "valores del pgi en la variable _pgi "
        ayuda += ", pudiendo modificar cualquier valor, "
        ayuda += "a la variable global _global y a la "
        ayuda += "clase DbPostgres con _db."
        ayuda = wordwrap(ayuda, 450, wx.ClientDC(self))

        """Para listar las variables y su valor:
            import wx
            variables = list()
            for nom in dir() :
                if not nom.startswith("__") and nom != "variables" and nom != "wx":
                    variables.append("%s=%s" % (nom , locals()[nom]))
            wx.MessageBox("\n".join(variables),  "Inicial",  wx.ICON_ERROR)
        """

        dlg = DlgDefCampo(self, wx.ID_ANY, titulo, data, ayuda, True, True)
        while True:
            dlg.CenterOnParent()
            val = dlg.ShowModal()
            if val == wx.ID_OK:
                data_nuevo = dlg.get_data()
                key = data_nuevo["nombre"]
                if key:
                    if key_data:
                        if key != data["nombre"]:
                            if self.existe_nombre_data(key):
                                continue
                        self.data[key_data] = data_nuevo
                    else:
                        if self.existe_nombre_data(key):
                            continue
                        n = self.n_registros(titulo)
                        self.data["%s%s" % (titulo, n)] = data_nuevo
                    self.carga_origen()
                    item = util.tree_get_item_text(self.tree_org, key, titulo)
                    util.tree_expand_item(self.tree_org, item)
                    self.tree_org.SelectItem(item)
            break
        dlg.Destroy()

    def dialogo_fijo(self, data=None, key_data=None):
        dlg = DlgValorFijo(self, wx.ID_ANY, VALOR_FIJO, data)
        dlg.CenterOnParent()
        while True:
            val = dlg.ShowModal()
            if val == wx.ID_OK:
                data_nuevo = dlg.get_data()
                key = data_nuevo["nombre"]
                if key:
                    if key_data:
                        if key != data["nombre"]:
                            if self.existe_nombre_data(key):
                                continue
                        self.data[key_data] = data_nuevo
                    else:
                        if self.existe_nombre_data(key):
                            continue
                        n = self.n_registros(VALOR_FIJO)
                        self.data["%s%s" % (VALOR_FIJO, n)] = data_nuevo
                    self.carga_origen()
                    item = util.tree_get_item_text(self.tree_org, key, VALOR_FIJO)
                    util.tree_expand_item(self.tree_org, self.tree_org.GetItemParent(item))
                    self.tree_org.SelectItem(item)
            break
        dlg.Destroy()

    def dialogo_inicial(self, data=None, key_data=None):
        dlg = DlgSql(self, wx.ID_ANY, SQL_INI, data, False)
        dlg.CenterOnParent()
        while True:
            val = dlg.ShowModal()
            if val == wx.ID_OK:
                data_nuevo = dlg.get_data()
                key = data_nuevo["nombre"]
                if key:
                    if key_data:
                        if key != data["nombre"]:
                            if self.existe_nombre_data(key):
                                continue
                        self.data[key_data] = data_nuevo
                    else:
                        if self.existe_nombre_data(key):
                            continue
                        n = self.n_registros(SQL_INI)
                        self.data["%s%s" % (SQL_INI, n)] = data_nuevo
                    self.carga_origen()
                    item = util.tree_get_item_text(self.tree_org, key, SQL_INI)
                    util.tree_expand_item(self.tree_org, item)
                    self.tree_org.SelectItem(item)
            break
        dlg.Destroy()

    def dialogo_registro(self, data=None, key_data=None):
        insert = list()
        for k in self.data.iterkeys():
            if k.find(ID_INSERT) == 0:
                insert.append(self.data[k][0])

        dlg = DlgSql(self, wx.ID_ANY, SQL_REG, data, True, insert)
        dlg.CenterOnParent()
        while True:
            val = dlg.ShowModal()
            if val == wx.ID_OK:
                data_nuevo = dlg.get_data()
                key = data_nuevo["nombre"]
                if key:
                    if data_nuevo["modificar"]:
                        if len(data_nuevo["tablas"]) != 1:
                            wx.MessageBox("Para modificar solo puede ser una tabla", APLICACION, wx.ICON_ERROR)
                            continue
                        if not data_nuevo["tablas"][0][0:2].isnumeric() or data_nuevo["tablas"][0][2:3] != "_":
                            wx.MessageBox(u"Para modificar debe referenciar la tabla igual al 'Destino',\nanteponiendo el prefijo '??_'", APLICACION, wx.ICON_ERROR)
                            continue
                    elif data_nuevo["tablas"] and data_nuevo["tablas"][0][0:2].isnumeric() and data_nuevo["tablas"][0][2:3] == "_":
                        wx.MessageBox(u"El prefijo '??_' de la tabla es solo para la opción modificar.", APLICACION, wx.ICON_ERROR)
                        continue

                    if key_data:
                        if key != data["nombre"]:
                            if self.existe_nombre_data(key):
                                continue
                        self.data[key_data] = data_nuevo
                    else:
                        if self.existe_nombre_data(key):
                            continue
                        n = self.n_registros(SQL_REG)
                        self.data["%s%s" % (SQL_REG, n)] = data_nuevo
                    self.carga_origen()
                    item = util.tree_get_item_text(self.tree_org, key, SQL_REG)
                    util.tree_expand_item(self.tree_org, item)
                    self.tree_org.SelectItem(item)
            break
        dlg.Destroy()

    def dialogo_campo_reg(self, data=None, key_data=None):
        ayuda = "Se tiene acceso a los campos anteponiendo "
        ayuda += "el prefijo '@' y '@csv.' a los del csv, "
        ayuda += "estos se deben de poner entre comillas. "
        ayuda += "Y a la variable global _global y a la clase "
        ayuda += "DbPostgres con _db.\n"
        ayuda += "En la definición hay que asignar el nombre del "
        ayuda += "campo a un valor.."

        ayuda = wordwrap(ayuda, 450, wx.ClientDC(self))

        dlg = DlgDefCampo(self, wx.ID_ANY, CAMPO_REG, data, ayuda)
        while True:
            dlg.CenterOnParent()
            val = dlg.ShowModal()
            if val == wx.ID_OK:
                data_nuevo = dlg.get_data()
                key = data_nuevo["nombre"]
                if key:
                    err = codigo.check_funcion(data_nuevo["valor"], self.db)
                    if err:
                        wx.MessageBox(err, APLICACION, wx.ICON_ERROR, self)
                        continue
                    if key_data:
                        if key != data["nombre"]:
                            if self.existe_nombre_data(key):
                                continue
                        self.data[key_data] = data_nuevo
                    else:
                        if self.existe_nombre_data(key):
                            continue
                        n = self.n_registros(CAMPO_REG)
                        self.data["%s%s" % (CAMPO_REG, n)] = data_nuevo
                    self.carga_origen()
                    item = util.tree_get_item_text(self.tree_org, key, CAMPO_REG)
                    util.tree_expand_item(self.tree_org, item)
                    self.tree_org.SelectItem(item)
            break
        dlg.Destroy()

    def dialogo_campo(self, data, campo, item):
        valor = data["campos"][campo]
        dlg = DlgValorCampoSql(self, wx.ID_ANY, campo, valor)
        dlg.CenterOnParent()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            text = dlg.get_data()
            data["campos"][campo] = text
            item, cookie = self.tree_org.GetFirstChild(item)
            if item.IsOk():
                self.tree_org.SetItemText(item, text)
        dlg.Destroy()

    def dialogo_campo_def(self, data=None, key_data=None):
        ayuda = u"Se tiene acceso al csv con el nombre del campo, "
        ayuda += u"siempre de tipo str. "
        ayuda += u"En la definición hay que asignar el nombre del "
        ayuda += u"campo a un valor."
        ayuda = wordwrap(ayuda, 450, wx.ClientDC(self))

        dlg = DlgDefCampo(self, wx.ID_ANY, CAMPO_DEF, data, ayuda)
        dlg.CenterOnParent()
        while True:
            val = dlg.ShowModal()
            if val == wx.ID_OK:
                data_nuevo = dlg.get_data()
                if FICHERO_CSV not in self.data or "campos" not in self.data[FICHERO_CSV]:
                    break
                campos = self.data[FICHERO_CSV]["campos"]
                err = codigo.evalua_codigo(data_nuevo["nombre"], data_nuevo["valor"], campos, self.get_1valor_csv())
                if err:
                    wx.MessageBox(err, APLICACION, wx.ICON_ERROR)
                    continue
                else:
                    key = data_nuevo["nombre"]
                    if key_data:
                        if key != data["nombre"]:
                            if self.existe_nombre_data("csv.%s" % key):
                                continue
                        self.data[key_data] = data_nuevo
                    else:
                        if self.existe_nombre_data("csv.%s" % key):
                            continue
                        n = self.n_registros(CAMPO_DEF)
                        self.data["%s%s" % (CAMPO_DEF, n)] = data_nuevo
                    self.get_data()
                    fichero = self.data[FICHERO_CSV]["fichero"]
                    delimitador = self.data[FICHERO_CSV]["delimitador"]
                    nombres1 = self.data[FICHERO_CSV]["nombres1"]
                    lineas = self.data[FICHERO_CSV]["lineas"]
                    encode = self.data[FICHERO_CSV]["encode"]
                    self.carga_fichero_csv(fichero, delimitador, nombres1, lineas, encode)
            break
        dlg.Destroy()

    def get_1valor_csv(self):
        self.get_data()
        fichero = self.data[FICHERO_CSV]["fichero"]
        delimitador = self.data[FICHERO_CSV]["delimitador"]
        nombres1 = self.data[FICHERO_CSV]["nombres1"]
        encode = self.data[FICHERO_CSV]["encode"]
        campos = list()
        try:
            with open(fichero, 'rb') as f:
                for i, cam in enumerate(UnicodeReader(f, encoding=encode, delimiter=str(delimitador), quotechar='"')):
                    lon = len(cam)
                    if i == 0 and nombres1:
                        continue
                    for n in range(0, lon):
                        campos.append(cam[n])
                    break
        except:
            pass
        return campos

    def set_data(self, data):
        if NOTAS in data:
            self.txt_notas.SetValue(data[NOTAS])
        else:
            self.txt_notas.SetValue("")

        if NOMBRE in data:
            self.SetTitle("%s (%s)" % (APLICACION, data[NOMBRE]))

        if FICHERO_CSV in data:
            if not os.path.isfile(data[FICHERO_CSV]["fichero"]):
                if data[FICHERO_CSV]["fichero"]:
                    txt = "No existe el fichero:%s" % data[FICHERO_CSV]["fichero"]
                    self.infobar_cb.ShowMessage(txt, wx.ICON_ERROR)
                data[FICHERO_CSV]["fichero"] = ""

            self.text_fichero_csv.Value = data[FICHERO_CSV]["fichero"]

            if data[FICHERO_CSV]["delimitador"] == chr(9):
                self.cb_csv_delimita.Value = "tab"
            elif data[FICHERO_CSV]["delimitador"] == " ":
                self.cb_csv_delimita.Value = "esp"
            else:
                self.cb_csv_delimita.Value = data[FICHERO_CSV]["delimitador"]

            self.chk_csv_nombres.Value = data[FICHERO_CSV]["nombres1"]
            self.sc_csv_lin.Value = int(data[FICHERO_CSV]["lineas"])
            self.cb_csv_encode.Value = data[FICHERO_CSV]["encode"]
            self.carga_fichero_csv(data[FICHERO_CSV]["fichero"], data[FICHERO_CSV]["delimitador"],
                                   data[FICHERO_CSV]["nombres1"], data[FICHERO_CSV]["lineas"],
                                   data[FICHERO_CSV]["encode"])
        else:
            self.carga_origen()

        if CONEXION in data:
            self.text_host.Value = data[CONEXION]["host"]
            self.spin_puerto.Value = data[CONEXION]["puerto"]
            self.text_usuario.Value = data[CONEXION]["usuario"]
            self.text_clave.Value = data[CONEXION]["clave"]
            self.cb_database.SetValue(data[CONEXION]["database"])
            wx.Yield()
            self.tree_des.DeleteAllItems()
            self.tree_des_cam.DeleteAllItems()
            if data[CONEXION]["database"].strip():
                if self.carga_databases(data[CONEXION]["host"], data[CONEXION]["puerto"], data[CONEXION]["usuario"],
                                     data[CONEXION]["clave"], data[CONEXION]["database"]):
                    self.carga_tablas(data[CONEXION]["host"], data[CONEXION]["puerto"], data[CONEXION]["usuario"],
                                      data[CONEXION]["clave"], data[CONEXION]["database"])
                self.carga_destino()

        root = self.tree_org.GetRootItem()
        if root:
            self.tree_org.Expand(root)
            self.tree_org_item = root

        root = self.tree_des_cam.GetRootItem()
        if root:
            self.tree_des_cam.Expand(root)
            self.tree_des_cam_item = root

    def get_data(self):
        host = self.text_host.Value
        puerto = self.spin_puerto.Value
        usuario = self.text_usuario.Value
        clave = self.text_clave.Value
        database = self.cb_database.GetValue()

        lineas = self.sc_csv_lin.Value
        encode = self.cb_csv_encode.Value
        fichero = self.text_fichero_csv.Value
        delimitador = self.cb_csv_delimita.Value
        nombres1 = self.chk_csv_nombres.Value

        if delimitador == "tab":
            delimitador = chr(9)

        if delimitador == "esp":
            delimitador = " "

        campos = []
        if FICHERO_CSV in self.data and "campos" in self.data[FICHERO_CSV]:
            campos = self.data[FICHERO_CSV]["campos"]

        self.data[VERSION] = NVERSION

        self.data[CONEXION] = {"host": host, "puerto": puerto, "usuario": usuario, "clave": clave,
                               "database": database}

        self.data[FICHERO_CSV] = {"fichero": fichero, "delimitador": delimitador, "nombres1": nombres1,
                                  "campos": campos, "lineas": lineas, "encode": encode}

        return self.data

    def grabar(self, fichero):
        self.fichero_pgi = fichero
        try:
            with open(fichero, 'w') as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
            self.fichero_pgi = fichero
            archivo = os.path.basename(fichero)
            self.data[NOMBRE] = archivo
            self.SetTitle("%s (%s)" % (APLICACION, archivo))
        except IOError, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

    def abrir(self, fichero):
        self.pon_reloj()
        busy = wx.BusyInfo("Cargando...", self)
        wx.Yield()

        try:
            with open(fichero, 'r') as f:
                self.data = json.load(f)

            self.fichero_pgi = fichero
            archivo = os.path.basename(fichero)
            self.data[NOMBRE] = archivo
            self.SetTitle("%s (%s)" % (APLICACION, archivo))
            if self.data and "Version" in self.data:
                if versiontuple(self.data["Version"]) < "0.1.1":
                    txt = u"Versión incorrecta [%s], actual [%s]" % (self.data["Version"], NVERSION)
                    self.infobar_cb.ShowMessage(txt, wx.ICON_ERROR)
                    # wx.MessageBox(txt, APLICACION, wx.ICON_ERROR)
                else:
                    self.set_data(self.data)
        except IOError, e:
            self.infobar_cb.ShowMessage(str(e), wx.ICON_ERROR)
            # wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

        except ValueError, e:
            self.infobar_cb.ShowMessage(str(e), wx.ICON_ERROR)
            # wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

        del busy
        self.quita_reloj()

    def info(self, txt):
        self.SetStatusText(txt, 0)
        lis = txt.split(":")
        if len(lis) == 3 and lis[1] == VALOR_FIJO:
            txt = lis[2]
        elif len(lis) == 4 and lis[1] == SQL_INI and lis[0] == "3":
            txt = lis[3]
        elif len(lis) == 3 and lis[1] == FICHERO_CSV:
            txt = lis[2]
        elif len(lis) == 4 and lis[1] == SQL_REG and lis[0] == "3":
            txt = lis[3]
        elif len(lis) == 3 and lis[1] == ID_INSERT:
            txt = lis[2]
        else:
            txt = ""
        self.SetStatusText(txt, 1)

    def n_registros(self, key):
        n = 0
        for k in sorted(self.data.iterkeys()):
            if k.find(key) == 0:
                n = int(k[len(key):])
        return '%03d' % (n + 1)

    def n_registros_tabla(self, tabla):
        n = 0
        for k, v in sorted(self.data.iteritems()):
            if k.find(ID_INSERT) == 0 and v[0][3:] == tabla:
                n = v[0].split("_")
                n = int(n[0])
        return '%02d_%s' % ((n + 1), tabla)

    def asigna(self, campo_org, tabla, campo_des):
        self.info("%s=>%s.%s" % (campo_org, tabla, campo_des))
        item = util.tree_get_item_data(self.tree_des_cam, "2:%s:%s" % (tabla, campo_des))
        if item:
            txt = self.tree_des_cam.GetPyData(item).split(":")
            self.tree_des_cam.SetItemText(item, "%s = @%s" % (txt[2], campo_org))
            for k, v in self.data.iteritems():
                if k.find(ID_INSERT) == 0 and v[0] == tabla:
                    for i in range(0, len(self.data[k][1])):
                        if self.data[k][1][i][0][0] == campo_des:
                            self.data[k][1][i][1] = "@" + campo_org
                            self.tree_des_cam.SetItemImage(item, self.idxasig, wx.TreeItemIcon_Normal)

    def grabar_db(self, db, tablas, fichero):
        path = tempfile.mkdtemp()

        if tablas:
            maximo = len(tablas)
            dlg = wx.ProgressDialog("Exportando datos", "Exportar", maximum=maximo, parent=self,
                                    style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME)
                                    #|wx.PD_ESTIMATED_TIME| wx.PD_REMAINING_TIME)# | wx.PD_AUTO_HIDE)
            dlg.SetIcon(imagenes.importar.GetIcon())
            count = 0
            for t in sorted(tablas):
                count += 1
                #wx.MilliSleep(250)
                wx.Yield()
                (sigue, salta) = dlg.Update(count, t)
                if not sigue:
                    break
                error = exporta_tabla(path, db, t)
                if error:
                    wx.MessageBox(error, self.app.GetAppName(), wx.ICON_ERROR)
                    break
            busy = wx.BusyInfo("Creando zip...", self)
            wx.Yield()
            fzip = Zip(fichero)
            fzip.push_path(path, ".", True)
            fzip.fichero()
            del busy
            dlg.Update(maximo)
            dlg.Destroy()

        shutil.rmtree(path, True)

    def comparar_db(self, db, fichero):
        path = tempfile.mkdtemp()

        busy = wx.BusyInfo("Extraiendo zip...", self)
        wx.Yield()
        fzip = Zip(fichero)
        del busy
        error = fzip.extrae(path)
        if error:
            wx.MessageBox("%s\n\n[%s]" % (error.message, fichero), self.app.GetAppName(), wx.ICON_ERROR)
            return

        ficheros = []
        for fic in os.listdir(path):
            f = os.path.join(path, fic)
            if not os.path.isdir(f):
                ficheros.append(f)

        maximo = len(ficheros)
        dlg = wx.ProgressDialog("Comparando datos", "Compara", maximum=maximo, parent=self,
                                style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME | wx.PD_AUTO_HIDE)
                                #|wx.PD_ESTIMATED_TIME| wx.PD_REMAINING_TIME)# | wx.PD_AUTO_HIDE)
        dlg.SetIcon(imagenes.importar.GetIcon())
        count = 0
        datos = dict()
        lon = len(path) + 1
        for fichero in sorted(ficheros):
            tabla = fichero[lon:-4]
            count += 1
            #wx.MilliSleep(250)
            wx.Yield()
            (sigue, salta) = dlg.Update(count, tabla)
            if not sigue:
                break
            error = compara_tabla(datos, fichero, db, tabla)
            if error:
                wx.MessageBox(error, self.app.GetAppName(), wx.ICON_ERROR)
                break
        dlg.Update(maximo)
        dlg.Destroy()
        if datos:
            frm = FrmCompara(self, wx.ID_ANY, self.db, datos)
            frm.CenterOnParent()
            frm.Show()
            #frm.SetFocus() No se porque falla esto, lo hago con FutureCall y ya va
            wx.FutureCall(1000, frm.SetFocus)
        else:
            wx.MessageBox("No hay modificaciones...", self.app.GetAppName(), wx.ICON_INFORMATION)

        shutil.rmtree(path, True)

    def exporta_csv(self, destino, descam, desnom1):
        fichero = self.data[FICHERO_CSV]["fichero"]
        try:
            maximo = open(fichero).read().count('\n')
        except IOError, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)
            return

        dlg = wx.ProgressDialog("Exportando datos", "Exportar", maximum=maximo, parent=self,
                                style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME
                                | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)
        dlg.SetIcon(imagenes.importar.GetIcon())

        try:
            cam_def = []
            for k, v in self.data.iteritems():
                if k.find(CAMPO_DEF) == 0:
                    cam_def.append([v["nombre"], v["valor"]])

            if cam_def:
                funciones, err = codigo.crea_modulo(cam_def, self.data[FICHERO_CSV])
                if err:
                    raise Exception(err)

            origen = self.data[FICHERO_CSV]["fichero"]
            encode = self.data[FICHERO_CSV]["encode"]
            orgnom1 = self.data[FICHERO_CSV]["nombres1"]
            orgcam = self.data[FICHERO_CSV]["campos"]
            delimitador = str(self.data[FICHERO_CSV]["delimitador"])
            with open(destino, 'wb') as f1:
                # w = UnicodeWriter(f1, encoding="utf-8", delimiter=chr(9), quotechar='"')
                w = UnicodeWriter(f1, encoding=encode, delimiter=delimitador, quotechar='"')
                if desnom1:
                    w.writerow(descam)
                datos = dict()
                with open(origen, 'rb') as f2:
                    for i, cam in enumerate(UnicodeReader(f2, encoding=encode, delimiter=str(delimitador), quotechar='"')):
                        (sigue, salta) = dlg.Update(i, u"línea:%d" % i)
                        #wx.MilliSleep(250)
                        if not sigue:
                            break

                        if i == 0 and orgnom1:
                            continue

                        for j in range(0, len(orgcam)):
                            datos[orgcam[j]] = cam[j]

                        for c in cam_def:
                            try:
                                valor = funciones[c[0]](cam)
                            except:
                                exc_type, exc_value, exc_traceback = sys.exc_info()
                                exc = traceback.format_exception(exc_type, exc_value, exc_traceback)
                                exc.insert(0, "*** Linea csv:%s ***%s" % (i, os.linesep))
                                raise Exception(os.linesep.join(exc))

                            if type(valor) != unicode:
                                valor = str(valor)

                            datos[c[0]] = valor

                        nuevo = []
                        for j in range(0, len(descam)):
                            nuevo.append(datos[descam[j]])
                        w.writerow(nuevo)

                        if i % 100 == 0: wx.Yield()

        except IOError, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

        except Exception, e:
            wx.MessageBox(e.message, APLICACION, wx.ICON_ERROR)

        finally:
            dlg.Update(maximo)
            dlg.Destroy()

    def on_carga_compara(self, event):
        if self.db.esta_conectada:
            fichero = dialogo_abrir_fic(self, "Archivos pgc (*.pgc)|*.pgc|Todos los archivos (*.*)|*")
            if fichero:
                busy = wx.BusyInfo("Cargando...", self)
                datos = util.read_object(fichero[0])
                del busy
                frm = FrmCompara(self, wx.ID_ANY, self.db, datos)
                frm.CenterOnParent()
                frm.Show()
                # frm.SetFocus() No se porque falla esto, lo hago con FutureCall y ya va
                wx.FutureCall(1000, frm.SetFocus)

    def on_desconectar(self, event):
        self.db.close()
        wx.FutureCall(2500, self.on_show)
        self.Hide()
        # frm = FrmSql1(self, wx.ID_ANY, self.db, None)
        # frm.CenterOnParent()
        # frm.Show()
        # frm.SetFocus()

    def on_show(self):
        self.Show()


class MyApp(wx.App):
    propidades = dict()
    config = None
    fic_config = ""

    def __init__(self, redirect=False):
        wx.App.__init__(self, redirect)

    def OnInit(self):
        wx.SetDefaultPyEncoding("utf-8")
        self.locale = wx.Locale(wx.LANGUAGE_SPANISH)

        self.config = self.get_config()
        propi = self.config.Read("propiedades")
        ver = self.config.Read("version")
        try:
            if propi and ver == self.get_version:
                self.propidades = pickle.loads(propi.decode("hex").decode("zlib"))
        except:
            pass

        self.SetAppName(APLICACION)

        if not "MIDEBUG" in os.environ:
            sys.excepthook = ExceptionHook

        frame = Frame(self)
        frame.Show()
        return True

    def OnExit(self):
        propi = pickle.dumps(self.propidades).encode("zlib").encode('hex')
        #propi = json.dumps(self.propidades)
        self.config.Write("version", self.get_version)
        self.config.Write("propiedades", propi)
        self.config.Flush()
        self.Exit()

    @property
    def get_version(self):
        return NVERSION

    @property
    def get_data_dir(self):
        sp = wx.StandardPaths.Get()
        return sp.GetUserDataDir()

    def get_config(self):
        if not os.path.exists(self.get_data_dir):
            os.makedirs(self.get_data_dir)
        self.fic_config = os.path.join(self.get_data_dir, "propiedades")
        config = wx.FileConfig(localFilename=self.fic_config)
        return config

    def get_propiedad(self, propi):
        if propi in self.propidades:
            return self.propidades[propi]
        return None

    def set_propiedad(self, propi, valor):
        self.propidades[propi] = valor


def main():
    try:
        path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(path)
    except:
        pass

    app = MyApp()
    app.MainLoop()

if __name__ == '__main__':
    main()

# http://mundogeek.net/archivos/2008/09/23/distribuir-aplicaciones-python/

# en
# def asigna(self, campo_org, tabla, campo_des):
# hay que refrescar el Tree_org para que refleje lo asignado
# En desasignar lo mismo
#
# en carga_origen
# 	descomentar
# 		asignado = None # self.get_campo_asignado_destino("@%s" % nombre)[1]
# 		ademas hay que ver donde se utiliza el text en lugar de data para asignar valores