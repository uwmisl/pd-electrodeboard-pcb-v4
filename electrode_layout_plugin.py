import pcbnew
import os
#import yaml

class ElectrodeLayout(pcbnew.ActionPlugin):
    """
    Uses data in layout.yaml (location in your kicad project directory) to layout electrode footprints
    """
    def defaults( self ):
        self.name = "Layout electrodes from layout.yaml"
        self.category = "Modify PCB"
        self.description = "Move the electrode footprints to match the layout.yaml file in the project diretory"
        self.show_toolbar_button = True

    def Run( self ):
        pcb = pcbnew.GetBoard()
        projdir = os.environ['KIPRJMOD']
        # Kicad seems to be broken at setting this variable? 
        #projdir = "Users/jeff/Dropbox/MISL/Projects/ElectrodeBoard/newhw/PD_ElectrodeBoard_v4"
        with open(os.path.join(projdir, 'layout.yaml')) as f:
            data = yaml.load(f.read())
        
        def lookup_location(index):
            for row in range(len(data['map'])):
                for col in range(len(data['map'][row])):
                    if data['map'][row][col] == index:
                        return (col, row)
            return None
        
        def lookup_footprint(index):
            if not 'footprints' in data:
                return None
            if index in data['footprints']:
                return data['footprints'][i]
            else:
                return data['footprints']['default']
        
        def lookup_rotation(index):
            if 'rotations' in data and index in data['rotations']:
                return data['rotations'][i]
            else:
                return None
        
        x0 = data['origin'][0]
        y0 = data['origin'][1]
        pitch = data['pitch']
        for i in range(400):
            mod = pcb.FindModuleByReference('E%d' % i)
            if mod is None:
                continue
            
            location = lookup_location(i)
            if location is None:
                continue
            
            # This is a kludgey way to distinguish standard electrode pads from special pads like reservoirs
            # Special footprints have designators > 200
            if i < 200:
                footprint_name = lookup_footprint(i)
            else:
                footprint_name = None
            if footprint_name:
                # As far as I can tell, you can't change the footprint of a module, you have to delete and re-add
                
                # Save important properties of the exiting module
                ref = mod.GetReference()
                net = mod.Pads().Get().GetNet()
                value = mod.GetValue()
                
                basepath = os.environ.get('KIPRJMOD')
                libpath = os.path.join(basepath, "../electrodes.pretty")
                newmod = pcbnew.FootprintLoad(libpath, footprint_name)
                if newmod is None:
                    print("Failed to load footprint")
                    raise RuntimeError("Failed to load footprint %s from %s" % (footprint_name, libpath))
                pcb.Delete(mod)
                mod = newmod
                # Restore original props
                mod.SetReference(ref)
                mod.Pads().Get().SetNet(net)
                mod.SetValue(value)
                pcb.Add(mod)
            
            mod.SetPosition(pcbnew.wxPointMM(x0 + location[0] * pitch, y0 + location[1] * pitch))
            rotation = lookup_rotation(i)
            if rotation is not None:
                mod.SetOrientationDegrees(rotation)

        # for i in data:
        #     c = pcb.FindModuleByReference('E1"')
        #     c.SetPosition(pcbnew.wxPointMM(float(i[1]),float(i[2])))
        #     c.SetOrientation(1.0 * i[3] * 10)


ElectrodeLayout().register()