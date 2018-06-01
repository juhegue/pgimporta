import os

lista = [
        "img2py -F    -i -n importar        pgimporta48.png     imagenes.py",
        "img2py -F -a -i -n libro		    libro.png	 	    imagenes.py",
        "img2py -F -a -i -n libro_azul	    libro_azul.png	    imagenes.py",
        "img2py -F -a -i -n libro_verde     libro_verde.png	    imagenes.py",
        "img2py -F -a -i -n libro_azul_key  libro_azul_key.png  imagenes.py",
        "img2py -F -a -i -n libro_azul_key2 libro_azul_key2.png imagenes.py",
        "img2py -F -a -i -n key             key.png             imagenes.py",
        "img2py -F -a -i -n db1			    db1.png 		    imagenes.py",
        "img2py -F -a -i -n db2			    db2.png 		    imagenes.py",
        "img2py -F -a -i -n db3			    db3.png 		    imagenes.py",
        "img2py -F -a -i -n pazul		    pazul.bmp		    imagenes.py",
        "img2py -F -a -i -n projo 		    projo.bmp 		    imagenes.py",
        "img2py -F -a -i -n pverde 		    pverde.bmp 		    imagenes.py",
        "img2py -F -a -i -n refrescar	    refrescar.png	    imagenes.py",
        "img2py -F -a -i -n process 	    process.png		    imagenes.py",
        "img2py -F -a -i -n smiles 		    smiles.png		    imagenes.py",
        "img2py -F -a -i -n miscellaneous   miscellaneous.png   imagenes.py",
        "img2py -F -a -i -n sql             sql.png             imagenes.py",
        "img2py -F -a -i -n cuadro          cuadro.png          imagenes.py",
        "img2py -F -a -i -n flecha          flecha.png          imagenes.py",
        "img2py -F -a -i -n flechaarriba    flechaarriba.png    imagenes.py",
        "img2py -F -a -i -n flechaabajo     flechaabajo.png     imagenes.py",
        "img2py -F -a -i -n info            info.png            imagenes.py",
        "img2py -F -a -i -n python          python.png          imagenes.py",
        "img2py -F -a -i -n flechaup        flechaup.png        imagenes.py",
        "img2py -F -a -i -n flechadown      flechadown.png      imagenes.py",
        "img2py -F -a -i -n csv             csv.png             imagenes.py",
        "img2py -F -a -i -n refresh  	    refresh.png	        imagenes.py",
        "img2py -F -a -i -n asigna   	    asigna.png	        imagenes.py",
        "img2py -F -a -i -n marca    	    marca.png	        imagenes.py",
        "img2py -F -a -i -n marcaa    	    marcaa.png	        imagenes.py",
]

for p in lista:
    os.system(p)

raw_input("Pulsa 'Enter':")