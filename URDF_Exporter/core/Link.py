# -*- coding: utf-8 -*-
"""
Created on Sun May 12 20:11:28 2019
Modified on Sun Jan 17 2021
Modified on Sun March 30 2025

@author: syuntoku
@author: spacemaster85
@author: newtonjeri
"""

import adsk, re, traceback
from xml.etree.ElementTree import Element, SubElement
from ..utils import utils

class Link:

    def __init__(self, name, xyz, center_of_mass, repo, mass, inertia_tensor, material):
        """
        Parameters
        ----------
        name: str
            name of the link
        xyz: [x, y, z]
            coordinate for the visual and collision
        center_of_mass: [x, y, z]
            coordinate for the center of mass
        link_xml: str
            generated xml describing about the link
        repo: str
            the name of the repository to save the xml file
        mass: float
            mass of the link
        inertia_tensor: [ixx, iyy, izz, ixy, iyz, ixz]
            tensor of the inertia
        """
        self.name = name
        # xyz for visual
        self.xyz = [-_ for _ in xyz]  # reverse the sign of xyz
        # xyz for center of mass
        self.center_of_mass = center_of_mass
        self.link_xml = None
        self.repo = repo
        self.mass = mass
        self.inertia_tensor = inertia_tensor
        self.material = material

    def make_link_xml(self):
        """
        Generate the link_xml and hold it by self.link_xml
        """

        link = Element('link')
        link.attrib = {'name':self.name}
        
        # inertial (unchanged)
        inertial = SubElement(link, 'inertial')
        origin_i = SubElement(inertial, 'origin')
        origin_i.attrib = {'xyz':' '.join([str(_) for _ in self.center_of_mass]), 'rpy':'0 0 0'}       
        mass = SubElement(inertial, 'mass')
        mass.attrib = {'value':str(self.mass)}
        inertia = SubElement(inertial, 'inertia')
        inertia.attrib = \
            {'ixx':str(self.inertia_tensor[0]), 'iyy':str(self.inertia_tensor[1]),\
            'izz':str(self.inertia_tensor[2]), 'ixy':str(self.inertia_tensor[3]),\
            'iyz':str(self.inertia_tensor[4]), 'ixz':str(self.inertia_tensor[5])}       
        
        # visual
        visual = SubElement(link, 'visual')
        origin_v = SubElement(visual, 'origin')
        origin_v.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':'0 0 0'}
        geometry_v = SubElement(visual, 'geometry')
        mesh_v = SubElement(geometry_v, 'mesh')
        mesh_v.attrib = {'filename':'package://' + self.repo + self.name + '.stl','scale':'0.001 0.001 0.001'}  # mm to m conversion
        material = SubElement(visual, 'material')
        material.attrib = {'name': self.material}
        
        # collision
        collision = SubElement(link, 'collision')
        origin_c = SubElement(collision, 'origin')
        origin_c.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':'0 0 0'}
        geometry_c = SubElement(collision, 'geometry')
        mesh_c = SubElement(geometry_c, 'mesh')
        mesh_c.attrib = {'filename':'package://' + self.repo + self.name + '.stl','scale':'0.001 0.001 0.001'}  # mm to m conversion

        self.link_xml = "\n".join(utils.prettify(link).split("\n")[1:])

def make_inertial_dict(root, msg):
    allOccs = root.occurrences
    inertial_dict = {}
    
    def format_float(value):
        if abs(value) < 1e-10 and value != 0:
            return "{:.15e}".format(value)
        return "{:.15g}".format(value)
        
    for occs in allOccs:
        occs_dict = {}
        prop = occs.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
        
        occs_dict['name'] = re.sub('[ :()]', '_', occs.name)
        mass = prop.mass  # kg
        occs_dict['mass'] = format_float(mass)
        occs_dict['mass_float'] = mass
        
        # Convert mm to m for center of mass
        center_of_mass = [_/100.0 for _ in prop.centerOfMass.asArray()]
        occs_dict['center_of_mass'] = [format_float(x) for x in center_of_mass]
        occs_dict['center_of_mass_float'] = center_of_mass

        (_, xx, yy, zz, xy, yz, xz) = prop.getXYZMomentsOfInertia()
        moment_inertia_world = [xx/1e4, yy/1e4, zz/1e4, xy/1e4, yz/1e4, xz/1e4]
        moment_inertia_com = utils.origin2center_of_mass(
                moment_inertia_world, 
                center_of_mass, 
                mass
            )
        
        occs_dict['inertia'] = [format_float(x) for x in moment_inertia_com]
        occs_dict['inertia_float'] = moment_inertia_com
        
        if 'base_link' in occs.component.name:
            inertial_dict['base_link'] = occs_dict
        else:
            inertial_dict[re.sub('[ :()]', '_', occs.name)] = occs_dict

    return inertial_dict, msg

