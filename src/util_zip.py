# coding=utf-8
import os
import shutil
import tempfile
import zipfile


class Zip(object):
    def __init__(self, nombre_fichero_zip, path_zip=None):
        """Crea fichero zip

        :param nombre_fichero_zip: str, nombre del fichero sin extensión
        :param path_zip:  str, path opcional
        """
        self.__ficheros = []
        self.__paths = []
        self.__nombre = nombre_fichero_zip
        self.__path = path_zip
        self.__usa_temp = False
        if not path_zip:
            self.__path = tempfile.mkdtemp()
            self.__usa_temp = True

    def __del__(self):
        if self.__usa_temp:
            shutil.rmtree(self.__path, True)

    def __crea(self):
        zipf = zipfile.ZipFile(self.path_nombre_zip, 'w')
        for f1, f2, borra in self.__ficheros:
            zipf.write(f1, f2)
            if borra:
                os.remove(f1)
        zipf.close()

        for p, borra in self.__paths:
            if borra:
                shutil.rmtree(p, ignore_errors=True)

    def __mkdir_recursive(self, path):
        sub_path = os.path.dirname(path)
        if not os.path.exists(sub_path):
            self.__mkdir_recursive(sub_path)
        if not os.path.exists(path):
            os.mkdir(path)

    @property
    def path_nombre_zip(self):
        """Retorna nombre completo, path+fichero+extensión


        :return: str
        """
        return os.path.join(self.__path, self.__nombre)

    @property
    def path_zip(self):
        """Retorna path del zip


        :return: str
        """
        return self.__path

    @path_zip.setter
    def path_zip(self, path):
        """Asigna path del zip

        :param path:
        """
        self.__path = path

    def push(self, path_nombre_org, path_nombre_des=None, borrar=False):
        """Añade fichero al zip,

        :param path_nombre_org: str, path+nombre completo del fichero origen
        :param nombre_des: str, nombre del path+fichero destino, si se omite el origen sin el path
        :param borra: boleano, si borra o nó el fichero origen
        """
        if not path_nombre_des:
            path_nombre_des = os.path.basename(path_nombre_org)
            nom_en_zip = path_nombre_des
        else:
            if path_nombre_des.startswith(os.sep):
                path_nombre_des = path_nombre_des[len(os.sep):]
            nom_en_zip = path_nombre_des
            path_nombre_des = os.path.join(self.__path, path_nombre_des)
            self.__mkdir_recursive(os.path.dirname(path_nombre_des))

        self.__ficheros.append([path_nombre_org, nom_en_zip, borrar])

    def push_path(self, path_org, path_des=None, borrar=False):
        self.__paths.append([path_org, borrar])

        if not path_des:
            path_des = path_org
        if path_des.startswith(os.sep):
            path_des = path_des[len(os.sep):]

        for root, dirs, files in os.walk(path_org):
            for f in files:
                nom = os.path.join(root, f)
                nom_en_zip = nom[len(path_org):]
                if nom_en_zip.startswith(os.sep):
                    nom_en_zip = nom_en_zip[len(os.sep):]
                nom_en_zip= os.path.join(path_des, nom_en_zip)
                self.__ficheros.append([nom, nom_en_zip, False])

    def fichero(self):
        """Crea zip y retorna fichero zip (path+nombre+extensión)


        :return: str
        """
        self.__crea()
        return self.path_nombre_zip

    def extrae(self, path_destino):
        """Extrae el fichero en el path indicado

        :param path_destino: str
        :return: Nones si no hay error y str si lo hay
        """
        try:
            with zipfile.ZipFile(self.__nombre, "r") as z:
                z.extractall(path_destino)
            return None

        except zipfile.BadZipfile, e:
            return e