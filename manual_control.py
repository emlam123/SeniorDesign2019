#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Allows controlling a vehicle with a keyboard. For a simpler and more
# documented example, please take a look at tutorial.py.

"""
Welcome to CARLA manual control.

Use ARROWS or WASD keys for control.

    W            : throttle
    S            : brake
    AD           : steer
    Q            : toggle reverse
    Space        : hand-brake
    P            : toggle autopilot
    M            : toggle manual transmission
    ,/.          : gear up/down

    TAB          : change sensor position
    `            : next sensor
    [1-9]        : change to sensor [1-9]
    C            : change weather (Shift+C reverse)
    Backspace    : change vehicle

    R            : toggle recording images to disk

    CTRL + R     : toggle recording of simulation (replacing any previous)
    CTRL + P     : start replaying last recorded simulation
    CTRL + +     : increments the start time of the replay by 1 second (+SHIFT = 10 seconds)
    CTRL + -     : decrements the start time of the replay by 1 second (+SHIFT = 10 seconds)

    F1           : toggle HUD
    H/?          : toggle help
    ESC          : quit
"""

from __future__ import print_function


# ==============================================================================
# -- find carla module ---------------------------------------------------------
# ==============================================================================


import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

try:
    sys.path.append(glob.glob('../carla/agents/navigation')[0])
except IndexError:
    pass


#from roaming_agent import RoamingAgent
#from basic_agent import BasicAgent


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================