def make_material_dict(root, msg):
    """      
    Parameters
    ----------
    root: adsk.fusion.Design.cast(product)
        Root component
    msg: str
        Tell the status
        
    Returns
    ----------
    Material_dict: {component_name:material}
    color_dict: {material_name:rgba string}   
    msg: str
        Tell the status 
    """
    def convert_german(str_in):
        str_in = str_in.replace('ä', 'ae')
        str_in = str_in.replace( 'ö', 'oe')
        str_in = str_in.replace( 'ü', 'ue')
        str_in = str_in.replace( 'Ä', 'Ae')
        str_in = str_in.replace( 'Ö', 'Oe')
        str_in = str_in.replace( 'Ü', 'Ue')
        str_in = str_in.replace( 'ß', 'ss')
        return str_in
    # Get component properties.      
    allOccs = root.occurrences
    material_dict = {}

    color_dict = {}
    color_dict['silver_default'] = "0.700 0.700 0.700 1.000"
    for occs in allOccs:
        app_dict = {}
        app_dict['material'] = "silver_default"
  
        #occs_dict = {}
        
        #for attr in occs.attributes:
            #print(attr.value)
 
   
        def traverseColor(occ):
            appear = None
            if occ.appearance:
                #print("occ appearance")
                for prop in occ.appearance.appearanceProperties:

                    if type(prop) == adsk.core.ColorProperty:
                        #print(prop.name)  
                        return(occ.appearance.name, prop)
            
            if occ.bRepBodies:
                for body in occ.bRepBodies:
                    if body.appearance:
                        for prop in body.appearance.appearanceProperties:

                            if type(prop) == adsk.core.ColorProperty:
                                #print(prop.name)  
                                return(body.appearance.name, prop)
                
                # for prop in occ.component.material.appearance.appearanceProperties:
                #     #print(prop)
                #     if type(prop) == adsk.core.ColorProperty:
                #         return(occ.component.material.appearance.name, prop)  


            if occ.component.material:
                #print("material found")
                for prop in occ.component.material.appearance.appearanceProperties:
                    #print(prop)
                    if type(prop) == adsk.core.ColorProperty:
                        return(occ.component.material.appearance.name, prop)  

            if occ.childOccurrences:
                for child in occ.childOccurrences:
                    #print(child.name)
                    appear = traverseColor(child)
            return appear
    
        try:
            prop_name, prop = traverseColor(occs)
        
        
            if prop:
                color_name = convert_german(prop_name).replace("Farbe - ","").replace("Color - ","")
                color_name = ("".join(re.findall(r"[A-Za-z0-9 ]*", color_name)))
                color_name = re.sub('\s+',' ',color_name)
                color_name.strip()
                color_name = re.sub('[ :()]', '_', color_name)
                color_name = color_name.replace("__","_").lower()
                    # print("Color found: "+ color_name)
                    # print("Red: %d ", prop.value.red)
                    # print("Green: %d", prop.value.green)
                    # print("Blue: %d", prop.value.green)                    
                    # print("Opac: %d", prop.value.opacity)
                    
                app_dict['material'] = color_name
                color_dict[color_name] = f"{prop.value.red/255} {prop.value.green/255} {prop.value.blue/255} {prop.value.opacity/255}"
     
        
        
        except:
                print('Failed:\n{}'.format(traceback.format_exc()))



        # if occs.appearance:
        #     for prop in occs.appearance.appearanceProperties:
                
        #         if type(prop) == adsk.core.ColorProperty:
        # #if prop:
        #             color_name = convert_german(occs.appearance.name).replace("Farbe - ","").replace("Color - ","")
        #             color_name = ("".join(re.findall(r"[A-Za-z0-9 ]*", color_name)))
        #             color_name = re.sub('\s+',' ',color_name)
        #             color_name.strip()
        #             color_name = re.sub('[ :()]', '_', color_name)
        #             color_name = color_name.replace("__","_").lower()
        #             # print("Color found: "+ color_name)
        #             # print("Red: %d ", prop.value.red)
        #             # print("Green: %d", prop.value.green)
        #             # print("Blue: %d", prop.value.green)                    
        #             # print("Opac: %d", prop.value.opacity)
                    
        #             app_dict['material'] = color_name
        #             color_dict[color_name] = f"{prop.value.red/255} {prop.value.green/255} {prop.value.blue/255} {prop.value.opacity/255}"
        #             break

        if "base_link" in occs.component.name:
            material_dict['base_link'] = app_dict
        else:
            material_dict[re.sub('[ :()]', '_', occs.name)] = app_dict

    return material_dict, color_dict, msg