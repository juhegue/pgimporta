# -*- coding: utf-8 -*-

import pickle
import util
from bases import *
from constantes import *
from dialogos import dialogo_abrir_fic, dialogo_grabar_fic


class FrmCompara(BaseFrame):
    def __init__(self, parent, id, db, data):
        BaseFrame.__init__(self, parent, id, parent.app.GetAppName() + " (Compara)", (400, 400),
                          style=wx.DEFAULT_FRAME_STYLE)# | wx.STAY_ON_TOP)
        self.parent = parent
        self.db = db
        self.data = data
        self.tabla_actual = None
        #util.save_object(data, "/home/juan/workspace/frmcompara")

        self.SetIcon(parent.GetIcon())

        s0 = BaseSplitter(self, "izquierda", 150)
        p0 = wx.Panel(s0, style=wx.BORDER_THEME)

        s1 = BaseSplitter(s0, "derecha", 150)
        p1 = wx.Panel(s1, style=wx.BORDER_THEME)

        p2 = wx.Panel(s1, style=wx.BORDER_THEME)

        s1.SetMinimumPaneSize(10)
        s1.SplitVertically(p1, p2, s1.get_size())

        s0.SetMinimumPaneSize(10)
        s0.SplitVertically(p0, s1, s0.get_size())

        b0 = wx.BoxSizer()
        b1 = wx.BoxSizer()
        b2 = wx.BoxSizer()

        p0.SetSizer(b0)
        p1.SetSizer(b1)
        p2.SetSizer(b2)

        t0 = wx.TreeCtrl(p0, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HAS_BUTTONS)
        t0.SetImageList(parent.imglst)
        b0.Add(t0, 1, wx.EXPAND)

        l1 = BaseListCtrl(p1, wx.ID_ANY, style=wx.LC_REPORT)
        l1.SetImageList(parent.imglst, wx.IMAGE_LIST_SMALL)
        b1.Add(l1, 1, wx.EXPAND)

        t2 = wx.TreeCtrl(p2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HAS_BUTTONS)
        t2.SetImageList(parent.imglst)
        b2.Add(t2, 1, wx.EXPAND)

        self.treeiz = t0
        self.list = l1
        self.treede = t2

        self.crea_tool_bar()

        self.carga_tree()

        self.set_size()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_tree_changed, self.treeiz)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected, self.list)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.on_col_end_drag, self.list)
        self.treede.Bind(wx.EVT_KEY_DOWN, self.on_treede_keydown)
        self.treeiz.Bind(wx.EVT_KEY_DOWN, self.on_treeiz_keydown)

    def crea_tool_bar(self):
        tb_id1 = wx.NewId()
        tb_id2 = wx.NewId()

        tsize = (24,24)
        self.tb = self.CreateToolBar(style=wx.TB_HORIZONTAL|wx.TB_FLAT)
        self.tb.SetToolBitmapSize(tsize)

        self.tb.AddSeparator()
        bmp1 = wx.ArtProvider_GetBitmap(wx.ART_QUIT, wx.ART_OTHER, (16,16))
        self.tb.AddLabelTool(tb_id1, "Salir", bmp1, shortHelp="Salir", longHelp=u"Salir")
        bmp3 = wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE, wx.ART_OTHER, (16, 16))
        self.tb.AddLabelTool(tb_id2, "Grabar", bmp3, shortHelp="Grabar", longHelp=u"Grabar comparación")

        self.tb.Realize()

        self.Bind(wx.EVT_MENU, self.on_salir, id=tb_id1)
        self.Bind(wx.EVT_MENU, self.on_grabar, id=tb_id2)

    def on_salir(self, event):
        self.Close()

    def on_grabar(self, event):
        fichero = dialogo_grabar_fic(self, "pgc", "Archivos pgc (*.pgc)|*.pgc|Todos los archivos (*.*)|*", "")
        if fichero:
            try:
                busy = wx.BusyInfo("Crabando...", self)
                util.save_object(self.data, fichero)
                # with open(fichero, 'w') as f:
                #     pickle.dump(self.data.encode("zlib").encode('hex'), f)
            except IOError, e:
                wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR, self)
            finally:
                del busy

    def on_size(self, event):
        valor = self.GetSizeTuple()
        if valor[0] < 200 or valor[1] < 200:
            return

        self.set_propi_size()
        event.Skip(True)

    def on_col_end_drag(self, event):
        if self.tabla_actual:
            self.list.set_propi_columns(self.tabla_actual)

    def on_treede_keydown(self, event):
        key = event.KeyCode
        if event.ControlDown() and key in (ord('C'), ord('C')):
            item = self.treede.GetSelection()
            if item.IsOk():
                data = self.treede.GetItemText(item).strip()
                clipdata = wx.TextDataObject()
                clipdata.SetText(data)
                wx.TheClipboard.Open()
                wx.TheClipboard.SetData(clipdata)
                wx.TheClipboard.Close()

    def on_treeiz_keydown(self, event):
        key = event.KeyCode
        if event.ControlDown() and key in (ord('C'), ord('C')):
            item = self.treeiz.GetSelection()
            if item.IsOk():
                data = self.treeiz.GetItemText(item).strip()
                clipdata = wx.TextDataObject()
                clipdata.SetText(data)
                wx.TheClipboard.Open()
                wx.TheClipboard.SetData(clipdata)
                wx.TheClipboard.Close()

    def on_close(self, event):
        self.Destroy()

    def on_sel_tree_changed(self, event):
        item = event.GetItem()
        txt = self.treeiz.GetPyData(item)
        txt = txt.split(":")
        if txt[0] == "1":
            try:
                busy = wx.BusyInfo("Cargando...", self)
                self.carga_list(txt[1])
                del busy
            except Exception, e:
                # print str(e)
                del busy
                wx.MessageBox("Error al comparar. La estructura de la BD es disntina...", APLICACION, wx.ICON_ERROR)

    def carga_tree(self):
        self.treeiz.Freeze()
        self.treeiz.DeleteAllItems()
        font = self.treeiz.GetFont()
        #Por el bug de windows
        if not util.is_windows or util.bits == 64:
            font.SetWeight(wx.BOLD)

        root = self.treeiz.AddRoot("Modificadas")
        self.treeiz.SetPyData(root, "0:root")
        self.treeiz.SetItemFont(root, font)
        if '__WXMSW__' not in wx.Platform:  # peta en windows!!!
            self.treeiz.SetItemImage(root, self.parent.idxlibro, wx.TreeItemIcon_Normal)

        for tabla in sorted(self.data):
            pkey = []
            for k in self.db.get_primary_key(tabla):
                pkey.append(k[0])

            item = self.treeiz.AppendItem(root, tabla)
            key = "1:%s" % tabla
            self.treeiz.SetPyData(item, key)
            if not pkey:
                self.treeiz.SetItemImage(item, self.parent.idxlibroa, wx.TreeItemIcon_Normal)
            elif len(pkey) == 1:
                self.treeiz.SetItemImage(item, self.parent.idxlibrok, wx.TreeItemIcon_Normal)
            else:
                self.treeiz.SetItemImage(item, self.parent.idxlibrok2, wx.TreeItemIcon_Normal)
            self.treeiz.SetItemFont(item, font)

        self.treeiz.Expand(root)
        self.treeiz.Thaw()

    def carga_list(self, tabla):
        if self.tabla_actual != tabla:
            if self.tabla_actual:
                self.list.set_propi_columns(self.tabla_actual)
            self.tabla_actual = tabla

        self.treede.Freeze()
        self.treede.DeleteAllItems()
        self.treede.Thaw()

        campos_tabla = self.db.get_campos(tabla)
        campos = []
        for c in campos_tabla:
            tipo = c[1]
            if tipo != "bytea":
                campos.append(c[0])

        self.list.Freeze()
        self.list.DeleteAllItems()
        self.list.DeleteAllColumns()

        ind = 0
        for reg in sorted(self.data[tabla].items()):
            clave = reg[0]
            accion = reg[1][0]
            reg_antes = reg[1][1]
            reg_nuevo = reg[1][2]

            lantes = len(reg_antes)
            lnuevo = len(reg_nuevo)
            lon = lantes if lantes > lnuevo else lnuevo

            if ind == 0:
                self.list.InsertColumn(0, "Tipo")
                for n in range(0, lon):
                    w = util.get_width_font(self.list, campos[n]) + 15
                    self.list.InsertColumn(n+1, campos[n], width=w)

            for n in range(0, lon):
                nuevo = antes = ""
                if reg_nuevo:
                    nuevo = reg_nuevo[n] if n < lnuevo else "???"
                    nuevo = str(nuevo)

                if reg_antes:
                    antes = reg_antes[n] if n < lantes else "???"
                    antes = str(antes)

                valor = nuevo
                if accion == "BORRA":
                    valor = antes

                if n == 0:
                    #self.list.InsertStringItem(ind, accion) en lugar del texto pongo la imagen+texto
                    if accion == "NUEVO":
                        indice = self.list.InsertImageStringItem(ind, "N", self.parent.idxpverde)
                        self.list.SetItemData(indice, ind)
                    if accion == "MODI":
                        indice = self.list.InsertImageStringItem(ind, "M", self.parent.idxpazul)
                        self.list.SetItemData(indice, ind)
                    if accion == "BORRA":
                        indice = self.list.InsertImageStringItem(ind, "B", self.parent.idxprojo)
                        self.list.SetItemData(indice, ind)
                    self.list.SetStringItem(ind, n+1, valor)
                else:
                    self.list.SetStringItem(ind, n+1, valor)
            self.list.set_color_row(ind)

            if accion == "MODI":
                ind += 1
                for n in range(0, len(reg_antes)):
                    nuevo = antes = ""
                    if reg_nuevo:
                        nuevo = reg_nuevo[n]
                        nuevo = str(nuevo)

                    if reg_antes:
                        antes = reg_antes[n]
                        antes = str(antes)

                    valor = ""
                    if nuevo != antes:
                        valor = u"•" + unicode(antes)

                    if n == 0:
                        #self.list.InsertStringItem(ind, "")
                        indice = self.list.InsertImageStringItem(ind, "", self.parent.idxpazul)
                        self.list.SetItemData(indice, ind)
                        self.list.SetStringItem(ind, n+1, valor)
                    else:
                        self.list.SetStringItem(ind, n+1, valor)
                self.list.set_color_row(ind)
            ind += 1

        for i in range(0, self.list.GetItemCount()):
            item = self.list.GetItem(i, 0)

            tipo = item.GetText()
            if tipo == "N":
                item.SetTextColour(wx.Colour(20, 80, 0))  # verde oscuro
                self.list.SetItem(item)

            elif tipo == "B":
                item.SetTextColour(wx.RED)
                self.list.SetItem(item)

            elif tipo == "M":
                item.SetTextColour(wx.BLUE)
                self.list.SetItem(item)

            else:
                item.SetTextColour(wx.BLACK)
                self.list.SetItem(item)

        if self.list.ItemCount > 0:
            self.list.Select(0)

        self.list.set_size_columns(tabla)
        self.list.Thaw()

    def get_column_text(self, index, col):
        item = self.list.GetItem(index, col)
        return item.GetText()

    def on_item_selected(self, event):
        item = event.m_itemIndex
        tipo = self.list.GetItemText(item)

        if tipo == "N":
            tipo = "Nuevo"
            icon = self.parent.idxpverde
        elif tipo == "B":
            tipo = "Baja"
            icon = self.parent.idxprojo
        else:
            tipo = u"Modificación"
            icon = self.parent.idxpazul

        font = self.treede.GetFont()
        #Por el bug de windows
        if not util.is_windows or util.bits == 64:
            font.SetWeight(wx.BOLD)

        self.treede.Freeze()
        self.treede.DeleteAllItems()

        root = self.treede.AddRoot(tipo)
        self.treede.SetItemFont(root, font)

        self.treede.SetItemImage(root, icon, wx.TreeItemIcon_Normal)

        nom_val = dict()
        #for i in range(0, self.list.GetColumnCount()):
        # empieza por 1 para que no ponga la columna Tipo
        for i in range(1, self.list.GetColumnCount()):
            nom = self.list.GetColumn(i).GetText()
            val = self.get_column_text(item, i)
            nom_val[nom] = val

        for nom, val in sorted(nom_val.iteritems()):
            if len(val) > 150:
                txt = "%s = %s ..." % (nom, val[:150])
            else:
                txt = "%s = %s " % (nom, val)
            txt = txt.replace("\n", " ")
            itemt = self.treede.AppendItem(root, txt)
            self.treede.SetItemImage(itemt, self.parent.idxcam, wx.TreeItemIcon_Normal)

        self.treede.ExpandAll()
        self.treede.Thaw()

