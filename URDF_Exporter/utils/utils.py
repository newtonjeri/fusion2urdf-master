# -*- coding: utf-8 -*-
"""
Created on Sun May 12 19:15:34 2019
Modified on Sun Jan 17 2021
Modified on Sun March 30 2025

@author: syuntoku
@author: spacemaster85
@author: newtonjeri
"""

import adsk
import adsk.core
import adsk.fusion
import os.path
import re
from xml.etree import ElementTree
from xml.dom import minidom
import shutil
import fileinput
import sys


def export_stl(_app, save_dir):
    """
    export stl files into "save_dir/meshes/"
    Uses mm units and generates low-resolution meshes

    Parameters
    ----------
    _app: adsk.core.Application.get()
    save_dir: str
        directory path to save
    """
    def traverse(occ):
        # recursive method to get all bodies from components and sub-components
        body = adsk.fusion.BRepBody.cast(None)
        liste = []
        if occ.childOccurrences and occ.isLightBulbOn:
            for child in occ.childOccurrences:
                liste = liste + traverse(child)
        if occ.isLightBulbOn:   
            liste = liste + [body for body in occ.bRepBodies if body.isLightBulbOn and occ.component.isBodiesFolderLightBulbOn]
        return liste

    des: adsk.fusion.Design = _app.activeProduct
    root: adsk.fusion.Component = des.rootComponent

    showBodies = []
    body = adsk.fusion.BRepBody.cast(None)
    if root.isBodiesFolderLightBulbOn:
        lst = [body for body in root.bRepBodies if body.isLightBulbOn]
        if len(lst) > 0:
            showBodies.append(['root', lst])

        occ = adsk.fusion.Occurrence.cast(None)
        for occ in root.allOccurrences:
            if not occ.assemblyContext and occ.isLightBulbOn:
                lst = [body for body in occ.bRepBodies if body.isLightBulbOn and occ.component.isBodiesFolderLightBulbOn]
                if occ.childOccurrences:
                    for child in occ.childOccurrences:
                        lst = lst + traverse(child)
                if len(lst) > 0:
                    showBodies.append([occ.name, lst])

        # get clone body
        tmpBrepMng = adsk.fusion.TemporaryBRepManager.get()
        tmpBodies = []
        for name, bodies in showBodies:
            lst = [tmpBrepMng.copy(body) for body in bodies]
            if len(lst) > 0:
                tmpBodies.append([name, lst])

        # create export Doc - DirectDesign
        fusionDocType = adsk.core.DocumentTypes.FusionDesignDocumentType
        expDoc: adsk.fusion.FusionDocument = _app.documents.add(fusionDocType)
        expDes: adsk.fusion.Design = expDoc.design
        expDes.designType = adsk.fusion.DesignTypes.DirectDesignType

        # get export rootComponent
        expRoot: adsk.fusion.Component = expDes.rootComponent

        # paste clone body
        mat0 = adsk.core.Matrix3D.create()
        for name, bodies in tmpBodies:
            occ = expRoot.occurrences.addNewComponent(mat0)
            comp = occ.component
            comp.name = name
            for body in bodies:
                comp.bRepBodies.add(body)

        # export stl
        try:
            os.mkdir(save_dir + '/meshes')
        except:
            pass
        exportFolder = save_dir + '/meshes'

        exportMgr = des.exportManager
        for occ in expRoot.allOccurrences:
            if "base_link" in occ.component.name:
                expName = "base_link"
            else:
                expName = re.sub('[ :()]', '_', occ.component.name)
            expPath = os.path.join(exportFolder, '{}.stl'.format(expName))
            stlOpts = exportMgr.createSTLExportOptions(occ, expPath)
            
            # Set to lowest resolution mesh
            stlOpts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementLow
            stlOpts.isBinaryFormat = True  # Binary format for smaller files
            
            # Since we're working in mm, but URDF expects meters, we'll handle scaling in the URDF
            stlOpts.isUnitInMeter = False  # Keep original mm units in STL
            exportMgr.execute(stlOpts)

        # remove export Doc
        expDoc.close(False)

def file_dialog(ui):
    """
    display the dialog to save the file
    """
    # Set styles of folder dialog.
    folderDlg = ui.createFolderDialog()
    folderDlg.title = 'Fusion Folder Dialog'

    # Show folder dialog
    dlgResult = folderDlg.showDialog()
    if dlgResult == adsk.core.DialogResults.DialogOK:
        return folderDlg.folder
    return False

def origin2center_of_mass(inertia, center_of_mass, mass):
    """
    convert the moment of the inertia about the world coordinate into
    that about center of mass coordinate

    Parameters
    ----------
    moment of inertia about the world coordinate:  [xx, yy, zz, xy, yz, xz]
    center_of_mass: [x, y, z]
    mass: float

    Returns
    ----------
    moment of inertia about center of mass : [xx, yy, zz, xy, yz, xz]
    """
    x = center_of_mass[0]
    y = center_of_mass[1]
    z = center_of_mass[2]
    translation_matrix = [y**2 + z**2, x**2 + z**2, x**2 + y**2,
                        -x*y, -y*z, -x*z]
    
    # Calculate without rounding first
    result = [i - mass*t for i, t in zip(inertia, translation_matrix)]
    
    # Format with maximum precision while preserving small values
    formatted_result = []
    for val in result:
        if abs(val) < 1e-10 and val != 0:
            # Use scientific notation for very small values
            formatted_result.append(float("{:.15e}".format(val)))
        else:
            # Use maximum precision for larger values
            formatted_result.append(float("{:.15g}".format(val)))
    
    return formatted_result


def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.
    Parameters
    ----------
    elem : xml.etree.ElementTree.Element


    Returns
    ----------
    pretified xml : str
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def copy_package(save_dir, package_dir):
    try:
        os.mkdir(save_dir + '/launch')
    except:
        pass
    try:
        os.mkdir(save_dir + '/urdf')
    except:
        pass
    # shutil.copytree(package_dir, save_dir)
    shutil.copytree(package_dir, save_dir, dirs_exist_ok=True)



def update_cmakelists(save_dir, package_name):
    file_name = save_dir + '/CMakeLists.txt'

    for line in fileinput.input(file_name, inplace=True):
        if 'project(fusion2urdf)' in line:
            sys.stdout.write("project(" + package_name + ")\n")
        else:
            sys.stdout.write(line)

def update_ros2_launchfile(save_dir, package_name):
    file_name = save_dir + '/launch/robot_description.launch.py'

    for line in fileinput.input(file_name, inplace=True):
        if 'fusion2urdf' in line:
            sys.stdout.write(line.replace('fusion2urdf', package_name))
        else:
            sys.stdout.write(line)

def update_package_xml(save_dir, package_name):
    file_name = save_dir + '/package.xml'

    for line in fileinput.input(file_name, inplace=True):
        if '<name>' in line:
            sys.stdout.write("  <name>" + package_name + "</name>\n")
        elif '<description>' in line:
            sys.stdout.write("<description>The " +
                             package_name + " package</description>\n")
        else:
            sys.stdout.write(line)
