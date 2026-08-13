# ba_meta require api 9

import babase
import bascenev1 as bs
import math
import random
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.bomb import Blast 

COMBO_TIME_LIMIT = 0.3

COOLDOWN_TELEPORT = 0.01
COOLDOWN_INFINITY = 1.0    
COOLDOWN_BLUE = 1.0         
COOLDOWN_RED = 1.0          
COOLDOWN_PURPLE = 1.0      
COOLDOWN_DOMAIN = 1.0
COOLDOWN_HEAL = 1.0        

DURATION_INFINITY = 10.0    
DURATION_BLUE = 2.0         
DURATION_DOMAIN = 10.0      

COMBOS = {
    "D-D-D": "gojo_teleport",      
    "U-U-U-U-U-U": "gojo_infinity",      
    "R-R-R": "gojo_blue",          
    "L-L-L": "gojo_red",           
    "L-U-R": "gojo_purple",        
    "U-D-U-D": "gojo_domain",
    "D-L-U": "gojo_heal"           
}

COOLDOWN_MAP = {
    "gojo_teleport": COOLDOWN_TELEPORT,
    "gojo_infinity": COOLDOWN_INFINITY,
    "gojo_blue": COOLDOWN_BLUE,
    "gojo_red": COOLDOWN_RED,
    "gojo_purple": COOLDOWN_PURPLE,
    "gojo_domain": COOLDOWN_DOMAIN,
    "gojo_heal": COOLDOWN_HEAL     
}

def get_dir(spaz):
    if not spaz.node.exists(): return (1, 0, 0)
    jx = spaz.node.move_left_right
    jz = -spaz.node.move_up_down 
    mag = math.sqrt(jx**2 + jz**2)
    if mag < 0.1:
        return (1, 0, 0)
    return (jx/mag, 0, jz/mag)

def spawn_ui(spaz, name, color=(0.5, 0.0, 1.0)):
    if not spaz.node.exists(): return
    mn = bs.newnode('math', owner=spaz.node, attrs={'input1': (0, 1.5, 0), 'operation': 'add'})
    spaz.node.connectattr('position', mn, 'input2')
    txt = bs.newnode('text', owner=spaz.node, attrs={
        'text': name, 'in_world': True, 'color': color, 
        'scale': 0.0, 'h_align': 'center', 'shadow': 1.0})
    mn.connectattr('output', txt, 'position')
    bs.animate(txt, 'scale', {0:0, 0.1:0.02, 1.5:0.02, 2.0:0})
    bs.timer(2.0, babase.CallPartial(txt.delete))

def set_invincible(spaz, duration):
    if not spaz.node.exists(): return
    spaz.node.invincible = True
    def remove_inv():
        if spaz.node.exists():
            spaz.node.invincible = False
    bs.timer(duration, remove_inv)

def create_solid_orb(start_pos, end_pos, move_time, color, radius):
    orbs = []
    for _ in range(4):
        orb = bs.newnode('shield', attrs={'position': start_pos, 'color': color, 'radius': radius})
        bs.animate_array(orb, 'position', 3, {0: start_pos, move_time: end_pos})
        orbs.append(orb)
    return orbs

def delete_solid_orb(orbs):
    for orb in orbs:
        if orb.exists():
            orb.delete()


def gojo_heal(spaz):
   
    if not spaz.node.exists(): return
    
    
    if hasattr(spaz, 'hitpoints_max'):
        spaz.hitpoints = spaz.hitpoints_max
    else:
        spaz.hitpoints = 1000
        
    
    spawn_ui(spaz, " ", color=(0.2, 1.0, 0.2))
    p = spaz.node.position
    bs.emitfx(position=p, count=20, spread=0.5, chunk_type='spark')


def gojo_teleport(spaz):
    f = get_dir(spaz)
    if not spaz.node.exists(): return
    p = spaz.node.position
    new_pos = (p[0] + f[0]*6, p[1] + 1.0, p[2] + f[2]*6)
    spaz.node.handlemessage("stand", new_pos[0], new_pos[1], new_pos[2], 0)
    bs.emitfx(position=p, count=15, spread=0.5, chunk_type='spark')
    bs.emitfx(position=new_pos, count=15, spread=0.5, chunk_type='spark')

def gojo_infinity(spaz):
    if not spaz.node.exists(): return
    
    inf_shield = bs.newnode('shield', owner=spaz.node, attrs={'color': (0.01, 0.01, 0.01), 'radius': 2.2})
    spaz.node.connectattr('position', inf_shield, 'position')

    def repel():
        if not spaz.node.exists(): return
        pos = spaz.node.position
        for node in bs.getnodes():
            if node != spaz.node and node.getnodetype() in ['spaz', 'prop']:
                try:
                    n_pos = node.position
                    dist = math.sqrt((n_pos[0]-pos[0])**2 + (n_pos[1]-pos[1])**2 + (n_pos[2]-pos[2])**2)
   
                    if dist < 1.5: 
                        dx, dy, dz = n_pos[0]-pos[0], n_pos[1]-pos[1], n_pos[2]-pos[2]
                        node.handlemessage("impulse", n_pos[0], n_pos[1], n_pos[2], 0, 0, 0, 500, 500, 0, 0, dx, dy, dz)
                except: pass

    def end_infinity():
        if inf_shield.exists():
            inf_shield.delete()
            
    iterations = int(DURATION_INFINITY * 20)
    for i in range(iterations):
        bs.timer(i * 0.05, babase.CallPartial(repel))
    bs.timer(DURATION_INFINITY, babase.CallPartial(end_infinity))

