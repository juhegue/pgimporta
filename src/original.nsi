;--------------------------------
;Include Modern UI

    !include "MUI2.nsh"
    !include "x64.nsh"

;-------------------------------
; Iconos del instalador

    !define MUI_ICON "pgimporta.ico"
    !define MUI_HEADERIMAGE
    !define MUI_HEADERIMAGE_BITMAP "pgimporta.bmp"
    !define MUI_HEADERIMAGE_RIGHT

;--------------------------------
;General
    !define APP "pgimporta"
    !define DES "Importar datos a DB postgres"
    !define EMP "Juhegue"

    ;Name and file
    Name "${DES}"
    OutFile "${APP}_install.exe"

    ;Default installation folder.  No se usa ya que enla funcion .onInit se asigna
;   InstallDir "$PROGRAMFILES64\${APP}"

    ;Get installation folder from registry if available
    InstallDirRegKey HKCU "Software\${EMP}\${APP}" ""

    ;Request application privileges for Windows Vista
    RequestExecutionLevel admin

;--------------------------------
;Obtiene el path de instalacion

    Function .onInit
        ${If} $InstDir == ""
            ${If} ${RunningX64}
                StrCpy $InstDir "$ProgramFiles64\${EMP}\${APP}"
            ${Else}
                StrCpy $InstDir "$ProgramFiles32\${EMP}\${APP}"
            ${EndIf}
        ${EndIf}
    FunctionEnd

;--------------------------------
;Interface Settings

    !define MUI_ABORTWARNING

;--------------------------------
;Pages

    !insertmacro MUI_PAGE_DIRECTORY
    !insertmacro MUI_PAGE_INSTFILES

    !insertmacro MUI_UNPAGE_CONFIRM
    !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

    !insertmacro MUI_LANGUAGE "Spanish"

;--------------------------------
;Installer Sections

Section "Dummy Section" SecDummy

    SetOutPath "$INSTDIR"

    ${If} ${RunningX64}

__FIC_INSTALL__

    ${Else}
        File "32\${APP}.exe"
        File "32\${APP}.ico"
    ${EndIf}

    CreateShortCut "$DESKTOP\${APP}.lnk" "$INSTDIR\${APP}.exe" "" "$INSTDIR\${APP}.ico"

    CreateDirectory "$SMPROGRAMS\${EMP}"
    CreateDirectory "$SMPROGRAMS\${EMP}\${APP}"
    CreateShortCut "$SMPROGRAMS\${EMP}\${APP}\${APP}.lnk" "$INSTDIR\${APP}.exe" "" "$INSTDIR\${APP}.ico"
    CreateShortCut "$SMPROGRAMS\${EMP}\${APP}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0

    ;Store installation folder
    WriteRegStr HKCU "Software\${EMP}\${APP}" "" $INSTDIR

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd


Section "Ejemplos Section" Examples

    SetOutPath "$INSTDIR\ejemplos"

    File "..\ejemplos\articulos.csv"
    File "..\ejemplos\articulos.pgi"
    File "..\ejemplos\pgimporta.pdf"

SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"

    ${If} ${RunningX64}

__FIC_UNINSTALL__

    ${Else}
        Delete "$INSTDIR\${APP}.exe"
        Delete "$INSTDIR\${APP}.ico"
    ${EndIf}

    Delete "$INSTDIR\pgimporta.log"

    Delete "$INSTDIR\ejemplos\articulos.csv"
    Delete "$INSTDIR\ejemplos\articulos.pgi"
    Delete "$INSTDIR\ejemplos\pgimporta.pdf"

    Delete "$INSTDIR\Uninstall.exe"

    RMDir "$INSTDIR\ejemplos"
    RMDir "$INSTDIR"

    DeleteRegKey /ifempty HKCU "Software\${EMP}\${APP}"

    Delete "$DESKTOP\${APP}.lnk"

    Delete "$SMPROGRAMS\${EMP}\${APP}\${APP}.lnk"
    Delete "$SMPROGRAMS\${EMP}\${APP}\Uninstall.lnk"
    RMDIR  "$SMPROGRAMS\${EMP}\${APP}"
    RMDIR  "$SMPROGRAMS\${EMP}"

SectionEnd