sys.path.append(glob.glob('/Users/Emily/Anaconda3/CARLA_0.9.5/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])

import socket
from multiprocessing import Process,Lock
import carla


import threading
import concurrent.futures
import math

#from carla import ColorConverter as cc
from time import sleep
import argparse
import collections
import datetime
import logging
import math
import random
import re
import weakref
import seg

tailgate_distance=None
try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_BACKQUOTE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_c
    from pygame.locals import K_d
    from pygame.locals import K_h
    from pygame.locals import K_m
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_r
    from pygame.locals import K_s
    from pygame.locals import K_w
    from pygame.locals import K_MINUS
    from pygame.locals import K_EQUALS

    from pygame.locals import K_v
    from pygame.locals import K_x
    from pygame.locals import K_z

except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')


diff=0
steer_angle=0
turn_right=False
turn_left=False
from_server = 'None'
dist_left=0
dist_right=0


# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================


def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


# ==============================================================================
# -- World ---------------------------------------------------------------------
# ==============================================================================


class World(object):
    def __init__(self, carla_world, hud, actor_filter, actor_role_name='hero'):
        self.world = carla_world
        self.actor_role_name = actor_role_name
        self.map = self.world.get_map()
        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        self._actor_filter = actor_filter
        self.restart()
        self.world.on_tick(hud.on_world_tick)
        self.recording_enabled = False
        self.recording_start = 0
        self.dummies=[]

        self.spawn_vehicle()

    def tailgate(self):
        global tailgate_distance

        player_xy = self.player.get_location()
        
        location=(player_xy.x,player_xy.y,player_xy.z)
        
        for car in self.dummies:
            dummy_xy = car.get_location()
            dummy_location=(dummy_xy.x,dummy_xy.y,dummy_xy.z)
            distance = math.sqrt(sum([(a-b)**2 for a, b in zip(location,dummy_location)]))
            
            if distance<6:
                if tailgate_distance!=distance:
                    tailgate_distance=distance

                print("TOO CLOSE")
            else:
                tailgate_distance=None

                

    def dummy_vehicle(self):
        # Get a random blueprint.
        blueprint = random.choice(self.world.get_blueprint_library().filter("model3"))
        blueprint.set_attribute('role_name', self.actor_role_name)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        # Spawn the players
        
        spawn_points = self.map.get_spawn_points()
        spawn_point = random.choice(spawn_points)
        print(spawn_point)
        new_actor = self.world.try_spawn_actor(blueprint, spawn_point)
        self.dummies.append(new_actor)

        new_actor.set_autopilot(True)

        while new_actor is None:
            spawn_points = self.map.get_spawn_points()
            spawn_point = random.choice(spawn_points) #if spawn_points else carla.Transform()
            print(spawn_point)
            new_actor = self.world.try_spawn_actor(blueprint, spawn_point)
            self.dummies.append(new_actor)

            new_actor.set_autopilot(True)

    def spawn_vehicle(self):
        # Get a random blueprint. Spawn 5 cars.
        cars=[]
        for i in range(2):
            blueprint = random.choice(self.world.get_blueprint_library().filter("tesla"))
            cars.append(blueprint)
            blueprint.set_attribute('role_name', self.actor_role_name)
            if blueprint.has_attribute('color'):
                color = random.choice(blueprint.get_attribute('color').recommended_values)
                blueprint.set_attribute('color', color)
        # Spawn the players
        loc=[]

        spawn_points = self.map.get_spawn_points()
        spawn_point = random.choice(spawn_points)
        print(spawn_point)
        spawn_point.location.x=21.715
        spawn_point.location.y=139.518
        spawn_point.location.z=2.5
        spawn_point.rotation.pitch=0
        spawn_point.rotation.yaw=0.234757
        spawn_point.rotation.roll=0
        loc.append(spawn_point)
        spawn_points = self.map.get_spawn_points()
        spawn_point = random.choice(spawn_points)
        #print(spawn_point)
        spawn_point.location.x=25.715
        spawn_point.location.y=146.5
        spawn_point.location.z=2.5
        spawn_point.rotation.pitch=0
        spawn_point.rotation.yaw=0.234757
        spawn_point.rotation.roll=0
        loc.append(spawn_point)

        new_actor = self.world.try_spawn_actor(cars[0], loc[0])
        self.dummies.append(new_actor)
        new_actor1 = self.world.try_spawn_actor(cars[1], loc[1])
        self.dummies.append(new_actor1)
        new_actor1.set_autopilot(True)
        new_actor.set_autopilot(True)

        while new_actor is None:
            spawn_points = self.map.get_spawn_points()
            spawn_point = random.choice(spawn_points) #if spawn_points else carla.Transform()
            #print(spawn_point)
            new_actor = self.world.try_spawn_actor(blueprint, spawn_point)
            self.dummies.append(new_actor)

            new_actor.set_autopilot(True)    

    def restart(self):
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Get a random blueprint.
        blueprint = random.choice(self.world.get_blueprint_library().filter('tesla'))
        blueprint.set_attribute('role_name', self.actor_role_name)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        # Spawn the player.
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        while self.player is None:
            spawn_points = self.map.get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            spawn_point.location.x=21.7007
            spawn_point.location.y=143.018
            spawn_point.location.z=2.5
            spawn_point.rotation.pitch=0
            spawn_point.rotation.yaw=0.234757
            spawn_point.rotation.roll=0

            #print(spawn_point)
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
            #self.spawn_vehicle()
        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)


    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def tick(self, clock,socket):
        #self.tailgate()
        self.hud.tick(self, clock,socket)

    def render(self, display):
        self.camera_manager.render(display)
        self.hud.render(display)

    def destroy_sensors(self):
        self.camera_manager.sensor.destroy()
        self.camera_manager.sensor = None
        self.camera_manager.index = None

    def destroy(self):
        actors = [
            self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor,
            self.player]
        for actor in actors:
            if actor is not None:
                actor.destroy()

        for actor in self.dummies:
            if actor is not None:
                actor.destroy()

# ==============================================================================
# -- KeyboardControl -----------------------------------------------------------
# ==============================================================================


class KeyboardControl(object):
    def __init__(self, world, start_in_autopilot,socket):
        global from_server

        self._autopilot_enabled = start_in_autopilot
        if isinstance(world.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            world.player.set_autopilot(self._autopilot_enabled)
            
            #check initial tire friction
            #physics_control = world.player.get_physics_control()
            #print(physics_control)
            

        elif isinstance(world.player, carla.Walker):
            self._control = carla.WalkerControl()
            self._autopilot_enabled = False
            self._rotation = world.player.get_transform().rotation
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)


    def parse_events(self, client, world, clock):
        global turn_left
        global turn_right

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True

                elif event.key == K_v:
                    #spawn more dummy vehicles
                    world.dummy_vehicle()
               
                #turn signals
                elif event.key == K_x and not (pygame.key.get_mods() & KMOD_CTRL):
                    turn_right=True
                    print(turn_right)
                elif event.key == K_x and (pygame.key.get_mods() & KMOD_CTRL):
                    turn_right=False
                elif event.key == K_z and not (pygame.key.get_mods() & KMOD_CTRL):
                    turn_left=True
                    print(turn_left)
                elif event.key == K_z and (pygame.key.get_mods() & KMOD_CTRL):
                    turn_left=False

                elif event.key == K_BACKSPACE:
                    world.restart()
                elif event.key == K_F1:
                    world.hud.toggle_info()
                elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                    world.hud.help.toggle()
                elif event.key == K_TAB:
                    world.camera_manager.toggle_camera()
                elif event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                    world.next_weather(reverse=True)
                elif event.key == K_c:
                    world.next_weather()
                elif event.key == K_BACKQUOTE:
                    world.camera_manager.next_sensor()
                elif event.key > K_0 and event.key <= K_9:
                    world.camera_manager.set_sensor(event.key - 1 - K_0)
                elif event.key == K_r and not (pygame.key.get_mods() & KMOD_CTRL):
                    world.camera_manager.toggle_recording()
                elif event.key == K_r and (pygame.key.get_mods() & KMOD_CTRL):
                    if (world.recording_enabled):
                        client.stop_recorder()
                        world.recording_enabled = False
                        world.hud.notification("Recorder is OFF")
                    else:
                        client.start_recorder("manual_recording.rec")
                        world.recording_enabled = True
                        world.hud.notification("Recorder is ON")
                elif event.key == K_p and (pygame.key.get_mods() & KMOD_CTRL):
                    # stop recorder
                    client.stop_recorder()
                    world.recording_enabled = False
                    # work around to fix camera at start of replaying
                    currentIndex = world.camera_manager.index
                    world.destroy_sensors()
                    # disable autopilot
                    self._autopilot_enabled = False
                    world.player.set_autopilot(self._autopilot_enabled)
                    world.hud.notification("Replaying file 'manual_recording.rec'")
                    # replayer
                    client.replay_file("manual_recording.rec", world.recording_start, 0, 0)
                    world.camera_manager.set_sensor(currentIndex)
                elif event.key == K_MINUS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        world.recording_start -= 10
                    else:
                        world.recording_start -= 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                elif event.key == K_EQUALS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        world.recording_start += 10
                    else:
                        world.recording_start += 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                if isinstance(self._control, carla.VehicleControl):
                    if event.key == K_q:
                        self._control.gear = 1 if self._control.reverse else -1
                    elif event.key == K_m:
                        self._control.manual_gear_shift = not self._control.manual_gear_shift
                        self._control.gear = world.player.get_control().gear
                        world.hud.notification('%s Transmission' %
                                               ('Manual' if self._control.manual_gear_shift else 'Automatic'))
                    elif self._control.manual_gear_shift and event.key == K_COMMA:
                        self._control.gear = max(-1, self._control.gear - 1)
                    elif self._control.manual_gear_shift and event.key == K_PERIOD:
                        self._control.gear = self._control.gear + 1
                    elif event.key == K_p and not (pygame.key.get_mods() & KMOD_CTRL):
                        self._autopilot_enabled = not self._autopilot_enabled
                        world.player.set_autopilot(self._autopilot_enabled)
                        world.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
       
        if not self._autopilot_enabled:
            if isinstance(self._control, carla.VehicleControl):
                keys = pygame.key.get_pressed()
                if sum(keys) > 0:
                    self._parse_vehicle_keys(keys, clock.get_time())
                    self._control.reverse = self._control.gear < 0
                    world.player.apply_control(self._control)
            elif isinstance(self._control, carla.WalkerControl):
                self._parse_walker_keys(pygame.key.get_pressed(), clock.get_time())
                world.player.apply_control(self._control)

    def _parse_vehicle_keys(self, keys, milliseconds):
        self._control.throttle = 1.0 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 5e-4 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

    def _parse_walker_keys(self, keys, milliseconds):
        self._control.speed = 0.0
        if keys[K_DOWN] or keys[K_s]:
            self._control.speed = 0.0
        if keys[K_LEFT] or keys[K_a]:
            self._control.speed = .01
            self._rotation.yaw -= 0.08 * milliseconds
        if keys[K_RIGHT] or keys[K_d]:
            self._control.speed = .01
            self._rotation.yaw += 0.08 * milliseconds
        if keys[K_UP] or keys[K_w]:
            self._control.speed = 5.556 if pygame.key.get_mods() & KMOD_SHIFT else 2.778
        self._control.jump = keys[K_SPACE]
        self._rotation.yaw = round(self._rotation.yaw, 1)
        self._control.direction = self._rotation.get_forward_vector()

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)