def gojo_blue(spaz):
    f = get_dir(spaz)
    if not spaz.node.exists(): return
    p = spaz.node.position
    center = (p[0] + f[0]*5, p[1] + 1.0, p[2] + f[2]*5)
    
    blue_orbs = create_solid_orb(p, center, 0.3, (0.0, 0.2, 3.0), 0.8)
    damaged_nodes = set()
    
    def pull():
        if not blue_orbs[0].exists(): return
        bs.emitfx(position=center, count=5, spread=1.5, emit_type='distortion')
        for node in bs.getnodes():
            if node != spaz.node and node.getnodetype() == 'spaz':
                try:
                    n_pos = node.position
                    dist = math.sqrt((n_pos[0]-center[0])**2 + (n_pos[1]-center[1])**2 + (n_pos[2]-center[2])**2)
                    if dist < 8.0:
                        dx, dy, dz = center[0]-n_pos[0], center[1]-n_pos[1], center[2]-n_pos[2]
                        node.handlemessage("impulse", n_pos[0], n_pos[1], n_pos[2], 0, 0, 0, 600, 600, 0, 0, dx, dy, dz)
                        if node not in damaged_nodes:
                            node.handlemessage(bs.HitMessage(pos=n_pos, velocity=(0,0,0), magnitude=100.0, flat_damage=True, hit_type='punch', source_node=spaz.node))
                            damaged_nodes.add(node)
                except: pass
    
    iterations = int(DURATION_BLUE * 10)
    for i in range(3, iterations):
        bs.timer(i * 0.1, babase.CallPartial(pull))
    bs.timer(DURATION_BLUE, babase.CallPartial(delete_solid_orb, blue_orbs))

def gojo_red(spaz):
    f = get_dir(spaz)
    if not spaz.node.exists(): return
    p = spaz.node.position
    center = (p[0] + f[0]*5, p[1] + 1.0, p[2] + f[2]*5)
    
    red_orbs = create_solid_orb(p, center, 0.25, (2.0, 0.0, 0.0), 0.6)
    
    def explode():
        delete_solid_orb(red_orbs)
        Blast(position=center, blast_radius=3.0, blast_type='tnt').auto_retain()
        
        for node in bs.getnodes():
            if node != spaz.node and node.getnodetype() == 'spaz':
                try:
                    n_pos = node.position
                    dist = math.sqrt((n_pos[0]-center[0])**2 + (n_pos[1]-center[1])**2 + (n_pos[2]-center[2])**2)
                    if dist < 6.0:
                        dx, dy, dz = n_pos[0]-center[0], n_pos[1]-center[1], n_pos[2]-center[2]
                        node.handlemessage(bs.HitMessage(pos=n_pos, velocity=(dx*2, dy*2, dz*2), magnitude=100.0, flat_damage=True, hit_type='explosion', source_node=spaz.node))
                except: pass
    
    bs.timer(0.25, explode)

def gojo_purple(spaz):
    f = get_dir(spaz)
    if not spaz.node.exists(): return
    
    set_invincible(spaz, 0.3)
    
    p = spaz.node.position
    end_pos = (p[0] + f[0]*15, p[1] + 1.0, p[2] + f[2]*15)
    
    purple_orbs = create_solid_orb(p, end_pos, 1.5, (0.4, 0.0, 1.0), 2.0)
    damaged_nodes = set()
    
    def purple_destroy():
        if not purple_orbs[0].exists(): return
        curr_pos = purple_orbs[0].position
        
        Blast(position=curr_pos, blast_radius=2.0, blast_type='normal').auto_retain()
        
        for node in bs.getnodes():
            if node != spaz.node and node.getnodetype() == 'spaz':
                try:
                    n_pos = node.position
                    dist = math.sqrt((n_pos[0]-curr_pos[0])**2 + (n_pos[1]-curr_pos[1])**2 + (n_pos[2]-curr_pos[2])**2)
                    if dist < 3.5:
                        if node not in damaged_nodes:
                            node.handlemessage(bs.HitMessage(pos=n_pos, velocity=(f[0]*10, 5, f[2]*10), magnitude=100.0, flat_damage=True, hit_type='punch', source_node=spaz.node))
                            damaged_nodes.add(node)
                except: pass

    for i in range(1, 151):
        bs.timer(i * 0.1, babase.CallPartial(purple_destroy))
        
    bs.timer(1.5, babase.CallPartial(delete_solid_orb, purple_orbs))

