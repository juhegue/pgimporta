# -*- coding: utf-8 -*-

from parse_select import parse_select
from constantes import *
from bases import *
from popup import show_popup
from dialogos import dialogo_grabar_fic
from csvunicode import UnicodeWriter


VALOR_ID_VACIA = u"•••"


class FrmSql(BaseFrame):
    sql_list = list()

    def __init__(self, parent, id, sql):
        BaseFrame.__init__(self, parent, id, parent.app.GetAppName() + " (SQL)", (800, 600),
                           style=wx.DEFAULT_FRAME_STYLE)  # | wx.STAY_ON_TOP
        self.parent = parent
        self.sql = sql
        self.tablas = None
        self.pkey = None
        self.index = None
        self.vacio = list()
        self.data = dict()
        self.cargando = False

        self.SetIcon(parent.GetIcon())
#--
        p0 = wx.Panel(self, style=wx.BORDER_THEME)
        self.st = wx.StaticText(p0, wx.ID_ANY, "Sql: ")
        self.cb_sql = wx.ComboBox(p0, wx.ID_ANY, "", choices=[], style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)

        bmp = imagenes.refrescar.GetBitmap()
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn1 = wx.BitmapButton(p0, wx.ID_ANY, bmp, (20, 20), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn1.SetToolTipString("Refrescar sql")

        bmp = imagenes.info.GetBitmap()
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn2 = wx.BitmapButton(p0, wx.ID_ANY, bmp, (20, 20), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn2.SetToolTipString("Ayuda")

        bmp = imagenes.csv.GetBitmap()
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn3 = wx.BitmapButton(p0, wx.ID_ANY, bmp, (20, 20), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn3.SetToolTipString("Exportar csv (utf8)")

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add((5,5), 0, wx.ALL, border=2)
        box.Add(self.st, 0, wx.ALIGN_CENTER, border=5)
        box.Add(self.cb_sql, 1, wx.ALIGN_CENTER, border=5)
        box.Add(btn1, 0, wx.ALL, border=5)
        box.Add(btn3, 0, wx.ALL, border=5)
        box.Add(btn2, 0, wx.ALL, border=5)
        p0.SetSizer(box)
#--
        s0 = BaseSplitter(self, "central", 300)
        p1 = wx.Panel(s0, style=wx.BORDER_THEME)
        p2 = wx.Panel(s0, style=wx.BORDER_THEME)
        s0.SetMinimumPaneSize(10)
        s0.SplitVertically(p1, p2, s0.get_size())

        b1 = wx.BoxSizer()
        b2 = wx.BoxSizer()

        p1.SetSizer(b1)
        p2.SetSizer(b2)

        self.list = BaseEditListCtrl(p1, wx.ID_ANY, style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_HRULES |
                                     wx.LC_VRULES | wx.LC_SINGLE_SEL)

        b1.Add(self.list, 1, wx.EXPAND)

        self.tree = wx.TreeCtrl(p2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HAS_BUTTONS)
        self.tree.SetImageList(parent.imglst)
        b2.Add(self.tree, 1, wx.EXPAND)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(p0, 0, wx.EXPAND)
        box1.Add(s0, 1, wx.EXPAND)
        self.SetSizer(box1)
        self.sb = self.CreateStatusBar(style=wx.ST_SIZEGRIP)
#--
        self.carga(sql)

        # Restaura el tamaño del frame
        self.set_size((800, 600))

        # Función que se ejecuta al pulsar enter en el editor del ListCtrl
        self.list.set_callback_enter(self.on_enter)

        self.Bind(wx.EVT_TEXT_ENTER, self.on_refresca)
        # en windows no va bien
        # self.Bind(wx.EVT_COMBOBOX, self.on_refresca, self.cb_sql)
        self.Bind(wx.EVT_BUTTON, self.on_refresca, btn1)
        self.Bind(wx.EVT_BUTTON, self.on_ayuda, btn2)
        self.Bind(wx.EVT_BUTTON, self.on_csv, btn3)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected, self.list)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.on_col_end_drag, self.list)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.on_begin_label_edit, self.list)
        #self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down, self.list)
        self.list.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
        self.tree.Bind(wx.EVT_KEY_DOWN, self.on_tree_keydown)

        if self.list.ItemCount > 0:
            self.list.Select(0)

    def es_modificable(self, borrar=False):
        if self.tablas == "@TABLAS":
            return False

        if self.tablas and len(self.tablas) != 1:
            return False

        if not self.pkey:
            return False

        if self.list.GetColumnCount() == 1 and not borrar:
            return False

        update = False
        for i in range(0, self.list.GetColumnCount()):
            nom = self.list.GetColumn(i).GetText()
            if nom == self.pkey:
                update = True

        if not update:
            return False

        return True

    def on_begin_label_edit(self, event):
        if not self.es_modificable():
            event.Veto()
            return

        nom = self.list.GetColumn(event.m_col).GetText()
        if nom == self.pkey:
            event.Veto()
        else:
            event.Skip()

    def on_right_down(self, event):
        if not hasattr(self, "ID1"):
            self.ID1 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_list_borrar, id=self.ID1)

        menu = wx.Menu()
        item1 = wx.MenuItem(menu, self.ID1, "Borrar registro")
        menu.AppendItem(item1)

        if not self.es_modificable(True):
            item1.Enable(False)

        if self.es_modificable():
            if self.list.get_data_row(self.index)[self.column_id] == VALOR_ID_VACIA:
                item1.Enable(False)

        if self.list.GetItemCount() <= 1:
            item1.Enable(False)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_list_borrar(self, event):
        index = self.index
        cam_keys = list()
        for i in range(0, self.list.GetColumnCount()):
            nom = self.list.GetColumn(i).GetText()
            if nom == self.pkey:
                cam_keys.append("%s='%s'" % (nom, self.list.GetItem(index, i).GetText()))

        txt = u"¿Borrar registro %s?" % ", ".join(cam_keys)
        dlg1 = wx.MessageDialog(self, txt, self.GetTitle(), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if dlg1.ShowModal() == wx.ID_YES:
            db = self.parent.db
            tabla = self.tablas[0]
            sql = "DELETE FROM %s WHERE %s" % (tabla, ", ".join(cam_keys))
            db.ejecuta(sql)
            if db.error:
                wx.MessageBox("%s\n%s" % (db.error, sql), APLICACION, wx.ICON_ERROR, self)
                return False
            else:
                self.list.del_row(index)
        self.info()
        dlg1.Destroy()

    def carga(self, sql_org):
        if self.cargando:
            return
        self.cargando = True

        db = self.parent.db
        self.tablas = None
        self.pkey = None
        self.data = dict()

        def add_sql_combo(sql=None):
            if sql:
                if sql not in self.sql_list:
                    self.sql_list.insert(0,sql)

            self.cb_sql.Clear()
            for s in self.sql_list:
                self.cb_sql.Append(s)

            if sql:
                self.cb_sql.SetValue(sql)

        if not sql_org:
            add_sql_combo()
            self.list.Freeze()
            self.list.clear()
            self.list.set_columnas([""])
            self.list.set_data({})
            self.list.Thaw()
        else:
            if "@TABLAS" in sql_org:
                ini = sql_org.strip().upper().find("SELECT")
                fin = sql_org.strip().upper().find("FROM")
                if ini < 0 or fin < 0:
                    wx.MessageBox("Con '@TABLAS' solo se permite 'SELECT'.", self.GetTitle(), wx.ICON_ERROR)
                    self.cargando = False
                    return

                campos = sql_org[ini+6:fin].strip()
                if campos.strip() == "*":
                    wx.MessageBox("Con '@TABLAS' debe de informar los campos a mostrar.'.", self.GetTitle(), wx.ICON_ERROR)
                    self.cargando = False
                    return

                campos_tabla = list()
                fila = 0
                busy = wx.BusyInfo("Cargando...", self)
                for i, tabla in enumerate(db.get_tablas()):
                    sql = sql_org.replace("@TABLAS", tabla)
                    try:
                        tabla, campos, sql = parse_select(db, sql, False)
                    except Exception as e:
                        # print e
                        del busy
                        self.cargando = False
                        return

                    cursor = db.ejecuta_many(sql)
                    if cursor:
                        for reg in db.resul_iter(cursor):
                            valores = [tabla[0]]
                            for col in range(0, len(campos)):
                                txt = reg[col]
                                if type(txt) == str:
                                    txt = txt.decode("utf-8")
                                valores.append(txt)
                            self.data[fila] = valores
                            fila += 1
                    wx.Yield()
                    if i == 0:
                        add_sql_combo(sql_org)
                        campos_tabla = campos[:]
                        campos_tabla.insert(0, "tabla")

                # Inicialización del ListCtrl
                self.list.Freeze()
                self.list.clear()
                self.list.set_columnas(campos_tabla)
                self.list.set_data(self.data)
                self.list.Thaw()
                self.list.set_size_columns("@TABLAS")
                self.tablas = "@TABLAS"
                del busy
            else:
                tablas, campos, sql = parse_select(db, sql_org, False)
                if db.error:
                    wx.MessageBox(db.error, self.parent.app.GetAppName(), wx.ICON_ERROR, self)
                    self.cargando = False
                    return

                self.tablas = tablas
                if tablas:
                    for k in db.get_primary_key(tablas[0]):
                        self.pkey = k[0]

                busy = wx.BusyInfo("Cargando...", self)
                wx.Yield()
                cursor = db.ejecuta_many(sql)
                fila = 0
                if cursor:
                    for fila, reg in enumerate(db.resul_iter(cursor)):
                        if fila % 100 == 0: wx.Yield()
                        valores = []
                        for col in range(0, len(campos)):
                            txt = reg[col]
                            if type(txt) == str:
                                txt = txt.decode("utf-8")
                            valores.append(txt)
                        self.data[fila] = valores

                    add_sql_combo(sql_org)

                if campos:
                    indice = 0
                    for i, c in enumerate(campos):
                        if c == self.pkey:
                            indice = i
                    self.vacio = list()
                    for col in range(0, len(campos)):
                        self.vacio.append("")
                    self.vacio[indice] = VALOR_ID_VACIA
                    self.data[fila + 1] = self.vacio[:]

                wx.Yield()
                # Inicialización del ListCtrl
                self.list.Freeze()
                self.list.clear()
                self.list.set_columnas(campos)
                self.list.set_data(self.data)
                self.list.Thaw()
                if self.tablas:
                    self.list.set_size_columns("".join(self.tablas))

                del busy

                if db.error:
                    err = "%s%s" % (db.error, sql)
                    wx.MessageBox(err, self.parent.app.GetAppName(), wx.ICON_ERROR, self)
        self.info()
        self.cargando = False

    def info(self):
        if self.es_modificable():
            num = "{:,}".format(self.list.GetItemCount() - 1)
        else:
            num = "{:,}".format(self.list.GetItemCount())
        self.SetStatusText("Registros: %s" % num, 0)

    def on_size(self, event):
        valor = self.GetSizeTuple()
        if valor[0] < 200 or valor[1] < 200:
            return

        self.set_propi_size()
        event.Skip(True)

    def on_col_end_drag(self, event):
        if self.tablas:
            self.list.set_propi_columns("".join(self.tablas))

    def on_tree_keydown(self, event):
        key = event.KeyCode
        if event.ControlDown() and key in (ord('C'), ord('C')):
            item = self.tree.GetSelection()
            if item.IsOk():
                data = self.tree.GetItemText(item).strip()
                clipdata = wx.TextDataObject()
                clipdata.SetText(data)
                wx.TheClipboard.Open()
                wx.TheClipboard.SetData(clipdata)
                wx.TheClipboard.Close()

    def on_close(self, event):
        self.Destroy()

    def on_ayuda(self, event):
        txt = u"Se puede indicar cualquier sql válida.\n"
        txt += "Si en la tabla se informa @TABLAS se realizará\n"
        txt += "la sql para todas las tablas de la BD,\n"
        txt += "en este caso no se informará de ningún error."
        show_popup(self, event, txt)

    def on_csv(self, event):
        f = dialogo_grabar_fic(self, "csv", "Archivos csv (*.csv)|*.csv|Todos los archivos (*.*)|*", "")
        if f:
            maximo = self.list.GetItemCount()
            dlg = wx.ProgressDialog("Exportando datos", "Exportar", maximum=maximo, parent=self,
                                    style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME
                                          | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)
            dlg.SetIcon(imagenes.importar.GetIcon())
            try:
                column_id = self.column_id
                nombres = list()
                for i in range(0, self.list.GetColumnCount()):
                    nombres.append(self.list.GetColumn(i).GetText())

                delimitador = str(self.parent.data[FICHERO_CSV]["delimitador"])
                with open(f, 'wb') as f1:
                    w = UnicodeWriter(f1, encoding="utf-8", delimiter=delimitador, quotechar='"')
                    w.writerow(nombres)
                    for i in range(0, self.list.GetItemCount()):
                        (sigue, salta) = dlg.Update(i, u"línea:%d" % i)
                        if not sigue:
                            break
                        nuevo = list()
                        for j in range(0, self.list.GetColumnCount()):
                            nuevo.append(self.list.GetItem(i, j).GetText())

                        if nuevo[column_id] != VALOR_ID_VACIA:
                            w.writerow(nuevo)

                        if i % 100 == 0: wx.Yield()
            except Exception, e:
                wx.MessageBox(e.message, APLICACION, wx.ICON_ERROR)

            finally:
                dlg.Update(maximo)
                dlg.Destroy()

    def on_refresca(self, event):
        sql = self.cb_sql.GetValue()
        self.carga(sql)
        if self.list.ItemCount > 0:
            self.list.Select(0)

    def get_column_text(self, index, col):
        item = self.list.GetItem(index, col)
        return item.GetText()

    @property
    def column_id(self):
        for i in range(0, self.list.GetColumnCount()):
            nom = self.list.GetColumn(i).GetText()
            if nom == self.pkey:
                return i
        return 0

    def on_item_selected(self, event):
        self.index = event.m_itemIndex
        self.carga_tree(self.index)

    def carga_tree(self, index):
        icon = self.parent.idxpropi

        font = self.tree.GetFont()
        #Por el bug de windows
        if not util.is_windows or util.bits == 64:
            font.SetWeight(wx.BOLD)

        self.tree.DeleteAllItems()

        if self.es_modificable():
            if self.list.get_data_row(self.index)[self.column_id] == VALOR_ID_VACIA:
                return

        self.tree.Freeze()
        root = self.tree.AddRoot("Campos")
        self.tree.SetItemFont(root, font)

        self.tree.SetItemImage(root, icon, wx.TreeItemIcon_Normal)

        campos = dict()
        for i in range(0, self.list.GetColumnCount()):
            nom = self.list.GetColumn(i).GetText()
            val = self.get_column_text(index, i)
            campos[nom] = val

        for k, v in sorted(campos.iteritems()):
            if len(v) > 150:
                txt = "%s = %s ..." % (k, v[:150])
            else:
                txt = "%s = %s " % (k, v)
            txt = txt.replace("\n", " ")
            itemt = self.tree.AppendItem(root, txt)
            self.tree.SetItemImage(itemt, self.parent.idxcam, wx.TreeItemIcon_Normal)

        self.tree.ExpandAll()
        self.tree.Thaw()

    def on_enter(self, data):
        insert = None
        tabla = self.tablas[0]
        db = self.parent.db

        valores = []
        cam_update = []
        con_update = []
        cam_inser = []
        val_inser = []
        for i in range(0, self.list.GetColumnCount()):
            nom = self.list.GetColumn(i).GetText()
            val = data[i]

            if nom == self.pkey:
                if val == VALOR_ID_VACIA:
                    insert = i
                else:
                    con_update.append("\"%s\"='%s'" % (nom, val))

            if val != "None":
                cam_update.append((nom, val))

                if nom != self.pkey and val:
                    cam_inser.append('"%s"' % nom)
                    val_inser.append("'%s'" % val)

            valores.append(val)

        nuevo_cam = list()
        for n, v in cam_update:
            if v is not None:
                nuevo_cam.append("\"%s\"='%s'" % (n, v))

        cam_update = ",".join(nuevo_cam)
        con_update = " AND ".join(con_update)

        cam_inser = ",".join(cam_inser)
        val_inser = ",".join(val_inser)

        if insert is not None:
            sql = "INSERT INTO %s (%s) VALUES (%s) RETURNING %s" % (tabla, cam_inser, val_inser, self.pkey)
        else:
            sql = "UPDATE %s SET %s WHERE %s" % (tabla, cam_update, con_update)

        resul = db.ejecuta(sql)
        if db.error:
            wx.MessageBox("%s\n%s" % (db.error, sql), APLICACION, wx.ICON_ERROR, self)
            return False
        else:
            if insert is not None:
                data[insert] = resul[0][0]
                self.list.set_last_row(data)
                self.list.append_row(self.vacio)

                ind = self.list.GetItemCount()-1
                self.list.Select(ind)
                self.list.EnsureVisible(ind)

        self.info()
        return True