# ==============================================================================
# -- HUD -----------------------------------------------------------------------
# ==============================================================================


class HUD(object):
    def __init__(self, width, height,socket):
        self.dim = (width, height)
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        fonts = [x for x in pygame.font.get_fonts() if 'arial' in x]
        default_font = 'ubuntuarial'
        arial = default_font if default_font in fonts else fonts[0]
        arial = pygame.font.match_font(arial)
        self._font_arial = pygame.font.Font(arial, 14)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self.help = HelpText(pygame.font.Font(arial, 24), width, height)
        self.server_fps = 0
        self.frame_number = 0
        self.simulation_time = 0
        self._show_info = True
        self._info_text = []
        self._server_clock = pygame.time.Clock()
        self.initial_speed = 0
        self.old_speed=0
        self.music=False
        self.current_waypoint=None
        self.waypoint_R=None
        self.waypoint_L=None
        self.right_dist=0
        self.left_dist=0

    def change_waypoint(self,w,w1):
        if w==None:
            return True
        elif w.lane_id!=w1.lane_id:
            return True
        else:
            return False

    def calculate_distance(self,loc,w):
        dist=math.sqrt((w.transform.location.x - loc[0])**2 + (w.transform.location.y - loc[1])**2 + (w.transform.location.z - loc[2])**2)
        dist-=w.lane_width/2.0
        return dist

    def rotate(self,yaw,point):
        c=math.cos(math.radians(yaw))
        s=math.sin(math.radians(yaw))

        return ((c*point[0]-s*point[1],s*point[0]+c*point[1]))

    def lane_distance(self,world):
        #import pdb; pdb.set_trace()

        vehicle=world.player
        debug=world.world.debug
        #debug=carla.DebugHelper()
        box=vehicle.bounding_box
        #loc=box.location
        loc=vehicle.get_location()
        #print(loc)
        fwd=vehicle.get_transform().get_forward_vector()
        #print(fwd)

        #was working
        if fwd.x>fwd.y:
            orientation='x'
        else:
            orientation='y'

        yaw=vehicle.get_transform().rotation.yaw
        
        tr_v=(loc.x+box.extent.x, loc.y+box.extent.y, loc.z)
        tl_v=(loc.x+box.extent.x, loc.y-box.extent.y, loc.z)
        br_v=(loc.x-box.extent.x, loc.y+box.extent.y, loc.z)
        bl_v=(loc.x-box.extent.x, loc.y-box.extent.y, loc.z)
        

        # b1=(box.extent.x,box.extent.y)
        # b2=(box.extent.x,-box.extent.y)
        # b3=(-box.extent.x, box.extent.y)
        # b4=(-box.extent.x, -box.extent.y)

        # r1=self.rotate(yaw,b1)
        # r2=self.rotate(yaw,b2)
        # r3=self.rotate(yaw,b3)
        # r4=self.rotate(yaw,b4)


        # tr_v=(loc.x+r1[0], loc.y+r1[1], loc.z)
        # tl_v=(loc.x+r3[0], loc.y+r3[1], loc.z)
        # br_v=(loc.x+r2[0], loc.y+r2[1], loc.z)
        # bl_v=(loc.x+r4[0], loc.y+r4[1], loc.z)

        tr=carla.Location()
        tr.x=tr_v[0]
        tr.y=tr_v[1]
        tr.z=tr_v[2]

        tl=carla.Location()
        tl.x=tl_v[0]
        tl.y=tl_v[1]
        tl.z=tl_v[2]

        br=carla.Location()
        br.x=br_v[0]
        br.y=br_v[1]
        br.z=br_v[2]

        bl=carla.Location()
        bl.x=bl_v[0]
        bl.y=bl_v[1]
        bl.z=bl_v[2]


        #import pdb; pdb.set_trace()

        
        waypoint = world.map.get_waypoint(loc,project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Shoulder | carla.LaneType.Sidewalk))

        
       
        self.current_waypoint=waypoint
        
        self.waypoint_R=self.current_waypoint.get_right_lane()
        self.waypoint_L=self.current_waypoint.get_left_lane()


        # print("L and R waypoint: ",self.waypoint_R, self.waypoint_L)
        #print("LANE WIDTH: "+str(waypoint.lane_width))
        if (self.waypoint_R!=None and self.waypoint_L!=None):
            
            if fwd.x>fwd.y:
                orientation='x'
            else:
                orientation='y'

            if orientation=='y':
                wr=carla.Location(self.waypoint_R.transform.location.x, self.waypoint_R.transform.location.y+box.extent.y, self.waypoint_R.transform.location.z)
                wl=carla.Location(self.waypoint_L.transform.location.x, self.waypoint_L.transform.location.y+box.extent.y, self.waypoint_L.transform.location.z)

            else:
                wr=carla.Location(self.waypoint_R.transform.location.x+box.extent.x, self.waypoint_R.transform.location.y, self.waypoint_R.transform.location.z)
                wl=carla.Location(self.waypoint_L.transform.location.x+box.extent.x, self.waypoint_L.transform.location.y, self.waypoint_L.transform.location.z)


            # w1 = world.map.get_waypoint(tr,project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Shoulder | carla.LaneType.Sidewalk))
            # w2 = world.map.get_waypoint(tl,project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Shoulder | carla.LaneType.Sidewalk))
            # w3 = world.map.get_waypoint(br,project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Shoulder | carla.LaneType.Sidewalk))
            # w4 = world.map.get_waypoint(bl,project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Shoulder | carla.LaneType.Sidewalk))
            
            # debug.draw_point(location=tr, size=0.8, color=carla.Color(255,0,255),life_time=0,persistent_lines=True)
            # debug.draw_point(location=tl, size=0.8, color=carla.Color(255,0,255),life_time=0,persistent_lines=True)
            # debug.draw_point(location=waypoint.transform.location, size=0.8, color=carla.Color(255,0,0),life_time=0,persistent_lines=True)
            #debug.draw_point(location=self.waypoint_R.transform.location, size=0.1, color=carla.Color(255,255,0),life_time=0,persistent_lines=True)
            #debug.draw_point(location=self.waypoint_L.transform.location, size=0.1, color=carla.Color(255,255,0),life_time=0,persistent_lines=True)

            # #import pdb; pdb.set_trace()
            #debug.draw_point(location=wr, size=0.1, color=carla.Color(255,0,0),life_time=0,persistent_lines=True)
            #debug.draw_point(location=wl, size=0.1, color=carla.Color(255,0,0),life_time=0,persistent_lines=True)

            # d1 = tr.distance(w1)-self.waypoint_R.lane_width/2
            # d2 = tl.distance(w2)-self.waypoint_L.lane_width/2
            # d3 = br.distance(w3)-self.waypoint_R.lane_width/2
            # d4 = bl.distance(w4)-self.waypoint_L.lane_width/2

            # self.right_dist=min(d1,d3)
            # self.left_dist=min(d2,d4)
            #import pdb; pdb.set_trace()
            self.right_dist=tr.distance(wr)-self.waypoint_R.lane_width/2
            self.left_dist=tl.distance(wl)-self.waypoint_L.lane_width/2

            global dist_left
            global dist_right

            dist_left=self.left_dist
            dist_right=self.right_dist
            
            # #through middle
            # self.right_dist=math.sqrt((self.waypoint_R.transform.location.x - vehicle.get_location().x)**2 + (self.waypoint_R.transform.location.y - vehicle.get_location().y)**2 + (self.waypoint_R.transform.location.z - vehicle.get_location().z)**2)
            # self.right_dist-=self.waypoint_R.lane_width/2.0
            # self.left_dist=math.sqrt((self.waypoint_L.transform.location.x - vehicle.get_location().x)**2 + (self.waypoint_L.transform.location.y - vehicle.get_location().y)**2 + (self.waypoint_L.transform.location.z - vehicle.get_location().z)**2)
            # self.left_dist-=self.waypoint_L.lane_width/2.0
            #print(self.right_dist,self.left_dist)
       


    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        self.frame_number = timestamp.frame_count
        self.simulation_time = timestamp.elapsed_seconds


    def tick(self, world, clock,socket):
        # self.lane_distance(world)
        self._notifications.tick(world, clock)
        if not self._show_info:
            return
        t = world.player.get_transform()
        v = world.player.get_velocity()
        c = world.player.get_control()
        heading = 'N' if abs(t.rotation.yaw) < 89.5 else ''
        heading += 'S' if abs(t.rotation.yaw) > 90.5 else ''
        heading += 'E' if 179.5 > t.rotation.yaw > 0.5 else ''
        heading += 'W' if -0.5 > t.rotation.yaw > -179.5 else ''
        colhist = world.collision_sensor.get_collision_history()
        collision = [colhist[x + self.frame_number - 200] for x in range(0, 200)]
        max_col = max(1.0, max(collision))
        collision = [x / max_col for x in collision]
        vehicles = world.world.get_actors().filter('vehicle.*')
        self._info_text = [
            'Server:  % 16.0f FPS' % self.server_fps,
            'Client:  % 16.0f FPS' % clock.get_fps(),
            '',
            'Vehicle: % 20s' % get_actor_display_name(world.player, truncate=20),
            'Map:     % 20s' % world.map.name,
            'Simulation time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)),
            '',
            'Speed:   % 15.0f km/h' % (3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)),
            'Heading:% 16.0f\N{DEGREE SIGN} % 2s' % (t.rotation.yaw, heading),
            'Location:% 20s' % ('(% 5.1f, % 5.1f)' % (t.location.x, t.location.y)),
            'GNSS:% 24s' % ('(% 2.6f, % 3.6f)' % (world.gnss_sensor.lat, world.gnss_sensor.lon)),
            'Height:  % 18.0f m' % t.location.z,
            '']


        if isinstance(c, carla.VehicleControl):
            self._info_text += [
                ('Throttle:', c.throttle, 0.0, 1.0),
                ('Steer:', c.steer, -1.0, 1.0),
                ('Brake:', c.brake, 0.0, 1.0),
                ('Reverse:', c.reverse),
                ('Hand brake:', c.hand_brake),
                ('Manual:', c.manual_gear_shift),
                'Gear:        %s' % {-1: 'R', 0: 'N'}.get(c.gear, c.gear)]
        elif isinstance(c, carla.WalkerControl):
            self._info_text += [
                ('Speed:', c.speed, 0.0, 5.556),
                ('Jump:', c.jump)]

        #display notification from server
        self._info_text+=['','NOTIFICATION HERE:','']
        self._info_text.append('%s' %(from_server))


        #to send speed
        if ((3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2))>=10):
            speed = '%2.0f' %(3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2))
        else:
            speed = '0'+'%1.0f' %(3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2))
        
        num = int(speed)
        epsilon = 1+self.initial_speed
        epsilon2 = self.initial_speed-1
      
        #if (num<epsilon2 or num>epsilon):
        global steer_angle
        steer_angle=c.steer
        self.check_response(world,socket,speed,c.steer)
        self.initial_speed = num
        
        self._info_text+=['','Distance from right lane: ']
        self._info_text.append('%fm' % (self.right_dist))
        self._info_text+=['Distance from left lane: ']
        self._info_text.append('%fm' % (self.left_dist))



        self._info_text += [
            '',
            'Collision:',
            collision,
            '',
            'Number of vehicles: % 8d' % len(vehicles)]
        if len(vehicles) > 1:
            self._info_text += ['Nearby vehicles:']
            distance = lambda l: math.sqrt((l.x - t.location.x)**2 + (l.y - t.location.y)**2 + (l.z - t.location.z)**2)
            #THIS ALREADY CALCULATES DISTANCE

            vehicles = [(distance(x.get_location()), x) for x in vehicles if x.id != world.player.id]
            for d, vehicle in sorted(vehicles):
                if d > 200.0:
                    break
                vehicle_type = get_actor_display_name(vehicle, truncate=22)
                self._info_text.append('% 4dm %s' % (d, vehicle_type))
        
      
        

    def check_response(self,world,socket,speed,steer_angle):
        global from_server

        if (from_server=="Slow Down"):
            #playsound('liszt.mp3')

            physics_control = world.player.get_physics_control()
            #front_left_wheel  = carla.WheelPhysicsControl(tire_friction=3, damping_rate=1.0, steer_angle=70.0, disable_steering=False)
            #front_right_wheel = carla.WheelPhysicsControl(tire_friction=3, damping_rate=1.5, steer_angle=70.0, disable_steering=False)
            #rear_left_wheel   = carla.WheelPhysicsControl(tire_friction=3, damping_rate=0.2, steer_angle=0.0,  disable_steering=False)
            #rear_right_wheel  = carla.WheelPhysicsControl(tire_friction=3, damping_rate=1.3, steer_angle=0.0,  disable_steering=False)

            #wheels = [front_left_wheel, front_right_wheel, rear_left_wheel, rear_right_wheel]
            
            #physics_control.wheels = wheels

            #print ('changed tire friction to 3')
            #self.create_thread(socket,speed,steer_angle)
            #print(physics_control)
        elif (from_server=="Steering too far to the right (high steer)") or (from_server=="Steering too far to the left (high steer)"):
            self.warning_thread("beep.mp3")

        elif (from_server=="Steering too far to the right (low steer)") or (from_server=="Steering too far to the left (low steer)"):
            self.warning_thread("short_beep.mp3")
        
        self.create_thread(socket,speed,steer_angle)



    def create_thread(self,socket,speed,steer_angle):
        lock = Lock()
        t=threading.Thread(target=self.send_info,args=(lock,socket,speed,steer_angle))
        t.start()
        t.join()

    def warning_thread(self,file):
        warn=threading.Thread(target=self.play_noise,args=(file,))
        warn.start()
        warn.join()
        

    def play_noise(self,file):
        if pygame.mixer.music.get_busy()==False:
            pygame.mixer.init()
            pygame.mixer.music.load(file)
            pygame.mixer.music.play()


    def send_info(self,lock,socket,speed,steer):
        global dist_left
        global dist_right
        global steer_angle


        #send to server 
        lock.acquire()
        socket.send(('1:').encode()+speed.encode()+("\n").encode()+str(steer_angle).encode()+("\n").encode()+str(dist_left).encode()+("\n").encode()+str(dist_right).encode()+("\n").encode()+str(turn_left).encode()+("\n").encode()+str(turn_right).encode()+("\n").encode()+str(datetime.datetime.now()).encode())
        # print(steer_angle,dist_left,dist_right)
        lock.release()
        


    def toggle_info(self):
        self._show_info = not self._show_info

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def error(self, text):
        self._notifications.set_text('Error: %s' % text, (255, 0, 0))

    def render(self, display):
        if self._show_info:
            info_surface = pygame.Surface((220, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                    item = None
                    v_offset += 18
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                        f = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_arial.render(item, True, (255, 255, 255))
                    display.blit(surface, (8, v_offset))
                v_offset += 18
        self._notifications.render(display)
        self.help.render(display)


# ==============================================================================
# -- FadingText ----------------------------------------------------------------
# ==============================================================================


class FadingText(object):
    def __init__(self, font, dim, pos):
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        display.blit(self.surface, self.pos)


# ==============================================================================
# -- HelpText ------------------------------------------------------------------
# ==============================================================================


class HelpText(object):
    def __init__(self, font, width, height):
        lines = __doc__.split('\n')
        self.font = font
        self.dim = (680, len(lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill((0, 0, 0, 0))
        for n, line in enumerate(lines):
            text_texture = self.font.render(line, True, (255, 255, 255))
            self.surface.blit(text_texture, (22, n * 22))
            self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        self._render = not self._render

    def render(self, display):
        if self._render:
            display.blit(self.surface, self.pos)


# ==============================================================================
# -- CollisionSensor -----------------------------------------------------------
# ==============================================================================


class CollisionSensor(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self.history = []
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: CollisionSensor._on_collision(weak_self, event))

    def get_collision_history(self):
        history = collections.defaultdict(int)
        for frame, intensity in self.history:
            history[frame] += intensity
        return history

    @staticmethod
    def _on_collision(weak_self, event):
        self = weak_self()
        if not self:
            return
        actor_type = get_actor_display_name(event.other_actor)
        self.hud.notification('Collision with %r' % actor_type)
        impulse = event.normal_impulse
        intensity = math.sqrt(impulse.x**2 + impulse.y**2 + impulse.z**2)
        self.history.append((event.frame_number, intensity))
        if len(self.history) > 4000:
            self.history.pop(0)


# ==============================================================================
# -- LaneInvasionSensor --------------------------------------------------------
# ==============================================================================


class LaneInvasionSensor(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.lane_invasion')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: LaneInvasionSensor._on_invasion(weak_self, event))

    @staticmethod
    def _on_invasion(weak_self, event):
        global steer_angle
        # print(event)
        self = weak_self()
        if not self:
            return
        lane_types = set(x.type for x in event.crossed_lane_markings)
        text = ['%r' % str(x).split()[-1] for x in lane_types]
        self.hud.notification('Crossed line %s' % ' and '.join(text))
        # print(self._parent.get_location(), steer_angle)



# ==============================================================================
# -- GnssSensor --------------------------------------------------------
# ==============================================================================


class GnssSensor(object):
    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        self.lat = 0.0
        self.lon = 0.0
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(bp, carla.Transform(carla.Location(x=1.0, z=2.8)), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: GnssSensor._on_gnss_event(weak_self, event))

    @staticmethod
    def _on_gnss_event(weak_self, event):
        self = weak_self()
        if not self:
            return
        self.lat = event.latitude
        self.lon = event.longitude


# ==============================================================================
# -- CameraManager -------------------------------------------------------------
# ==============================================================================


class CameraManager(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self.surface = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        self._camera_transforms = [
            carla.Transform(carla.Location(x=-5.5, z=2.8), carla.Rotation(pitch=-15)),
            carla.Transform(carla.Location(x=1.6, z=1.7))]
        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.semantic_segmentation', carla.ColorConverter.CityScapesPalette,
                'Camera Semantic Segmentation (CityScapes Palette)'],
            ['sensor.camera.rgb', carla.ColorConverter.Raw, 'Camera RGB'],
            ['sensor.camera.depth', carla.ColorConverter.Raw, 'Camera Depth (Raw)'],
            ['sensor.camera.depth', carla.ColorConverter.Depth, 'Camera Depth (Gray Scale)'],
            ['sensor.camera.depth', carla.ColorConverter.LogarithmicDepth, 'Camera Depth (Logarithmic Gray Scale)'],
            ['sensor.camera.semantic_segmentation', carla.ColorConverter.Raw, 'Camera Semantic Segmentation (Raw)'],
            
            ['sensor.lidar.ray_cast', None, 'Lidar (Ray-Cast)']]
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for item in self.sensors:
            bp = bp_library.find(item[0])
            if item[0].startswith('sensor.camera'):
                bp.set_attribute('image_size_x', str(hud.dim[0]))
                bp.set_attribute('image_size_y', str(hud.dim[1]))
            elif item[0].startswith('sensor.lidar'):
                bp.set_attribute('range', '5000')
            item.append(bp)
        self.index = None

    def toggle_camera(self):
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.sensor.set_transform(self._camera_transforms[self.transform_index])

    def set_sensor(self, index, notify=True):
        index = index % len(self.sensors)
        needs_respawn = True if self.index is None \
            else self.sensors[index][0] != self.sensors[self.index][0]
        if needs_respawn:
            if self.sensor is not None:
                self.sensor.destroy()
                self.surface = None
            self.sensor = self._parent.get_world().spawn_actor(
                self.sensors[index][-1],
                self._camera_transforms[self.transform_index],
                attach_to=self._parent)
            # We need to pass the lambda a weak reference to self to avoid
            # circular reference.
            weak_self = weakref.ref(self)
            self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))
        if notify:
            self.hud.notification(self.sensors[index][2])
        self.index = index

    def next_sensor(self):
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording
        self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return
        if self.sensors[self.index][0].startswith('sensor.lidar'):
            points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
            points = np.reshape(points, (int(points.shape[0] / 3), 3))
            lidar_data = np.array(points[:, :2])
            lidar_data *= min(self.hud.dim) / 100.0
            lidar_data += (0.5 * self.hud.dim[0], 0.5 * self.hud.dim[1])
            lidar_data = np.fabs(lidar_data)  # pylint: disable=E1111
            lidar_data = lidar_data.astype(np.int32)
            lidar_data = np.reshape(lidar_data, (-1, 2))
            lidar_img_size = (self.hud.dim[0], self.hud.dim[1], 3)
            lidar_img = np.zeros(lidar_img_size)
            lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
            self.surface = pygame.surfarray.make_surface(lidar_img)
        else:
            image.convert(self.sensors[self.index][1])
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self.recording:
            global diff
            image.save_to_disk('_out/%08d' % image.frame_number)
            frame='%08d' % image.frame_number
            diff = seg.lane_diff(frame)
            print(diff)
            ##call segmentation function look for image w/ image.frame_number + prev


# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================


def game_loop(args,socket):
    pygame.init()
    pygame.font.init()
    world = None

    global from_server

    try:
        #print(carla)
        client = carla.Client(args.host, args.port)
        client.set_timeout(4.0)

        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        hud = HUD(args.width, args.height,socket)
        world = World(client.get_world(), hud, args.filter, args.rolename)
 

        controller = KeyboardControl(world,args.autopilot,socket)

        clock = pygame.time.Clock()
        while True:
            clock.tick_busy_loop(60)
            if controller.parse_events(client, world, clock):
                return
            # as soon as the server is ready continue!
            if not world.world.wait_for_tick(10.0):
                continue

            world.tick(clock,socket)
            world.render(display)
            pygame.display.flip()
            # if (from_server=='Slow Down'):
               
            #     while (from_server=='Slow Down'):
            #         if controller.parse_events(client, world, clock):
            #             return

            #         # as soon as the server is ready continue!
            #         if not world.world.wait_for_tick(10.0):
            #             continue

            #         world.tick(clock,socket)
            #         world.render(display)
            #         pygame.display.flip()
                    
            # controller = KeyboardControl(world,False,socket)

    finally:

        if (world and world.recording_enabled):
            client.stop_recorder()

        if world is not None:
            world.destroy()

        pygame.quit()


# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def main(socket):
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '--rolename',
        metavar='NAME',
        default='hero',
        help='actor role name (default: "hero")')

    #added arg for automatic control
    argparser.add_argument("--agent", type=str,
                           choices=["Roaming", "Basic"],
                           help="select which agent to run",
                           default="Basic")

    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    try:

        game_loop(args,socket)


    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')

def server_response(socket):
    global from_server

    while True:
        try:
            response = socket.recv(4096)
            from_server = response.decode()
            #print("in server response: "+from_server)
        except:
            continue

if __name__ == '__main__':
    try:
        client = socket.socket()
        
        t = threading.Thread(target=server_response,args=(client,))
        t.start()

        #Martin's laptop
        ip_addr = input("Enter an IP address: ")
        client.connect((ip_addr,12345))
        #client.connect((ip_addr,8080))
        #client.connect(('100.67.117.35',8080))
        #client.connect(('',12345))
        #client.connect(('100.67.127.255',12345))
        main(client)
        t.join()
    except KeyboardInterrupt:
        sys.exit(0)

    finally:
        sys.exit(1)