def gojo_domain(spaz):
    if not spaz.node.exists(): return
    
    txt = bs.newnode('text', attrs={
        'text': 'گسترش قلمرو...\nخلأ بی‌نهایت!',
        'in_world': False,
        'h_attach': 'center',
        'v_attach': 'top',           
        'h_align': 'center',
        'v_align': 'top',
        'position': (0, -150),       
        'scale': 0.0,
        'color': (1.0, 1.0, 1.0),
        'shadow': 1.0
    })
    
    bs.animate(txt, 'scale', {0.0: 0.0, 0.2: 2.0, 0.3: 1.8})
    bs.animate(txt, 'opacity', {0.0: 0.0, 0.1: 1.0, 3.0: 1.0, 4.0: 0.0})
    bs.timer(4.0, txt.delete)
    
    original_name = spaz.node.name
    spaz.node.name = " " 
    
    g_node = bs.getactivity().globalsnode
    old_tint = g_node.tint
    old_ambient = g_node.ambient_color
    
    g_node.tint = (0.02, 0.02, 0.05)
    g_node.ambient_color = (0.02, 0.02, 0.05)
    
    active_lights = []
    for node in bs.getnodes():
        if node.getnodetype() == 'spaz' and node != spaz.node:
            try:
                enemy_light = bs.newnode('light', owner=node, attrs={
                    'color': (0.8, 0.8, 1.0), 
                    'radius': 0.15, 
                    'intensity': 5.0,
                    'volume_intensity_scale': 0.1
                })
                node.connectattr('position', enemy_light, 'position')
                active_lights.append(enemy_light)
                
                node.handlemessage("knockout", DURATION_DOMAIN * 1000.0) 
            except: pass
            
    def end_domain():
        g_node.tint = old_tint
        g_node.ambient_color = old_ambient
        if spaz.node.exists():
            spaz.node.name = original_name 
            
        for l in active_lights:
            if l.exists():
                l.delete()
                
    bs.timer(DURATION_DOMAIN, end_domain)


def run_input(spaz, key):
    if not spaz.node.exists(): return
    
    if not hasattr(spaz, 'ds_cb'): spaz.ds_cb = []
    if not hasattr(spaz, '_ds_cooldowns'): spaz._ds_cooldowns = {} 
    
    spaz.ds_cb.append(key)
    if len(spaz.ds_cb) > 8: spaz.ds_cb.pop(0)
        
    seq = "-".join(spaz.ds_cb)
    matched = False
    
    for combo, f_name in COMBOS.items():
        if seq.endswith(combo):
            
            jx = spaz.node.move_left_right
            jz = spaz.node.move_up_down
            mag = math.sqrt(jx**2 + jz**2)
            
            # در اینجا gojo_heal اضافه شد تا بتوانید در حالت ایستاده هم جانتان را پر کنید
            if mag < 0.2 and f_name not in ["gojo_domain", "gojo_infinity", "gojo_heal"]:
                spaz.ds_cb = []
                return
                
            current_time = bs.time()
            last_used_time = spaz._ds_cooldowns.get(f_name, 0.0)
            required_cooldown = COOLDOWN_MAP.get(f_name, 0.0)
            
            if current_time < last_used_time + required_cooldown:
                time_left = (last_used_time + required_cooldown) - current_time
                spawn_ui(spaz, f"در حال شارژ: {time_left:.1f}s", (1.0, 0.2, 0.2))
                spaz.ds_cb = []
                return
                
            spaz._ds_cooldowns[f_name] = current_time
            globals()[f_name](spaz) 
            spaz.ds_cb = []
            matched = True
            break
            
    if hasattr(spaz, 'ds_tmr') and spaz.ds_tmr: 
        spaz.ds_tmr = None
        
    if not matched:
        def reset_cb(s):
            if hasattr(s, 'ds_cb'): s.ds_cb = []
        spaz.ds_tmr = bs.Timer(COMBO_TIME_LIMIT, babase.CallPartial(reset_cb, spaz))

def np(self): 
    self.old_p()
    run_input(self, 'L')
def nu(self): 
    self.old_u()
    run_input(self, 'U')
def nb(self): 
    self.old_b()
    run_input(self, 'R')
def nj(self): 
    self.old_j()
    run_input(self, 'D')

def patch():
    if hasattr(PlayerSpaz, '_gojo_patched'): return
    PlayerSpaz._gojo_patched = True
    
    PlayerSpaz.old_p = PlayerSpaz.on_punch_press
    PlayerSpaz.old_u = PlayerSpaz.on_pickup_press
    PlayerSpaz.old_b = PlayerSpaz.on_bomb_press
    PlayerSpaz.old_j = PlayerSpaz.on_jump_press
    
    PlayerSpaz.on_punch_press = np
    PlayerSpaz.on_pickup_press = nu
    PlayerSpaz.on_bomb_press = nb
    PlayerSpaz.on_jump_press = nj

# ba_meta export babase.Plugin
class GojoSatoruPlugin(babase.Plugin):
    def on_app_running(self):
        patch()
