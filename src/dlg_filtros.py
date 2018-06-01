# -*- coding: utf-8 -*-

from constantes import *
from bases import *
from util import *
from dialogos import DlgDefCampo
import codigo


def get_filtros_defecto():
    nombre1 = "Entero"
    valor1 = u"""# Convierte el número a entero

try:
    campo=int(campo)
except:
    campo=0
"""
    nombre2 = "ValidaDNI"
    valor2 = u"""# Chequea el Dni.
# Si no es correcto se interrumpe la importación

dni=campo
tabla = "TRWAGMYFPDXBNJZSQVHLCKE"
dig_ext = "XYZ"
reemp_dig_ext = {'X':'0', 'Y':'1', 'Z':'2'}
numeros = "1234567890"
dni = dni.upper()
if len(dni) == 9:
    dig_control = dni[8]
    dni = dni[:8]
    if dni[0] in dig_ext:
        dni = dni.replace(dni[0], reemp_dig_ext[dni[0]])
    if len(dni) != len([n for n in dni if n in numeros]) or tabla[int(dni)%23] != dig_control:
        raise Exception("DNI incorrecto:%s" % campo)
else:
    raise Exception("DNI incorrecto:%s" % campo)
"""
    nombre3 = "NumeroEs2Py"
    valor3 = u"""# Convierte el número de formato español a python
if campo == "":
    campo = "0"
campo = campo.replace('.',  '').replace(',', '.')
"""

    nombre4 = "FormatoFecha"
    valor4 = u"""# Convierte la fecha a formato postgres.
# Si no es posible asigna "0000-01-01"

resul = "0000-01-01"
tmp = campo.split(" ")
tmp = tmp[0].split("/")
if len(tmp) != 3:
    tmp = campo.split("-")
    if len(tmp) != 3:
        tmp = campo.split(".")

if len(tmp) == 3:
    if len(tmp[0]) == 4:
        resul = "%s-%s-%s" % (tmp[0], tmp[1], tmp[2])
    elif len(tmp[2]) == 4:
        resul = "%s-%s-%s" % (tmp[2], tmp[1], tmp[0])

campo = resul
"""

    return {nombre1: valor1, nombre2: valor2, nombre3: valor3, nombre4: valor4}


class Filtros(BaseSizedDialog):
    def __init__(self, parent, id, titulo, data):
        BaseSizedDialog.__init__(self, parent, id, titulo, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        self.data = data.copy()
        self.tree_cam_item = None
        self.tree_filtro_item = None

        s0 = BaseSplitter(self, "filtros", 300)

        self.tree_cam = wx.TreeCtrl(s0, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HAS_BUTTONS)
        self.tree_cam.SetImageList(parent.imglst)

        self.tree_filtro = wx.TreeCtrl(s0, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HAS_BUTTONS)
        self.tree_filtro.SetImageList(parent.imglst)

        s0.SetMinimumPaneSize(10)
        s0.SplitVertically(self.tree_cam, self.tree_filtro, s0.get_size())

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(s0, 1, wx.EXPAND)
        self.SetSizer(box1)

        self.botones()
        self.set_focus_ctrl(self.tree_cam)
        self.fit()

        self.set_size((800, 600))

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_tree_cam_changed, self.tree_cam)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_tree_filtro_changed, self.tree_filtro)
        self.tree_cam.Bind(wx.EVT_RIGHT_DOWN, self.on_right_tree_cam)
        self.tree_cam.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick_tree_cam)
        self.tree_filtro.Bind(wx.EVT_RIGHT_DOWN, self.on_right_tree_filtro)
        self.tree_filtro.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick_tree_filtro)

        if FILTROS not in self.data:
            filtros = wx.GetApp().get_propiedad(FILTROS)
        else:
            filtros = self.data[FILTROS]

        defecto = get_filtros_defecto()
        if type(filtros) == dict:
            filtros.update(defecto)
        else:
            filtros = defecto

        self.data[FILTROS] = filtros

        if CAMPO_FILTROS not in self.data:
            self.data[CAMPO_FILTROS] = dict()

        self.carga_campos()
        self.carga_filtros()
       
    def carga_campos(self, nom_actual=None):
        item_actual = None
        font = self.tree_cam.GetFont()
        # Por el bug de windows
        if not util.is_windows or util.bits == 64:
            font.SetWeight(wx.BOLD)

        self.tree_cam.DeleteAllItems()
        root = self.tree_cam.AddRoot("Campos")
        self.tree_cam.SetPyData(root, "0:root")
        self.tree_cam.SetItemFont(root, font)
        self.tree_cam.SetItemImage(root, self.parent.idxlibro, wx.TreeItemIcon_Normal)

        if FICHERO_CSV in self.data and "campos" in self.data[FICHERO_CSV]:
            tmp = list()
            for c in sorted(self.data[FICHERO_CSV]["campos"]):
                tmp.append(c)

            for k, v in self.data.iteritems():
                if k.find(CAMPO_DEF) == 0:
                    tmp.append(v["nombre"])

            for c in sorted(tmp):
                hijo = self.tree_cam.AppendItem(root, c)
                self.tree_cam.SetItemImage(hijo, self.parent.idxlibroa, wx.TreeItemIcon_Normal)
                self.tree_cam.SetPyData(hijo, "1:%s" % c)
                if c == nom_actual:
                    item_actual = hijo
                if c in self.data[CAMPO_FILTROS]:
                    for i, f in enumerate(self.data[CAMPO_FILTROS][c]):
                        item = self.tree_cam.AppendItem(hijo, f)
                        self.tree_cam.SetItemImage(item, self.parent.idxcam, wx.TreeItemIcon_Normal)
                        self.tree_cam.SetPyData(item, "3:%s:%s:%s" % (c, f, i))

        self.tree_cam.ExpandAll()
        if item_actual:
            self.tree_cam.SelectItem(item_actual)

    def carga_filtros(self, nom_actual=None):
        item_actual = None
        font = self.tree_cam.GetFont()
        # Por el bug de windows
        if not util.is_windows or util.bits == 64:
            font.SetWeight(wx.BOLD)

        self.tree_filtro.DeleteAllItems()
        root = self.tree_filtro.AddRoot("Filtros")
        self.tree_filtro.SetPyData(root, "0:root")
        self.tree_filtro.SetItemFont(root, font)
        self.tree_filtro.SetItemImage(root, self.parent.idxlibro, wx.TreeItemIcon_Normal)

        if self.data[FILTROS]:
            for f in sorted(self.data[FILTROS].iterkeys()):
                hijo = self.tree_filtro.AppendItem(root, f)
                self.tree_filtro.SetItemImage(hijo, self.parent.idxlibroa, wx.TreeItemIcon_Normal)
                self.tree_filtro.SetPyData(hijo, "1:%s" % f)
                if f == nom_actual:
                    item_actual = hijo

        self.tree_filtro.Expand(root)
        if item_actual:
            self.tree_filtro.SelectItem(item_actual)

    def on_sel_tree_cam_changed(self, event):
        if self.tree_cam.GetRootItem() is not event.GetItem():
            self.tree_cam_item = event.GetItem()
        else:
            self.tree_cam_item = None
        txt = self.tree_cam.GetPyData(self.tree_cam_item)
        self.parent.info(str(txt))

    def on_sel_tree_filtro_changed(self, event):
        if self.tree_filtro.GetRootItem() is not event.GetItem():
            self.tree_filtro_item = event.GetItem()
        else:
            self.tree_filtro_item = None
        txt = self.tree_filtro.GetPyData(self.tree_filtro_item)
        self.parent.info(str(txt))

    def on_right_tree_cam(self, event):
        if not hasattr(self, "camID1"):
            self.camID1 = wx.NewId()

        self.Bind(wx.EVT_MENU, self.on_elimina_filtro, id=self.camID1)

        menu = wx.Menu()
        item1 = wx.MenuItem(menu, self.camID1, u"Eliminar filtro")
        menu.AppendItem(item1)
        item1.Enable(False)

        item = self.tree_cam.GetSelection()
        if item:
            data = self.tree_cam.GetPyData(item).split(":")
            if data[0] == "3":
                item1.Enable(True)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_right_tree_filtro(self, event):
        if not hasattr(self, "filtroID1"):
            self.filtroID1 = wx.NewId()
            self.filtroID2 = wx.NewId()
            self.filtroID3 = wx.NewId()

        self.Bind(wx.EVT_MENU, self.on_nuevo_filtro, id=self.filtroID1)
        self.Bind(wx.EVT_MENU, self.on_edita_filtro, id=self.filtroID2)
        self.Bind(wx.EVT_MENU, self.on_borra_filtro, id=self.filtroID3)

        menu = wx.Menu()
        item1 = wx.MenuItem(menu, self.filtroID1, u"Nuevo filtro")
        menu.AppendItem(item1)
        item2 = wx.MenuItem(menu, self.filtroID2, u"Editar filtro")
        menu.AppendItem(item2)
        item3 = wx.MenuItem(menu, self.filtroID3, u"Eliminar filtro")
        menu.AppendItem(item3)

        item = self.tree_filtro.GetSelection()
        if item:
            data = self.tree_filtro.GetPyData(item).split(":")
            if data[0] == "0" or data[1] in get_filtros_defecto():
                item3.Enable(False)
            self.PopupMenu(menu)
            menu.Destroy()

    def on_dclick_tree_cam(self, event):
        if self.tree_cam_item and self.tree_filtro_item:
            campo = self.tree_cam.GetPyData(self.tree_cam_item).split(":")[1]
            filtro = self.tree_filtro.GetPyData(self.tree_filtro_item).split(":")[1]
            self.asigna_filtro(campo, filtro)

    def on_dclick_tree_filtro(self, event):
        if self.tree_cam_item and self.tree_filtro_item:
            campo = self.tree_cam.GetPyData(self.tree_cam_item).split(":")[1]
            filtro = self.tree_filtro.GetPyData(self.tree_filtro_item).split(":")[1]
            self.asigna_filtro(campo, filtro)

    def on_nuevo_filtro(self, event):
        self.filtro(dict())

    def on_edita_filtro(self, event):
        if self.tree_filtro_item:
            nom = self.tree_filtro.GetPyData(self.tree_filtro_item).split(":")[1]
            self.filtro({"nombre": nom, "valor": self.data[FILTROS][nom]})

    def on_borra_filtro(self, event):
        if self.tree_filtro_item:
            prev = self.tree_filtro.GetPrevSibling(self.tree_filtro_item)
            nom = self.tree_filtro.GetPyData(self.tree_filtro_item).split(":")[1]
            del self.data[FILTROS][nom]
            if prev.IsOk():
                nom = self.tree_filtro.GetPyData(prev).split(":")[1]
            else:
                nom = None
            self.carga_filtros(nom)

    def on_size(self, event):
        self.set_propi_size()
        event.Skip(True)

    def on_elimina_filtro(self, event):
        item = self.tree_cam.GetSelection()
        n, campo, filtro, pos = self.tree_cam.GetPyData(item).split(":")
        del self.data[CAMPO_FILTROS][campo][int(pos)]
        self.carga_campos(campo)

    def filtro(self, data):
        evalua = False
        while not evalua:
            ayuda = u"El valor del csv se asigna a la variable 'campo'\n"
            ayuda += u"para operar con ella, siempre de tipo 'str'.\n"
            ayuda += u"Este cogera el valor que se le asigne en la\ndefinición."
            aceptar = True
            if data and "nombre" in data and data["nombre"] in get_filtros_defecto():
                aceptar = False
            dlg = DlgDefCampo(self, wx.ID_ANY, "Filtro", data, ayuda, False, False, aceptar)
            dlg.CenterOnParent()
            val = dlg.ShowModal()
            if val == wx.ID_OK:
                data = dlg.get_data()
                err = codigo.evalua_codigo("campo", data["valor"], ["campo"], ["0"])
                if err:
                    wx.MessageBox(err, APLICACION, wx.ICON_ERROR, self)
                else:
                    evalua = True
            else:
                break
            dlg.Destroy()

        if evalua:
            self.data[FILTROS][data["nombre"]] = data["valor"]
            self.carga_filtros(data["nombre"])

    def asigna_filtro(self, campo, filtro):
        if campo not in self.data[CAMPO_FILTROS]:
            self.data[CAMPO_FILTROS][campo] = [filtro]
        else:
            self.data[CAMPO_FILTROS][campo].append(filtro)
        self.carga_campos(campo)

    def get_data(self):
        wx.GetApp().set_propiedad(FILTROS, self.data[FILTROS])
        return self.data[FILTROS], self.data[CAMPO_FILTROS]

